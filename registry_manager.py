import json
import os
import random
from dataclasses import dataclass, asdict
from typing import Optional, Dict

DATA_DIR = "registry_data"
EMPLOYEE_DB_FILE = os.path.join(DATA_DIR, "employee_registry.json")
COMPANY_DB_FILE = os.path.join(DATA_DIR, "company_registry.json")

# Ensure directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

@dataclass
class EmployeeRecord:
    id: str
    name: str
    address_line1: str
    address_line2: str
    ssn_last4: str
    department: str
    filing_status: str
    exemptions: int
    hourly_rate: float
    ytd_gross: float = 0.0
    ytd_federal_tax: float = 0.0
    ytd_ss_tax: float = 0.0
    ytd_medicare_tax: float = 0.0
    ytd_state_tax: float = 0.0
    ytd_benefits: float = 0.0

@dataclass
class CompanyRecord:
    name: str
    address_line1: str
    address_line2: str
    bank_name: str
    bank_address_line1: str
    bank_address_line2: str
    signature_name: str
    routing_number: str
    account_number: str

class RegistryManager:
    def __init__(self):
        self._load_databases()

    def _load_databases(self):
        if os.path.exists(EMPLOYEE_DB_FILE):
            with open(EMPLOYEE_DB_FILE, 'r') as f:
                self.employees = json.load(f)
        else:
            self.employees = {}

        if os.path.exists(COMPANY_DB_FILE):
            with open(COMPANY_DB_FILE, 'r') as f:
                self.companies = json.load(f)
        else:
            self.companies = {}

    def _save_employees(self):
        with open(EMPLOYEE_DB_FILE, 'w') as f:
            json.dump(self.employees, f, indent=4)

    def _save_companies(self):
        with open(COMPANY_DB_FILE, 'w') as f:
            json.dump(self.companies, f, indent=4)

    # --- Employee Methods ---

    def get_employee(self, employee_id: str) -> Optional[EmployeeRecord]:
        data = self.employees.get(employee_id)
        if data:
            return EmployeeRecord(**data)
        return None

    def upsert_employee(self, record: EmployeeRecord):
        """Creates or updates an employee record."""
        self.employees[record.id] = asdict(record)
        self._save_employees()

    # --- Company Methods ---

    def get_company(self, company_name: str) -> Optional[CompanyRecord]:
        data = self.companies.get(company_name)
        if data:
            return CompanyRecord(**data)
        return None

    def register_company(self, name, addr1, addr2, bank_name, bank_addr1, bank_addr2, sig_name, routing=None, account=None):
        """
        Registers a company. Generates random account number if not provided.
        """
        if not routing:
            # Default to Wells Fargo San Francisco if not specified
            routing = "121000248" 
        
        if not account:
            # Generate random 10-digit account number
            # "random numbers ... not in relation"
            account = str(random.randint(1000000000, 9999999999))

        record = CompanyRecord(
            name=name,
            address_line1=addr1,
            address_line2=addr2,
            bank_name=bank_name,
            bank_address_line1=bank_addr1,
            bank_address_line2=bank_addr2,
            signature_name=sig_name,
            routing_number=routing,
            account_number=account
        )
        
        self.companies[name] = asdict(record)
        self._save_companies()
        return record

