import json
import os
from datetime import date, datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER

# Import the new Agent system and the existing renderer function
from payroll_agents import PayrollOrchestrator, CompanyProfile, EmployeeProfile
from generate_adp_paystub import draw_adp_style_stub
from registry_manager import RegistryManager, EmployeeRecord, CompanyRecord

def get_user_input():
    print("--- Payroll System Configuration ---")
    freq = input("Enter Pay Frequency (weekly/biweekly) [default: biweekly]: ").strip().lower()
    if freq not in ['weekly', 'biweekly']:
        freq = 'biweekly'
        
    print("\nSelect Security Background Pattern:")
    print("1. SECURE DOCUMENT (Default)")
    print("2. VOID (Watermark)")
    print("3. Wavy Lines (Guilloche)")
    print("4. ORIGINAL DOCUMENT")
    choice = input("Enter choice (1-4): ").strip()
    
    mapping = {"1": "SECURE", "2": "VOID", "3": "LINES", "4": "ORIGINAL"}
    pattern = mapping.get(choice, "SECURE")
    
    return freq, pattern

def generate_smart_paystubs():
    # 0. Get User Input
    frequency, security_pattern = get_user_input()

    # 1. Load Registry
    registry = RegistryManager()
    
    # 2. Get or Create Company
    company_rec = registry.get_company("NTS Designs, Inc")
    if not company_rec:
        # Create default if not exists
        company_rec = registry.register_company(
            name="NTS Designs, Inc",
            addr1="3455 Peachtree Road, Northeast",
            addr2="Atlanta, GA 30318",
            bank_name="Wells Fargo",
            bank_addr1="333 Market Street",
            bank_addr2="San Francisco, CA 94105",
            sig_name="Kent Jones",
            routing="121000248" # Wells Fargo
            # Account will be auto-generated random
        )
    
    company_profile = CompanyProfile(
        name=company_rec.name,
        address_line1=company_rec.address_line1,
        address_line2=company_rec.address_line2,
        bank_name=company_rec.bank_name,
        bank_address_line1=company_rec.bank_address_line1,
        bank_address_line2=company_rec.bank_address_line2,
        signature_name=company_rec.signature_name,
        routing_number=company_rec.routing_number,
        account_number=company_rec.account_number
    )

    # 3. Get or Create Employee
    # We use a fixed ID for Tifiney as requested ("employee ID number will remain the same")
    emp_id = "71297" 
    emp_rec = registry.get_employee(emp_id)
    
    if not emp_rec:
        emp_rec = EmployeeRecord(
            id=emp_id,
            name="Tifiney Goins",
            address_line1="2872 North Fair Loop",
            address_line2="Stonecrest, GA 30038",
            ssn_last4="4315",
            department="Design",
            filing_status="Single",
            exemptions=1,
            hourly_rate=31.25,
            ytd_gross=0.0
        )
        registry.upsert_employee(emp_rec)
    
    employee_profile = EmployeeProfile(
        name=emp_rec.name,
        address_line1=emp_rec.address_line1,
        address_line2=emp_rec.address_line2,
        ssn_last4=emp_rec.ssn_last4,
        employee_id=emp_rec.id,
        department=emp_rec.department,
        filing_status=emp_rec.filing_status,
        exemptions=emp_rec.exemptions,
        hourly_rate=emp_rec.hourly_rate,
        ytd_gross=emp_rec.ytd_gross,
        ytd_federal_tax=emp_rec.ytd_federal_tax,
        ytd_ss_tax=emp_rec.ytd_ss_tax,
        ytd_medicare_tax=emp_rec.ytd_medicare_tax,
        ytd_state_tax=emp_rec.ytd_state_tax,
        ytd_benefits=emp_rec.ytd_benefits
    )

    # 4. Initialize the AI Orchestrator
    # "Check numbers... start at least 121 plus... if in the 10 number"
    # Let's start the sequence at a base like 1000
    orchestrator = PayrollOrchestrator(
        company_profile, 
        employee_profile, 
        start_check_num=1000,
        frequency=frequency
    )

    # 5. Define the Pay Schedule (Dates when the pay period ENDS)
    # User wanted bi-weekly dates.
    # From previous data: Period End 01/14/2026 and 01/28/2026
    # For demonstration, we'll keep these. In a real interactive mode, we could ask for dates.
    pay_period_ends = [
        date(2026, 1, 14),
        date(2026, 1, 28)
    ]
    
    if frequency == 'weekly':
        # Adjust for weekly example
        pay_period_ends = [
            date(2026, 1, 7),
            date(2026, 1, 14),
            date(2026, 1, 21),
            date(2026, 1, 28)
        ]

    # 6. Run the Agents to generate data
    print(f"AI Agents calculating {frequency} payroll...")
    # Adjust hours based on frequency
    hours = 80.0 if frequency == 'biweekly' else 40.0
    pay_stubs_data = orchestrator.run_payroll(pay_period_ends, hours=hours)

    # 7. Render PDFs
    output_dir = "TiffanyPageStubs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Convert the dataclasses back to the dictionary format expected by the renderer
    
    # Base "data" dict that renderer uses for company/employee info
    base_data = {
        "employee": {
            "name": employee_profile.name,
            "address_line1": employee_profile.address_line1,
            "address_line2": employee_profile.address_line2,
            "ssn_last4": employee_profile.ssn_last4,
            "employee_id": employee_profile.employee_id,
            "department": employee_profile.department,
            "filing_status": employee_profile.filing_status,
            "exemptions": employee_profile.exemptions
        },
        "company": {
            "name": company_profile.name,
            "address_line1": company_profile.address_line1,
            "address_line2": company_profile.address_line2,
            "bank_name": company_profile.bank_name,
            "bank_address_line1": company_profile.bank_address_line1,
            "bank_address_line2": company_profile.bank_address_line2,
            "signature_name": company_profile.signature_name
        }
    }

    for i, stub in enumerate(pay_stubs_data):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"Tifiney_Goins_SmartStub_{i+1}_{timestamp}.pdf")
        c = canvas.Canvas(filename, pagesize=LETTER)
        
        # Draw using existing renderer logic
        draw_adp_style_stub(c, base_data, stub, security_pattern=security_pattern)
        
        c.save()
        print(f"Generated {filename} (Check #{stub['check_number']})")

    # 8. Save updated Employee YTD back to Registry
    # Update record from profile
    emp_rec.ytd_gross = employee_profile.ytd_gross
    emp_rec.ytd_federal_tax = employee_profile.ytd_federal_tax
    emp_rec.ytd_ss_tax = employee_profile.ytd_ss_tax
    emp_rec.ytd_medicare_tax = employee_profile.ytd_medicare_tax
    emp_rec.ytd_state_tax = employee_profile.ytd_state_tax
    emp_rec.ytd_benefits = employee_profile.ytd_benefits
    
    registry.upsert_employee(emp_rec)
    print("Employee YTD updated in Registry.")

if __name__ == "__main__":
    generate_smart_paystubs()
