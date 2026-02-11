
import json
import random
from datetime import datetime

# Load existing data
with open('statement_data.json', 'r') as f:
    data = json.load(f)

checking_account = data['accounts'][0]
start_balance = checking_account['previous_balance']

# List of descriptions and amount ranges
merchants = [
    ("TARGET STORE", -50, -150),
    ("WAL-MART SUPERCENTER", -30, -200),
    ("SHELL OIL", -30, -60),
    ("CHEVRON", -40, -70),
    ("MCDONALDS", -10, -25),
    ("STARBUCKS", -5, -15),
    ("UBER TRIP", -15, -45),
    ("AMZN Mktp US", -20, -100),
    ("NETFLIX", -15.99, -15.99),
    ("SPOTIFY", -10.99, -10.99),
    ("CHICK-FIL-A", -12, -30),
    ("KROGER FUEL", -40, -80),
    ("PUBLIX SUPER MARKETS", -50, -150),
    ("CVS PHARMACY", -10, -50),
    ("DOORDASH", -20, -60),
    ("HOME DEPOT", -50, -200),
    ("LOWES", -50, -200),
    ("T-MOBILE BILL", -80, -120),
    ("COMCAST CABLE", -60, -100),
    ("APPLE SERVICE", -0.99, -9.99)
]

# Generate 30 new transactions
new_transactions = []
for i in range(30):
    merchant, min_amt, max_amt = random.choice(merchants)
    if min_amt == max_amt:
        amount = min_amt
    else:
        amount = round(random.uniform(min_amt, max_amt), 2)
    
    # Random day in Jan 2026 (avoiding 1st and 31st to keep existing ones intact mostly)
    day = random.randint(2, 30)
    date_str = f"01/{day:02d}"
    
    new_transactions.append({
        "date": date_str,
        "description": merchant,
        "amount": amount,
        "balance": 0.0 # Placeholder
    })

# Combine with existing transactions
all_transactions = checking_account['transactions'] + new_transactions

# Sort by date
def parse_date(tx):
    # format is MM/DD, assume year 2026
    return datetime.strptime(f"2026/{tx['date']}", "%Y/%m/%d")

all_transactions.sort(key=parse_date)

# Recalculate balances and totals
current_balance = start_balance
total_deposits = 0.0
total_withdrawals = 0.0

for tx in all_transactions:
    amount = tx['amount']
    current_balance += amount
    current_balance = round(current_balance, 2)
    tx['balance'] = current_balance
    
    if amount > 0:
        total_deposits += amount
    else:
        total_withdrawals += abs(amount)

# Update account data
checking_account['transactions'] = all_transactions
checking_account['deposits_credits'] = round(total_deposits, 2)
checking_account['withdrawals_debits'] = round(total_withdrawals, 2)
checking_account['ending_balance'] = round(current_balance, 2)

# Save back
with open('statement_data.json', 'w') as f:
    json.dump(data, f, indent=4)

print(f"Added 30 transactions. New ending balance: {checking_account['ending_balance']}")
