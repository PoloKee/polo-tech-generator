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

# Map states to common regional grocery/gas chains
REGIONAL_CHAINS = {
    "GA": {
        "GROCERY": ["PUBLIX SUPER MARKETS", "KROGER", "WHOLE FOODS MARKET", "TRADER JOES", "ALDI", "FOOD DEPOT"],
        "GAS": ["QT #", "RACETRAC", "SHELL OIL", "BP", "EXXON MOBIL"],
        "UTILITY": ["GEORGIA POWER", "COBB EMC", "ATLANTA GAS LIGHT"]
    },
    "FL": {
        "GROCERY": ["PUBLIX", "WINN-DIXIE", "WHOLE FOODS", "TRADER JOES", "ALDI", "FRESCO Y MAS"],
        "GAS": ["WAWA", "SHELL", "RACETRAC", "SUNOCO", "EXXON"],
        "UTILITY": ["FLORIDA POWER & LIGHT", "DUKE ENERGY", "TECO"]
    },
    "NY": {
        "GROCERY": ["STOP & SHOP", "WEGMANS", "WHOLE FOODS", "TRADER JOES", "KEY FOOD", "SHOPRITE"],
        "GAS": ["BP", "EXXON", "SUNOCO", "SHELL", "MOBIL"],
        "UTILITY": ["CON EDISON", "NATIONAL GRID", "PSEG"]
    },
    "CA": {
        "GROCERY": ["VONS", "SAFEWAY", "RALPHS", "WHOLE FOODS", "TRADER JOES", "SPROUTS"],
        "GAS": ["CHEVRON", "ARCO", "SHELL", "76", "MOBIL"],
        "UTILITY": ["PG&E", "SOCAL EDISON", "LADWP"]
    },
    "IL": {
        "GROCERY": ["JEWEL-OSCO", "MARIANO'S", "ALDI", "WHOLE FOODS", "TRADER JOES"],
        "GAS": ["BP", "SHELL", "CITGO", "MOBIL", "SPEEDWAY"],
        "UTILITY": ["COMED", "NICOR GAS", "PEOPLES GAS"]
    },
    "DEFAULT": {
        "GROCERY": ["WALMART SUPERCENTER", "KROGER", "ALDI", "TARGET GROCERY", "WHOLE FOODS"],
        "GAS": ["SHELL", "EXXON", "BP", "CHEVRON", "MOBIL"],
        "UTILITY": ["CITY UTILITIES", "COUNTY WATER", "ENERGY CO"]
    }
}

MERCHANT_CATEGORIES = {
    "DINING": {
        "low": ["MCDONALDS", "BURGER KING", "TACO BELL", "WENDYS", "CHICK-FIL-A", "POPEYES", "DUNKIN", "DOMINOS PIZZA"],
        "med": ["CHILI'S GRILL & BAR", "APPLEBEE'S", "OLIVE GARDEN", "PANERA BREAD", "CHIPOTLE", "STARBUCKS COFFEE", "BUFFALO WILD WINGS", "TEXAS ROADHOUSE"],
        "high": ["RUTH'S CHRIS STEAK HOUSE", "THE CAPITAL GRILLE", "BONEFISH GRILL", "SEASONS 52", "MAGGIANO'S", "CHEESECAKE FACTORY"]
    },
    "RETAIL": {
        "low": ["DOLLAR GENERAL", "FAMILY DOLLAR", "WALMART", "GOODWILL", "FIVE BELOW"],
        "med": ["TARGET", "TJ MAXX", "MARSHALLS", "ROSS DRESS FOR LESS", "OLD NAVY", "GAP", "BEST BUY", "DICK'S SPORTING GOODS"],
        "high": ["NORDSTROM", "BLOOMINGDALES", "MACY'S", "LULULEMON", "ANTHROPOLOGIE", "APPLE STORE", "SEPHORA"]
    },
    "SERVICES": ["USPS", "UPS STORE", "FEDEX OFFICE", "LA FITNESS", "PLANET FITNESS", "CINEMARK", "AMC THEATRES", "GREAT CLIPS", "SUPERCUTS"],
    "TRAVEL": ["DELTA AIR LINES", "UBER TRIP", "LYFT RIDE", "HILTON HOTELS", "MARRIOTT", "ENTERPRISE RENT-A-CAR", "AMERICAN AIRLINES", "AIRBNB"],
    "OFFICE_LUNCH": ["SUBWAY", "JIMMY JOHNS", "JERSEY MIKES", "DUNKIN", "STARBUCKS", "EINSTEIN BROS BAGELS", "PANDA EXPRESS", "CHIPOTLE"],
    "ONLINE": ["AMZN Mktp US", "Amazon.com", "APPLE.COM/BILL", "GOOGLE *SERVICES", "PAYPAL", "UBER EATS"]
}

