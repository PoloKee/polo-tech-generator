import datetime
import random
from generate_statement import create_statement_pdf
from transaction_generator import generate_transactions, MERCHANT_CATEGORIES, get_regional_merchants

def generate_kingdom_docs():
    # --- Profile Data ---
    account_holder = {
        "name": "ARJAY MATHEWS",
        "address_line1": "909 EAGLE LANDING PKWY #1044",
        "address_line2": "STOCKBRIDGE GA 30281", # Corrected format
        "access_number": "1140922", # Random realistic number
        "company_name": "KINGDOM MANDATE CENTER" # Context for us, used in header if supported or just address
    }

    # Since the template uses Name/Addr1/Addr2, we might want to put Company in Addr1 if it fits,
    # or just stick to the requested format.
    # User said: "Kingdom Mandate Center, address 909 Eagle landing pkwy #1044 Stockbridge GA 30281"
    # Usually business statements have:
    # KINGDOM MANDATE CENTER
    # ARJAY MATHEWS
    # ADDRESS...
    # Or just Company Name if it's a business account.
    # I will put "KINGDOM MANDATE CENTER" as the name, and "ATTN: ARJAY MATHEWS" in address line 1 if needed,
    # or just:
    # Name: KINGDOM MANDATE CENTER
    # Addr1: 909 EAGLE LANDING PKWY #1044
    # Addr2: STOCKBRIDGE GA 30281
    
    account_holder_data = {
        "name": "KINGDOM MANDATE CENTER",
        "address_line1": "909 EAGLE LANDING PKWY #1044",
        "address_line2": "STOCKBRIDGE GA 30281",
        "access_number": "8839102"
    }

    user_profile = {
        "income": "high",
        "position": "business_owner",
        "home_city": "STOCKBRIDGE",
        "home_state": "GA"
    }

    # --- Generate Transactions ---
    
    # 1. Main Month (Jan 4 - Jan 31)
    # Generate ~25 transactions for the rest of the month
    main_txs = generate_transactions("01/04/2026", "01/31/2026", user_profile, count=25)
    
    # 2. Specific First 3 Days (Jan 1 - Jan 3)
    # Requirement: "from the 1 - 3rd there will be 4 random transactions per day"
    # "payment of rent on the amount of 750"
    
    start_txs = []
    
    # Jan 01
    date_01 = datetime.datetime(2026, 1, 1)
    # Rent
    start_txs.append({
        "date_obj": date_01,
        "description": "RENT PAYMENT EAGLE LANDING",
        "amount": -750.00,
        "category": "RENT"
    })
    # 3 Randoms to make 4 total
    for _ in range(3):
        start_txs.append(create_random_tx(date_01, user_profile))
        
    # Jan 02
    date_02 = datetime.datetime(2026, 1, 2)
    for _ in range(4):
        start_txs.append(create_random_tx(date_02, user_profile))
        
    # Jan 03
    date_03 = datetime.datetime(2026, 1, 3)
    for _ in range(4):
        start_txs.append(create_random_tx(date_03, user_profile))

    # Combine and Sort
    all_raw_txs = start_txs + convert_formatted_to_raw(main_txs, 2026)
    all_raw_txs.sort(key=lambda x: x["date_obj"])
    
    # --- Balance Calculation ---
    start_balance = 8500.00
    current_balance = start_balance
    
    final_transactions = []
    
    for tx in all_raw_txs:
        current_balance += tx["amount"]
        final_transactions.append({
            "date": tx["date_obj"].strftime("%m/%d"),
            "description": tx["description"],
            "amount": tx["amount"],
            "balance": current_balance
        })

    # --- Statement Data Structure ---
    stmt_data = {
        "account_holder": account_holder_data,
        "period": "01/01/26 - 01/31/26",
        "accounts": [
            {
                "type": "Business Checking",
                "account_number": "5502948821",
                "previous_balance": start_balance,
                "deposits_credits": 0.00, # We didn't generate deposits, maybe add one?
                "withdrawals_debits": abs(sum(t['amount'] for t in final_transactions if t['amount'] < 0)),
                "ending_balance": current_balance,
                "ytd_dividends": 0.00,
                "transactions": final_transactions
            }
        ],
        "savings_account": {
            "type": "Business Savings",
            "account_number": "88102399",
            "previous_balance": 1200.00,
            "ending_balance": 1200.10,
            "dividends": 0.10,
            "ytd_dividends": 0.10,
            "transactions": [
                {"date": "01/31", "description": "DIVIDEND EARNED", "amount": 0.10, "balance": 1200.10}
            ]
        }
    }
    
    # Generate PDF
    output_file = "Kingdom_Mandate_Center_Statement_Jan2026.pdf"
    print(f"Generating {output_file}...")
    create_statement_pdf(output_file, stmt_data)
    print("Done.")

def create_random_tx(date_obj, profile):
    """Helper to create a single random transaction dictionary"""
    # Categories for business context
    categories = ["BUSINESS_EXPENSE", "OFFICE_LUNCH", "GAS", "SERVICES", "UTILITY"]
    weights = [40, 20, 15, 15, 10]
    
    cat = random.choices(categories, weights=weights, k=1)[0]
    
    desc = ""
    amt = 0.0
    
    if cat == "BUSINESS_EXPENSE":
        desc = random.choice(MERCHANT_CATEGORIES["BUSINESS_EXPENSE"])
        amt = random.uniform(25, 200)
    elif cat == "OFFICE_LUNCH":
        desc = random.choice(MERCHANT_CATEGORIES["OFFICE_LUNCH"])
        amt = random.uniform(10, 40)
    elif cat == "GAS":
        desc = random.choice(get_regional_merchants("GA", "GAS"))
        amt = random.uniform(30, 60)
    elif cat == "SERVICES":
        desc = random.choice(MERCHANT_CATEGORIES["SERVICES"])
        amt = random.uniform(20, 100)
    elif cat == "UTILITY":
        desc = random.choice(get_regional_merchants("GA", "UTILITY"))
        amt = random.uniform(50, 150)
        
    return {
        "date_obj": date_obj,
        "description": desc,
        "amount": -round(amt, 2),
        "category": cat
    }

def convert_formatted_to_raw(formatted_txs, year):
    """Converts the formatted output of generate_transactions back to raw objects for sorting/combining"""
    raw = []
    for tx in formatted_txs:
        # tx['date'] is "MM/DD"
        d_str = f"{tx['date']}/{year}"
        date_obj = datetime.datetime.strptime(d_str, "%m/%d/%Y")
        raw.append({
            "date_obj": date_obj,
            "description": tx["description"],
            "amount": tx["amount"],
            "category": "GENERAL"
        })
    return raw

if __name__ == "__main__":
    generate_kingdom_docs()
