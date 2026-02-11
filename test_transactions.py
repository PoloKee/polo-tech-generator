from transaction_generator import generate_transactions
import json

profile = {
    "income": "med",
    "gender": "female",
    "position": "office",
    "home_city": "Atlanta",
    "home_state": "GA"
}

transactions = generate_transactions("01/01/2024", "01/31/2024", profile, count=10)

print(json.dumps(transactions, indent=4))
