import sys
import os
from datetime import date

# Add parent directory to path to find statement_generator
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from statement_generator.truck_pay import Employee, PayrollInfo, EarningsItem, Deduction, Tax, PayStatement
    from statement_generator.truck_renderer import TruckPayRenderer
except ImportError:
    # Fallback if running from NvyJune root context or different structure
    sys.path.append(os.path.join(parent_dir, 'statement_generator'))
    from truck_pay import Employee, PayrollInfo, EarningsItem, Deduction, Tax, PayStatement
    from truck_renderer import TruckPayRenderer

def generate_tiffany_statement():
    # 1. Employee Data
    emp = Employee(
        name="Tiffany Smith", # Placeholder
        personnel_no="00012345",
        ssn="XXX-XX-XXXX",
        position="Driver",
        cost_center="Operations"
    )

    # 2. Payroll Info
    payroll = PayrollInfo(
        payroll_type="US:Weekly - UW",
        pay_period_start=date(2021, 6, 1),
        pay_period_end=date(2021, 6, 7),
        payroll_number="202123",
        pay_date=date(2021, 6, 8),
        tractor_origin="Unknown",
        check_number="0001234500001001",
        bank_name="Bank of America",
        account_number="123456789"
    )

    # 3. Create Statement
    stmt = PayStatement(emp, payroll)

    # 4. Add Earnings (Copied from truck example)
    stmt.add_earning(EarningsItem("Loaded Mileage", 454, 1.12))
    stmt.add_earning(EarningsItem("Empty Mileage", 54, 0.39))
    stmt.add_earning(EarningsItem("Per Diem Miles", 54, 1.80))
    stmt.add_earning(EarningsItem("Team Miles", 80, 0.75))
    stmt.add_earning(EarningsItem("Experience Adjustment", 57, 1.00))
    stmt.add_earning(EarningsItem("Guarantee Pay", 699, 0.3666)) 

    # 5. Add Deductions
    stmt.add_deduction(Deduction("Dental EE pre-tax", 12.00, True))
    stmt.add_deduction(Deduction("Basic Life EE pre-tax", 15.00, True))
    stmt.add_deduction(Deduction("Health Care EE pre-tax", 20.00, True))

    # 6. Add Taxes
    stmt.add_tax(Tax("Federal Withholding Tax", 71.35))
    stmt.add_tax(Tax("TX Withholding Tax", 53.80))
    stmt.add_tax(Tax("TX EE Medicare Tax", 12.58))

    # 7. Render
    output_path = os.path.abspath("generated_tiffany_statement.pdf")
    
    print(f"Rendering Tiffany's Truck Statement to {output_path}...")
    renderer = TruckPayRenderer(output_path)
    renderer.render(stmt)
    print("Done!")
    
    try:
        os.startfile(output_path)
    except Exception as e:
        print(f"Could not open file: {e}")

if __name__ == "__main__":
    generate_tiffany_statement()
