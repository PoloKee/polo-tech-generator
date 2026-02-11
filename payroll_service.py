import os
from datetime import date, datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER

from payroll_agents import PayrollOrchestrator, CompanyProfile, EmployeeProfile
from generate_adp_paystub import draw_adp_style_stub
from registry_manager import RegistryManager, EmployeeRecord, CompanyRecord

class PayrollService:
    def __init__(self, output_dir="TiffanyPageStubs"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.registry = RegistryManager()

    def generate_payroll(self, frequency="biweekly", security_pattern="SECURE"):
        """
        Generates payroll based on the stored Tifiney Goins profile and NTS Designs profile.
        Returns a list of generated file paths.
        """
        
        # 1. Get or Create Company
        company_rec = self.registry.get_company("NTS Designs, Inc")
        if not company_rec:
            company_rec = self.registry.register_company(
                name="NTS Designs, Inc",
                addr1="3455 Peachtree Road, Northeast",
                addr2="Atlanta, GA 30318",
                bank_name="Wells Fargo",
                bank_addr1="333 Market Street",
                bank_addr2="San Francisco, CA 94105",
                sig_name="Kent Jones",
                routing="121000248"
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

        # 2. Get or Create Employee (Tifiney Goins)
        emp_id = "71297" 
        emp_rec = self.registry.get_employee(emp_id)
        
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
            self.registry.upsert_employee(emp_rec)
        
        employee_profile = EmployeeProfile(
            name=emp_rec.name,
            address_line1=emp_rec.address_line1,
            address_line2=emp_rec.address_line2,
            ssn_last4=emp_rec.ssn_last4,
            employee_id=emp_rec.employee_id, # Accessing property which returns the ID
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

        # 3. Initialize Orchestrator
        orchestrator = PayrollOrchestrator(
            company_profile, 
            employee_profile, 
            start_check_num=1000,
            frequency=frequency
        )

        # 4. Define Pay Schedule
        # Dynamic dates could be passed in, but using the requested logic for now
        pay_period_ends = [
            date(2026, 1, 14),
            date(2026, 1, 28)
        ]
        
        if frequency == 'weekly':
            pay_period_ends = [
                date(2026, 1, 7),
                date(2026, 1, 14),
                date(2026, 1, 21),
                date(2026, 1, 28)
            ]

        # 5. Run Agents
        hours = 80.0 if frequency == 'biweekly' else 40.0
        pay_stubs_data = orchestrator.run_payroll(pay_period_ends, hours=hours)

        # 6. Render PDFs
        generated_files = []
        
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

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, stub in enumerate(pay_stubs_data):
            # Filename
            fname = f"Tifiney_Goins_{frequency}_{i+1}_{timestamp}.pdf"
            full_path = os.path.join(self.output_dir, fname)
            
            c = canvas.Canvas(full_path, pagesize=LETTER)
            draw_adp_style_stub(c, base_data, stub, security_pattern=security_pattern)
            c.save()
            
            generated_files.append(fname)

        # 7. Update Registry
        emp_rec.ytd_gross = employee_profile.ytd_gross
        emp_rec.ytd_federal_tax = employee_profile.ytd_federal_tax
        emp_rec.ytd_ss_tax = employee_profile.ytd_ss_tax
        emp_rec.ytd_medicare_tax = employee_profile.ytd_medicare_tax
        emp_rec.ytd_state_tax = employee_profile.ytd_state_tax
        emp_rec.ytd_benefits = employee_profile.ytd_benefits
        
        self.registry.upsert_employee(emp_rec)
        
        return generated_files