RECURRING_BILLS = {
    "UTILITIES": ["WATER BILL", "ELECTRIC BILL", "GAS BILL", "WASTE MANAGEMENT"],
    "TELECOM": ["VERIZON WIRELESS", "AT&T MOBILITY", "T-MOBILE", "XFINITY MOBILE"],
    "INTERNET_CABLE": ["COMCAST XFINITY", "SPECTRUM", "COX COMMUNICATIONS", "AT&T FIBER", "DIRECTV"],
    "INSURANCE": ["GEICO", "STATE FARM", "PROGRESSIVE", "ALLSTATE", "USAA P&C"],
    "SUBSCRIPTIONS": ["NETFLIX.COM", "SPOTIFY USA", "HULU", "DISNEY PLUS", "YOUTUBE PREMIUM", "APPLE MUSIC", "PRIME VIDEO"]
}

def get_regional_merchants(state, category):
    """Returns regional merchants if available, else default."""
    region_data = REGIONAL_CHAINS.get(state, REGIONAL_CHAINS["DEFAULT"])
    return region_data.get(category, REGIONAL_CHAINS["DEFAULT"].get(category, []))

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
    Generates a list of transactions based on the user profile with realistic logic.
    
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
        count (int): Approximate number of transactions to generate (excluding bills).
        
    Returns:
        list: List of dicts { "date": "MM/DD", "description": "...", "amount": float, "balance": 0 }
    """
    
    start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y")
    end_date = datetime.datetime.strptime(end_date_str, "%m/%d/%Y")
    days_diff = (end_date - start_date).days
    
    transactions = []
    
    income = profile.get("income", "med")
    position = profile.get("position", "office")
    home_city = profile.get("home_city", "ATLANTA")
    home_state = profile.get("home_state", "GA").upper()
    
    # --- 1. Generate Recurring Bills (Once per month) ---
    # We iterate through each month in the range
    
    current_date = start_date
    while current_date <= end_date:
        # Determine if we should add bills for this month
        # Logic: Add bills between 1st and 28th randomly
        
        # Phone Bill
        if random.random() < 0.9: # 90% chance of phone bill
            day_offset = random.randint(0, min(27, days_diff)) # Simple logic: random day in range
            bill_date = start_date + datetime.timedelta(days=day_offset)
            if start_date <= bill_date <= end_date:
                merch = random.choice(RECURRING_BILLS["TELECOM"])
                amt = round(random.uniform(60, 180), 2)
                transactions.append({"date_obj": bill_date, "description": merch, "amount": -amt, "category": "BILL"})

        # Internet/Cable
        if random.random() < 0.8:
            day_offset = random.randint(0, min(27, days_diff))
            bill_date = start_date + datetime.timedelta(days=day_offset)
            if start_date <= bill_date <= end_date:
                merch = random.choice(RECURRING_BILLS["INTERNET_CABLE"])
                amt = round(random.uniform(50, 150), 2)
                transactions.append({"date_obj": bill_date, "description": merch, "amount": -amt, "category": "BILL"})

        # Utilities (Electric/Water)
        if random.random() < 0.95:
            day_offset = random.randint(0, min(27, days_diff))
            bill_date = start_date + datetime.timedelta(days=day_offset)
            if start_date <= bill_date <= end_date:
                # Try to get specific utility for state
                local_utils = get_regional_merchants(home_state, "UTILITY")
                merch = random.choice(local_utils) if local_utils else random.choice(RECURRING_BILLS["UTILITIES"])
                amt = round(random.uniform(80, 250), 2)
                transactions.append({"date_obj": bill_date, "description": merch, "amount": -amt, "category": "BILL"})
        
        # Insurance
        if random.random() < 0.7:
            day_offset = random.randint(0, min(27, days_diff))
            bill_date = start_date + datetime.timedelta(days=day_offset)
            if start_date <= bill_date <= end_date:
                merch = random.choice(RECURRING_BILLS["INSURANCE"])
                amt = round(random.uniform(100, 200), 2)
                transactions.append({"date_obj": bill_date, "description": merch, "amount": -amt, "category": "BILL"})

        # Streaming Subs (Multiple)
        num_subs = random.randint(1, 4)
        for _ in range(num_subs):
            day_offset = random.randint(0, min(27, days_diff))
            bill_date = start_date + datetime.timedelta(days=day_offset)
            if start_date <= bill_date <= end_date:
                merch = random.choice(RECURRING_BILLS["SUBSCRIPTIONS"])
                amt = round(random.uniform(9.99, 19.99), 2)
                transactions.append({"date_obj": bill_date, "description": merch, "amount": -amt, "category": "SUB"})

        # Move to next month (approx) to prevent infinite loop if range > 1 month
        # For this simple generator, we assume the range is usually ~1 month.
        # If range is longer, we might need loop logic. 
        # For now, break after one pass since typical use case is 1 statement period.
        break 

    # --- 2. Generate Daily Spending ---
    
    # Weighting Logic
    categories = ["GROCERY", "DINING", "GAS", "RETAIL", "SERVICES", "ONLINE"]
    weights = [25, 25, 15, 15, 10, 10] # Default weights
    
    if position == "travel":
        categories.append("TRAVEL")
        weights = [15, 25, 10, 10, 5, 5, 30] # Heavy travel
    elif position == "office":
        categories.append("OFFICE_LUNCH")
        weights = [20, 20, 15, 15, 5, 10, 15] # Lots of lunches
        
    for _ in range(count):
        # 1. Date
        random_days = random.randint(0, days_diff)
        tx_date = start_date + datetime.timedelta(days=random_days)
        
        # 2. Category Selection
        cat = random.choices(categories, weights=weights, k=1)[0]
        
        # 3. Merchant & Amount Selection
        description = ""
        amount = 0.0
        
        if cat == "GROCERY":
            merchants = get_regional_merchants(home_state, "GROCERY")
            description = random.choice(merchants)
            # Add City context often
            if random.random() < 0.6:
                description += f" {get_nearby_city(home_city)}"
            amount = random.uniform(30, 250)
            
        elif cat == "GAS":
            merchants = get_regional_merchants(home_state, "GAS")
            description = random.choice(merchants)
            # Gas almost always has location or store number
            if "#" in description:
                description = description + str(random.randint(100, 999))
            description += f" {get_nearby_city(home_city)}"
            amount = random.uniform(25, 70)
            
        elif cat == "DINING":
            # Split by income for dining
            level = "med"
            if income == "high" and random.random() < 0.4: level = "high"
            elif income == "low": level = "low"
            
            description = random.choice(MERCHANT_CATEGORIES["DINING"][level])
            if random.random() < 0.5:
                description += f" {get_nearby_city(home_city)}"
            
            if level == "high": amount = random.uniform(80, 300)
            elif level == "med": amount = random.uniform(20, 80)
            else: amount = random.uniform(8, 25)

        elif cat == "OFFICE_LUNCH":
            description = random.choice(MERCHANT_CATEGORIES["OFFICE_LUNCH"])
            amount = random.uniform(8, 20)
            
        elif cat == "RETAIL":
            level = income if income in ["low", "med", "high"] else "med"
            description = random.choice(MERCHANT_CATEGORIES["RETAIL"][level])
            amount = random.uniform(20, 150)
            
        elif cat == "SERVICES":
            description = random.choice(MERCHANT_CATEGORIES["SERVICES"])
            amount = random.uniform(15, 100)
            
        elif cat == "TRAVEL":
            description = random.choice(MERCHANT_CATEGORIES["TRAVEL"])
            amount = random.uniform(30, 500)
            
        elif cat == "ONLINE":
            description = random.choice(MERCHANT_CATEGORIES["ONLINE"])
            amount = random.uniform(10, 200)

        transactions.append({
            "date_obj": tx_date,
            "description": description.upper(),
            "amount": -round(amount, 2),
            "category": cat
        })
        
    # Sort by date
    transactions.sort(key=lambda x: x["date_obj"])
    
    # Format output
    formatted_transactions = []
    for tx in transactions:
        formatted_transactions.append({
            "date": tx["date_obj"].strftime("%m/%d"),
            "description": tx["description"],
            "amount": tx["amount"],
            "balance": 0 # Calculated later
        })
        
    return formatted_transactions
