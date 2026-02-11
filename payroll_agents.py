import datetime
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# --- Data Models ---

@dataclass
class EmployeeProfile:
    name: str
    address_line1: str
    address_line2: str
    ssn_last4: str
    employee_id: str
    department: str
    filing_status: str
    exemptions: int
    hourly_rate: float
    # YTD Initialization (optional, if starting mid-year)
    ytd_gross: float = 0.0
    ytd_federal_tax: float = 0.0
    ytd_ss_tax: float = 0.0
    ytd_medicare_tax: float = 0.0
    ytd_state_tax: float = 0.0
    ytd_benefits: float = 0.0

@dataclass
class CompanyProfile:
    name: str
    address_line1: str
    address_line2: str
    bank_name: str
    bank_address_line1: str
    bank_address_line2: str
    signature_name: str
    routing_number: str = "121000248"
    account_number: str = "712975555"

@dataclass
class PayStubData:
    period_start: str
    period_end: str
    pay_date: str
    check_number: str
    advice_number: str
    gross_pay: float
    net_pay: float
    earnings: List[Dict]
    taxes: List[Dict]
    deductions: List[Dict]
    totals: Dict
    company_routing: str
    company_account: str
    distribution_account: str

# --- AI Agents ---

class DateLogicAgent:
    """
    Intelligent agent responsible for calculating pay periods and pay dates based on frequency rules.
    """
    def __init__(self, frequency='biweekly'):
        self.frequency = frequency

    def calculate_dates(self, period_end_date: datetime.date):
        """
        Calculates period start and pay date based on the end date.
        Rules:
        - Pay Date = Period End + 5 days
        - Bi-weekly Start = Period End - 13 days
        - Weekly Start = Period End - 6 days
        """
        pay_date = period_end_date + datetime.timedelta(days=5)
        
        if self.frequency.lower() == 'weekly':
            period_start = period_end_date - datetime.timedelta(days=6)
        else:
            # Default to biweekly
            period_start = period_end_date - datetime.timedelta(days=13)
            
        return period_start, period_end_date, pay_date

    def format_date(self, d: datetime.date) -> str:
        return d.strftime("%m/%d/%Y")

class TaxAgent:
    """
    Agent responsible for calculating taxes, tracking YTD limits, and ensuring compliance.
    """
    def __init__(self):
        # 2026/2025 Tax Constants (Approximate for simulation)
        self.SS_RATE = 0.062
        self.MEDICARE_RATE = 0.0145
        self.SS_WAGE_LIMIT = 176100.00  # 2025 limit
        self.GA_STATE_RATE = 0.048 # Approx GA rate
        
        # Federal Tax Bracket (Simplified for estimation)
        # In a real system, this would be a full tax table lookup
        self.FED_RATE_SINGLE = 0.114 # Effective rate approximation based on previous data ($285/$2500)

    def calculate_taxes(self, gross_pay: float, profile: EmployeeProfile):
        """
        Calculates current taxes and updates YTD values in the profile.
        """
        # 1. Social Security
        # Check if approaching limit
        remaining_ss_wage = max(0, self.SS_WAGE_LIMIT - profile.ytd_gross)
        taxable_ss = min(gross_pay, remaining_ss_wage)
        ss_tax = taxable_ss * self.SS_RATE
        
        # 2. Medicare (No limit)
        med_tax = gross_pay * self.MEDICARE_RATE
        
        # 3. Federal Withholding
        # Adjust slightly based on exemptions (Simplified logic)
        # Each exemption reduces taxable income slightly
        effective_fed_rate = max(0, self.FED_RATE_SINGLE - (profile.exemptions * 0.005))
        fed_tax = gross_pay * effective_fed_rate
        
        # 4. State Tax
        state_tax = gross_pay * self.GA_STATE_RATE

        # Update Profile YTD (Simulation happens here, but actual commitment happens after generation)
        # For this function, we return the calculated values
        return {
            "Federal Withholding": fed_tax,
            "Social Security": ss_tax,
            "Medicare": med_tax,
            "GA State Withholding": state_tax
        }

class CheckNumberAgent:
    """
    Agent responsible for generating secure and non-sequential check numbers.
    Logic: Next Check = Previous + 121 + Random Offset
    """
    def __init__(self, start_sequence: int):
        self.last_check_number = start_sequence

    def generate_next(self) -> str:
        # "if it is in the 10 number is at least 121 plus or add 121 plus and you ran a number after that"
        gap = 121 + random.randint(1, 9)
        next_num = self.last_check_number + gap
        self.last_check_number = next_num
        return str(next_num)
    
    def generate_advice_number(self, check_num: str) -> str:
        # Logic to generate a matching advice/voucher number
        return f"9{check_num.zfill(7)}"

