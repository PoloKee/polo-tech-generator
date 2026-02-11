import random
import datetime

# --- Data Repositories ---

NEIGHBORING_CITIES = {
    "ATLANTA": ["MARIETTA", "DECATUR", "SANDY SPRINGS", "SMYRNA", "EAST POINT", "COLLEGE PARK", "VININGS", "BUCKHEAD", "DUNWOODY", "ROSWELL"],
    "NEW YORK": ["BROOKLYN", "QUEENS", "JERSEY CITY", "HOBOKEN", "BRONX", "NEWARK"],
    "LOS ANGELES": ["SANTA MONICA", "BURBANK", "PASADENA", "LONG BEACH", "INGLEWOOD"],
    "CHICAGO": ["EVANSTON", "OAK PARK", "CICERO", "SKOKIE"],
    "MIAMI": ["MIAMI BEACH", "CORAL GABLES", "HIALEAH", "DORAL"],
}

MERCHANT_CATEGORIES = {
    "GROCERY": {
        "low": ["WAL-MART SUPERCENTER", "ALDI", "KROGER", "FOOD DEPOT"],
        "med": ["KROGER", "PUBLIX SUPER MARKETS", "TRADER JOES", "TARGET GROCERY"],
        "high": ["WHOLE FOODS MARKET", "SPROUTS FARMERS MARKET", "THE FRESH MARKET", "PUBLIX GREENWISE"]
    },
    "DINING": {
        "low": ["MCDONALDS", "BURGER KING", "TACO BELL", "WENDYS", "CHICK-FIL-A", "POPEYES"],
        "med": ["CHILI'S GRILL & BAR", "APPLEBEE'S", "OLIVE GARDEN", "PANERA BREAD", "CHIPOTLE", "STARBUCKS COFFEE"],
        "high": ["RUTH'S CHRIS STEAK HOUSE", "THE CAPITAL GRILLE", "BONEFISH GRILL", "SEASONS 52", "MAGGIANO'S"]
    },
    "RETAIL": {
        "low": ["DOLLAR GENERAL", "FAMILY DOLLAR", "WALMART", "GOODWILL"],
        "med": ["TARGET", "TJ MAXX", "MARSHALLS", "ROSS DRESS FOR LESS", "OLD NAVY", "GAP"],
        "high": ["NORDSTROM", "BLOOMINGDALES", "MACY'S", "LULULEMON", "ANTHROPOLOGIE"]
    },
    "GAS": ["SHELL OIL", "QT #", "EXXON MOBIL", "CHEVRON", "BP", "RACE TRAC"],
    "SERVICES": ["USPS", "UPS STORE", "FEDEX OFFICE", "LA FITNESS", "PLANET FITNESS", "CINEMARK", "AMC THEATRES"],
    "TRAVEL": ["DELTA AIR LINES", "UBER TRIP", "LYFT RIDE", "HILTON HOTELS", "MARRIOTT", "ENTERPRISE RENT-A-CAR"],
    "OFFICE_LUNCH": ["SUBWAY", "JIMMY JOHNS", "JERSEY MIKES", "DUNKIN", "STARBUCKS", "EINSTEIN BROS BAGELS"]
}

GENDER_SPECIFIC = {
    "female": ["SEPHORA", "ULTA BEAUTY", "BATH & BODY WORKS", "VICTORIAS SECRET", "H&M", "ZARA"],
    "male": ["AUTOZONE", "ADVANCE AUTO PARTS", "HOME DEPOT", "LOWES", "DICK'S SPORTING GOODS", "BASS PRO SHOPS"]
}

def get_nearby_city(home_city):
    """Returns a city within ~20 miles based on the home city."""
    home_city_upper = home_city.upper().strip()
    if home_city_upper in NEIGHBORING_CITIES:
        # 70% chance to be in a neighboring city, 30% home city
        if random.random() < 0.7:
            return random.choice(NEIGHBORING_CITIES[home_city_upper])
    return home_city_upper

