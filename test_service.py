from payroll_service import PayrollService
try:
    service = PayrollService()
    print("Service initialized.")
    # Dry run generation (mocking execution to ensure imports work)
    # files = service.generate_payroll() 
    # print(f"Generated: {files}")
    print("Imports and Init successful.")
except Exception as e:
    print(f"Error: {e}")
