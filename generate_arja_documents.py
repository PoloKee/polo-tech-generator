import json
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Import the generation functions
# We assume these files are in the same directory
from generate_adp_paystub import draw_adp_style_stub
from generate_statement import create_statement_pdf
from transaction_generator import generate_transactions

def generate_arja_docs():
    # --- Shared Data ---
    employee = {
        "name": "ARJA MATHEWES",
        "address_line1": "115 APPLE LANE",
        "address_line2": "ATLANTA, GA 393884",
        "ssn_last4": "5582",
        "filing_status": "Single",
        "exemptions": 1,
        "employee_id": "004421"
    }
    
    company = {
        "name": "NTS DESIGNS, INC.",
        "address_line1": "123 INNOVATION DR",
        "address_line2": "SUITE 200, TECH CITY, GA 30318",
        "bank_name": "Wells Fargo Bank, N.A.",
        "bank_address_line1": "420 Montgomery Street",
        "bank_address_line2": "San Francisco, CA 94104",
        "signature_name": "Kent Jones"
    }

    # Gross Pay Calculation: $2300/mo * 12 / 26 = $1061.54
    gross_pay = 1061.54
    hourly_rate = gross_pay / 80.0 # ~13.27
    
    # Simple tax assumption (approx 20%)
    taxes_map = {
        "Federal Income Tax": 84.92,
        "Social Security Tax": 65.82,
        "Medicare Tax": 15.39,
        "GA State Income Tax": 31.85
    }
    total_taxes = sum(taxes_map.values())
    net_pay = gross_pay - total_taxes # 1061.54 - 197.98 = 863.56
    
    # --- 1. Paystubs Data ---
    # Stub 1: Dec 2025
    stub1 = {
        "pay_period_start": "12/01/2025",
        "pay_period_end": "12/14/2025",
        "pay_date": "12/19/2025",
        "check_number": "1042",
        "net_pay": net_pay,
        "earnings": [
            {
                "description": "Regular Pay",
                "rate": hourly_rate,
                "hours": 80.00,
                "amount": gross_pay,
                "ytd_amount": gross_pay * 24
            }
        ],
        "totals": {
            "gross": gross_pay,
            "ytd_gross": gross_pay * 24
        },
        "taxes": [
            {"description": k, "amount": v, "ytd_amount": v * 24} for k, v in taxes_map.items()
        ],
        "deductions": [],
        "company_routing": "121000248",
        "company_account": "882930441",
        "distribution_account": "XXXXXX4921"
    }

    # Stub 2: Jan 2026 (New Year - YTD resets)
    stub2 = {
        "pay_period_start": "12/15/2025",
        "pay_period_end": "12/28/2025",
        "pay_date": "01/02/2026",
        "check_number": "1043",
        "net_pay": net_pay,
        "earnings": [
            {
                "description": "Regular Pay",
                "rate": hourly_rate,
                "hours": 80.00,
                "amount": gross_pay,
                "ytd_amount": gross_pay # Reset YTD
            }
        ],
        "totals": {
            "gross": gross_pay,
            "ytd_gross": gross_pay # Reset YTD
        },
        "taxes": [
            {"description": k, "amount": v, "ytd_amount": v} for k, v in taxes_map.items()
        ],
        "deductions": [],
        "company_routing": "121000248",
        "company_account": "882930441",
        "distribution_account": "XXXXXX4921"
    }

    paystub_full_data = {
        "company": company,
        "employee": employee,
        "pay_stubs": [] # We will call draw individually
    }

    # Generate Paystubs
    print("Generating Paystubs...")
    
    # Stub 1
    c1 = canvas.Canvas("Arja_Mathewes_Paystub_Dec19.pdf", pagesize=letter)
    draw_adp_style_stub(c1, paystub_full_data, stub1)
    c1.save()
    
    # Stub 2
    c2 = canvas.Canvas("Arja_Mathewes_Paystub_Jan02.pdf", pagesize=letter)
    draw_adp_style_stub(c2, paystub_full_data, stub2)
    c2.save()


    # --- 2. Bank Statements Data ---
    
    # Common Statement Data
    account_holder = {
        "name": "ARJA MATHEWES",
        "address_line1": "115 APPLE LANE",
        "address_line2": "ATLANTA, GA 393884",
        "access_number": "994821"
    }

    # Profile for Transaction Generation
    user_profile = {
        "income": "med",
        "gender": "female",
        "position": "office",
        "home_city": "ATLANTA",
        "home_state": "GA"
    }

    # Statement 1: Dec 2025
    # Generate random transactions
    stmt1_txs = generate_transactions("12/01/2025", "12/31/2025", user_profile, count=25)
    
    # Add Fixed Deposits/Bills
    stmt1_txs.append({"date": "12/19", "description": "ACH DEPOSIT NTS DESIGNS", "amount": 863.56, "balance": 0})
    stmt1_txs.append({"date": "12/15", "description": "NETFLIX.COM", "amount": -15.99, "balance": 0})
    
    # Sort again just in case
    stmt1_txs.sort(key=lambda x: x['date'])
    
    # Calculate balances for Stmt 1
    bal = 2450.00 # Start Bal
    stmt1_start = bal
    for tx in stmt1_txs:
        bal += tx['amount']
        tx['balance'] = bal
    stmt1_end = bal

    stmt1_data = {
        "account_holder": account_holder,
        "period": "12/01/25 - 12/31/25",
        "accounts": [
            {
                "type": "Business Checking",
                "account_number": "3025884921",
                "previous_balance": stmt1_start,
                "deposits_credits": 863.56,
                "withdrawals_debits": abs(sum(t['amount'] for t in stmt1_txs if t['amount'] < 0)),
                "ending_balance": stmt1_end,
                "ytd_dividends": 0.00,
                "transactions": stmt1_txs
            }
        ],
        "savings_account": {
            "type": "Business Savings",
            "account_number": "88210044",
            "previous_balance": 500.00,
            "ending_balance": 500.05,
            "dividends": 0.05,
            "ytd_dividends": 1.20,
            "transactions": [
                {"date": "12/31", "description": "DIVIDEND EARNED", "amount": 0.05, "balance": 500.05}
            ]
        }
    }

    # Statement 2: Jan 2026
    # Generate random transactions
    stmt2_txs = generate_transactions("01/01/2026", "01/31/2026", user_profile, count=25)
    
    # Add Fixed Deposits/Bills
    stmt2_txs.append({"date": "01/02", "description": "ACH DEPOSIT NTS DESIGNS", "amount": 863.56, "balance": 0})
    stmt2_txs.append({"date": "01/15", "description": "NETFLIX.COM", "amount": -15.99, "balance": 0})

    # Sort again
    stmt2_txs.sort(key=lambda x: x['date'])
    
    # Calculate balances for Stmt 2 (Start = Stmt 1 End)
    bal = stmt1_end
    stmt2_start = bal
    for tx in stmt2_txs:
        bal += tx['amount']
        tx['balance'] = bal
    stmt2_end = bal

    stmt2_data = {
        "account_holder": account_holder,
        "period": "01/01/26 - 01/31/26",
        "accounts": [
            {
                "type": "Business Checking",
                "account_number": "3025884921",
                "previous_balance": stmt2_start,
                "deposits_credits": 863.56,
                "withdrawals_debits": abs(sum(t['amount'] for t in stmt2_txs if t['amount'] < 0)),
                "ending_balance": stmt2_end,
                "ytd_dividends": 0.00,
                "transactions": stmt2_txs
            }
        ],
        "savings_account": {
            "type": "Business Savings",
            "account_number": "88210044",
            "previous_balance": 500.05,
            "ending_balance": 500.10,
            "dividends": 0.05,
            "ytd_dividends": 0.05, # Reset for new year
            "transactions": [
                {"date": "01/31", "description": "DIVIDEND EARNED", "amount": 0.05, "balance": 500.10}
            ]
        }
    }

    print("Generating Bank Statements...")
    create_statement_pdf("Arja_Mathewes_Statement_Dec2025.pdf", stmt1_data)
    create_statement_pdf("Arja_Mathewes_Statement_Jan2026.pdf", stmt2_data)

if __name__ == "__main__":
    generate_arja_docs()