def generate_transactions(start_date_str, end_date_str, profile, count=15):
    """
    Generates a list of transactions based on the user profile.
    
    Args:
        start_date_str (str): "MM/DD/YYYY"
        end_date_str (str): "MM/DD/YYYY"
        profile (dict): {
            "income": "low"|"med"|"high",
            "gender": "male"|"female",
            "position": "office"|"travel"|"remote"|"labor",
            "home_city": "Atlanta",
            "home_state": "GA"
        }
        count (int): Number of transactions to generate.
        
    Returns:
        list: List of dicts { "date": "MM/DD", "description": "...", "amount": float, "balance": 0 }
    """
    
    start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y")
    end_date = datetime.datetime.strptime(end_date_str, "%m/%d/%Y")
    days_diff = (end_date - start_date).days
    
    transactions = []
    
    income = profile.get("income", "med")
    gender = profile.get("gender", "male")
    position = profile.get("position", "office")
    home_city = profile.get("home_city", "ATLANTA")
    home_state = profile.get("home_state", "GA")
    
    # Weighting Logic
    categories = ["GROCERY", "DINING", "GAS", "RETAIL", "SERVICES"]
    weights = [30, 30, 15, 15, 10] # Default weights
    
    if position == "travel":
        categories.append("TRAVEL")
        weights = [20, 30, 10, 10, 5, 25] # Heavy travel
    elif position == "office":
        categories.append("OFFICE_LUNCH")
        weights = [25, 20, 15, 15, 10, 15] # Lots of lunches/coffee
        
    for _ in range(count):
        # 1. Date
        random_days = random.randint(0, days_diff)
        tx_date = start_date + datetime.timedelta(days=random_days)
        date_str = tx_date.strftime("%m/%d")
        
        # 2. Category Selection
        cat = random.choices(categories, weights=weights, k=1)[0]
        
        # 3. Merchant Selection
        merchant_name = ""
        amount = 0.0
        
        if cat in ["GROCERY", "DINING", "RETAIL"]:
            # Check for gender specific override (10% chance)
            if cat == "RETAIL" and random.random() < 0.15:
                merchant_name = random.choice(GENDER_SPECIFIC.get(gender, MERCHANT_CATEGORIES["RETAIL"][income]))
            else:
                merchant_list = MERCHANT_CATEGORIES[cat].get(income, MERCHANT_CATEGORIES[cat]["med"])
                merchant_name = random.choice(merchant_list)
                
            # Amount Logic
            if cat == "GROCERY":
                amount = random.uniform(40, 250) if income == "high" else random.uniform(20, 120)
            elif cat == "DINING":
                amount = random.uniform(50, 150) if income == "high" else random.uniform(8, 35)
            elif cat == "RETAIL":
                amount = random.uniform(50, 300)
                
        elif cat == "GAS":
            merchant_name = random.choice(MERCHANT_CATEGORIES["GAS"])
            amount = random.uniform(30, 70)
            
        elif cat == "SERVICES":
            merchant_name = random.choice(MERCHANT_CATEGORIES["SERVICES"])
            amount = random.uniform(10, 60)
            
        elif cat == "TRAVEL":
            merchant_name = random.choice(MERCHANT_CATEGORIES["TRAVEL"])
            amount = random.uniform(20, 100) # Uber/Lyft
            if "AIR LINES" in merchant_name: amount = random.uniform(200, 600)
            if "HOTELS" in merchant_name: amount = random.uniform(150, 400)
            
        elif cat == "OFFICE_LUNCH":
            merchant_name = random.choice(MERCHANT_CATEGORIES["OFFICE_LUNCH"])
            amount = random.uniform(5, 20)

        # 4. Location Logic
        # Some merchants are online
        if any(x in merchant_name for x in ["AMZN", "NETFLIX", "APPLE.COM", "UBER", "LYFT"]):
            city_str = "" # No city for digital/service usually, or generic
        else:
            city = get_nearby_city(home_city)
            city_str = f" {city} {home_state}"
            
        # Add random store number for chains
        if any(x in merchant_name for x in ["WAL-MART", "KROGER", "TARGET", "PUBLIX", "QT", "MCDONALDS"]):
             if "#" not in merchant_name:
                 merchant_name += f" #{random.randint(100, 999)}"
        
        full_desc = f"{merchant_name}{city_str}".strip()
        
        transactions.append({
            "date": date_str,
            "description": full_desc,
            "amount": -round(amount, 2),
            "balance": 0
        })
        
    # Sort by date
    transactions.sort(key=lambda x: x['date'])
    return transactions