class PayrollOrchestrator:
    """
    The Master Agent that coordinates the Date, Tax, and Check Agents to produce payroll data.
    """
    def __init__(self, company: CompanyProfile, employee: EmployeeProfile, 
                 start_check_num: int = 1000, frequency: str = 'biweekly'):
        self.company = company
        self.employee = employee
        
        # Initialize Sub-Agents
        self.date_agent = DateLogicAgent(frequency=frequency)
        self.tax_agent = TaxAgent()
        self.check_agent = CheckNumberAgent(start_sequence=start_check_num)
        
        # Employee's Bank Info (Simulated/Persistent)
        # In a real system, this comes from the employee profile.
        # We will generate a consistent random one if not present, but for now we generate it here
        # so it persists across this batch run.
        self.employee_distribution_account = f"XXXXXX{random.randint(1000,9999)}"

    def run_payroll(self, period_end_dates: List[datetime.date], hours: float):
        """
        Generates a series of pay stubs for the given dates.
        """
        pay_stubs = []
        
        for end_date in period_end_dates:
            # 1. Calculate Dates
            start_date, end_date, pay_date = self.date_agent.calculate_dates(end_date)
            
            # 2. Calculate Earnings
            gross_pay = self.employee.hourly_rate * hours
            
            # 3. Calculate Taxes
            taxes = self.tax_agent.calculate_taxes(gross_pay, self.employee)
            
            # 4. Calculate Deductions (Fixed for now, could be an agent too)
            health_ins = 45.00
            dental_ins = 8.00
            total_deductions = health_ins + dental_ins
            
            # 5. Calculate Totals
            total_taxes = sum(taxes.values())
            net_pay = gross_pay - total_taxes - total_deductions
            
            # 6. Generate Check Numbers
            check_num = self.check_agent.generate_next()
            advice_num = self.check_agent.generate_advice_number(check_num)
            
            # 7. Update YTD (Commit the run)
            # Create snapshot for this stub BEFORE updating cumulative YTD for next loop?
            # Actually, YTD on stub usually INCLUDES current.
            
            current_ytd_gross = self.employee.ytd_gross + gross_pay
            current_ytd_taxes = (self.employee.ytd_federal_tax + taxes["Federal Withholding"] +
                                 self.employee.ytd_ss_tax + taxes["Social Security"] +
                                 self.employee.ytd_medicare_tax + taxes["Medicare"] +
                                 self.employee.ytd_state_tax + taxes["GA State Withholding"])
            current_ytd_deductions = self.employee.ytd_benefits + total_deductions
            
            # Construct Data Object
            stub_data = {
                "pay_period_start": self.date_agent.format_date(start_date),
                "pay_period_end": self.date_agent.format_date(end_date),
                "pay_date": self.date_agent.format_date(pay_date),
                "check_number": check_num,
                "advice_number": advice_num,
                "company_routing": self.company.routing_number,
                "company_account": self.company.account_number,
                "distribution_account": self.employee_distribution_account,
                "earnings": [
                    {
                        "description": "Regular Pay",
                        "rate": self.employee.hourly_rate,
                        "hours": hours,
                        "amount": gross_pay,
                        "ytd_amount": current_ytd_gross
                    }
                ],
                "taxes": [
                    {"description": "Federal Withholding", "amount": taxes["Federal Withholding"], "ytd_amount": self.employee.ytd_federal_tax + taxes["Federal Withholding"]},
                    {"description": "Social Security", "amount": taxes["Social Security"], "ytd_amount": self.employee.ytd_ss_tax + taxes["Social Security"]},
                    {"description": "Medicare", "amount": taxes["Medicare"], "ytd_amount": self.employee.ytd_medicare_tax + taxes["Medicare"]},
                    {"description": "GA State Withholding", "amount": taxes["GA State Withholding"], "ytd_amount": self.employee.ytd_state_tax + taxes["GA State Withholding"]}
                ],
                "deductions": [
                    {"description": "Health Insurance", "amount": health_ins, "ytd_amount": self.employee.ytd_benefits/2 + health_ins}, # Approx split logic
                    {"description": "Dental Insurance", "amount": dental_ins, "ytd_amount": self.employee.ytd_benefits/2 + dental_ins}
                ],
                "net_pay": net_pay,
                "totals": {
                    "gross": gross_pay,
                    "ytd_gross": current_ytd_gross,
                    "taxes": total_taxes,
                    "ytd_taxes": current_ytd_taxes,
                    "deductions": total_deductions,
                    "ytd_deductions": current_ytd_deductions
                }
            }
            
            pay_stubs.append(stub_data)
            
            # Commit updates to employee profile for next iteration
            self.employee.ytd_gross = current_ytd_gross
            self.employee.ytd_federal_tax += taxes["Federal Withholding"]
            self.employee.ytd_ss_tax += taxes["Social Security"]
            self.employee.ytd_medicare_tax += taxes["Medicare"]
            self.employee.ytd_state_tax += taxes["GA State Withholding"]
            self.employee.ytd_benefits += total_deductions
            
        return pay_stubs
