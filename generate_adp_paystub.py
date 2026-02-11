import json
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph

def num_to_words(amount):
    """Simple converter for the specific amount range needed."""
    # Since the amount is fixed/predictable for this task ($1850.75), 
    # I'll implement a basic converter to be safe, but keep it simple.
    # For a full production system, use 'num2words' library.
    
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def convert_hundreds(n):
        if n == 0: return ""
        s = ""
        if n >= 100:
            s += units[n // 100] + " Hundred "
            n %= 100
        if n >= 20:
            s += tens[n // 10] + " "
            n %= 10
        if n >= 10:
            s += teens[n - 10] + " "
            n = 0
        if n > 0:
            s += units[n] + " "
        return s.strip()

    dollars = int(amount)
    cents = int(round((amount - dollars) * 100))
    
    parts = []
    if dollars >= 1000:
        parts.append(convert_hundreds(dollars // 1000) + " Thousand")
        dollars %= 1000
    
    if dollars > 0:
        parts.append(convert_hundreds(dollars))
        
    text = " ".join(parts)
    return f"{text} and {cents}/100".upper()

def draw_security_pattern(c, x, y, width, height, pattern_type="SECURE"):
    """Draws a repeating background pattern for security."""
    c.saveState()
    # Create a clipping path for the check area
    path = c.beginPath()
    path.rect(x, y, width, height)
    c.clipPath(path, stroke=0)
    
    # Draw repeating text or lines based on pattern type
    c.setFillColor(colors.Color(0.9, 0.95, 0.95)) # Very light blue/gray
    
    if pattern_type == "SECURE":
        c.setFont("Helvetica", 6)
        text = "SECURE DOCUMENT " * 5
        text_width = c.stringWidth(text, "Helvetica", 6)
        
        for row in range(int(y), int(y + height), 10):
            offset = (row % 20) * 2 # Shift every other line
            for col in range(int(x) - 20, int(x + width), int(text_width)):
                c.drawString(col + offset, row, text)
                
    elif pattern_type == "VOID":
        c.setFont("Helvetica-Bold", 48)
        c.setFillColor(colors.Color(0.92, 0.92, 0.92)) # Faint gray
        # Draw large VOID diagonally
        c.saveState()
        c.translate(x + width/2, y + height/2)
        c.rotate(30)
        c.drawCentredString(0, 0, "VOID")
        c.drawCentredString(0, 80, "VOID") 
        c.drawCentredString(0, -80, "VOID")
        c.restoreState()
        
    elif pattern_type == "LINES":
        # Guilloche-style wavy lines (simplified)
        c.setLineWidth(0.5)
        c.setStrokeColor(colors.Color(0.85, 0.9, 0.95))
        for row in range(int(y), int(y + height), 3):
            p = c.beginPath()
            p.moveTo(x, row)
            for col in range(int(x), int(x + width), 5):
                # Simple sine-like wave approximation
                dy = 2 if (col // 5) % 2 == 0 else -2
                p.lineTo(col, row + dy)
            c.drawPath(p)

    elif pattern_type == "ORIGINAL":
        c.setFont("Helvetica-Bold", 6)
        text = "ORIGINAL DOCUMENT - AUTHORIZED SIGNATURE " * 2
        text_width = c.stringWidth(text, "Helvetica", 6)
        
        for row in range(int(y), int(y + height), 12):
            offset = (row % 24) * 3 
            for col in range(int(x) - 40, int(x + width), int(text_width)):
                c.drawString(col + offset, row, text)

    c.restoreState()

def draw_adp_style_stub(c, data, stub_data, y_offset=0, security_pattern="SECURE"):
    width, height = LETTER
    # Colors
    light_gray = colors.Color(0.96, 0.96, 0.96)
    medium_gray = colors.Color(0.85, 0.85, 0.85)
    dark_gray = colors.Color(0.4, 0.4, 0.4)
    line_color = colors.Color(0.7, 0.7, 0.7)
    
    # --- Top Header ---
    # Small Info Box (Top Left)
    c.setLineWidth(0.5)
    c.setStrokeColor(line_color)
    c.setFillColor(light_gray)
    c.rect(30, height - 60, 200, 25, fill=1, stroke=1)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 6)
    headers = ["CO. FILE", "DEPT.", "CLOCK", "VCHR.NO", "062"]
    x_pos = 35
    for h in headers:
        c.drawString(x_pos, height - 42, h)
        x_pos += 38
        
    c.setFont("Helvetica", 7)
    values = ["918", "Design", "37661", stub_data["check_number"], "82214"]
    x_pos = 35
    for v in values:
        c.drawString(x_pos, height - 55, v)
        x_pos += 38

    # Company Name & Address
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 85, data["company"]["name"])
    c.setFont("Helvetica", 10)
    c.drawString(30, height - 100, data["company"]["address_line1"])
    c.drawString(30, height - 112, data["company"]["address_line2"])

    # Employee Metadata (Left)
    y_meta = height - 140
    c.setFont("Helvetica", 8)
    c.setFillColor(dark_gray)
    c.drawString(30, y_meta, "Social Security Number:")
    c.drawString(30, y_meta - 12, "Taxable Marital Status:")
    c.drawString(30, y_meta - 24, "Exemptions / Allowances:")
    c.drawString(30, y_meta - 36, "Employee ID:")
    
    c.setFillColor(colors.black)
    c.drawString(130, y_meta, f"XXX-XX-{data['employee']['ssn_last4']}")
    c.drawString(130, y_meta - 12, data["employee"]["filing_status"])
    c.drawString(130, y_meta - 24, str(data["employee"]["exemptions"]))
    c.drawString(130, y_meta - 36, f"ID: {data['employee']['employee_id']}")

    # Right Side Header
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(width - 30, height - 50, "Earnings Statement")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(dark_gray)
    c.drawRightString(width - 100, height - 70, "Period Beginning:")
    c.drawRightString(width - 100, height - 82, "Period Ending:")
    c.drawRightString(width - 100, height - 94, "Pay Date:")
    
    c.setFillColor(colors.black)
    c.drawRightString(width - 30, height - 70, stub_data["pay_period_start"])
    c.drawRightString(width - 30, height - 82, stub_data["pay_period_end"])
    c.drawRightString(width - 30, height - 94, stub_data["pay_date"])

    # Employee Address (Right)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, height - 130, data["employee"]["name"])
    c.setFont("Helvetica", 10)
    c.drawString(350, height - 145, data["employee"]["address_line1"])
    c.drawString(350, height - 157, data["employee"]["address_line2"])

    # --- Earnings Section ---
    y_start = height - 200
    
    # Headers
    c.setStrokeColor(line_color)
    c.setLineWidth(1)
    c.line(30, y_start, width - 30, y_start) # Top line
    c.line(30, y_start - 15, width - 30, y_start - 15) # Bottom header line
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, y_start - 11, "Earnings")
    c.drawCentredString(250, y_start - 11, "Rate")
    c.drawCentredString(320, y_start - 11, "Hours")
    c.drawRightString(420, y_start - 11, "Amount")
    c.drawRightString(520, y_start - 11, "Year To Date")
    
    # Earnings Rows
    y_row = y_start - 30
    c.setFont("Helvetica", 9)
    for earn in stub_data["earnings"]:
        c.drawString(30, y_row, earn["description"])
        c.drawCentredString(250, y_row, f"{earn['rate']:.2f}")
        c.drawCentredString(320, y_row, f"{earn['hours']:.2f}")
        c.drawRightString(420, y_row, f"{earn['amount']:,.2f}")
        c.drawRightString(520, y_row, f"{earn['ytd_amount']:,.2f}")
        y_row -= 15
        
    # Gross Pay Line
    y_row -= 5
    c.setFillColor(light_gray)
    c.rect(30, y_row - 2, 500, 15, fill=1, stroke=0) # Background bar
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(170, y_row + 2, "Gross Pay")
    c.drawRightString(420, y_row + 2, f"{stub_data['totals']['gross']:,.2f}")
    c.drawRightString(520, y_row + 2, f"{stub_data['totals']['ytd_gross']:,.2f}")
    
    # --- Deductions Section ---
    y_ded = y_row - 40
    
    # Headers
    c.line(30, y_ded, width - 30, y_ded)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, y_ded + 5, "Deductions")
    # Centering headers over the columns (Columns end at 420 and 520, width approx 60)
    c.drawCentredString(390, y_ded + 5, "Current") 
    c.drawCentredString(490, y_ded + 5, "Year To Date")
    
    y_d = y_ded - 15
    c.setFont("Helvetica-Bold", 9)
    c.drawString(170, y_d, "Statutory")
    y_d -= 15
    
    c.setFont("Helvetica", 9)
    for tax in stub_data["taxes"]:
        c.drawString(170, y_d, tax["description"])
        c.drawRightString(420, y_d, f"-{tax['amount']:,.2f}")
        c.drawRightString(520, y_d, f"{tax['ytd_amount']:,.2f}")
        y_d -= 12
        
    y_d -= 5
    c.setFont("Helvetica-Bold", 9)
    c.drawString(170, y_d, "Other")
    y_d -= 15
    
    c.setFont("Helvetica", 9)
    for ded in stub_data["deductions"]:
        c.drawString(170, y_d, ded["description"])
        c.drawRightString(420, y_d, f"-{ded['amount']:,.2f}")
        c.drawRightString(520, y_d, f"{ded['ytd_amount']:,.2f}")
        y_d -= 12

    # Net Pay Box
    y_net = y_d - 20
    c.setFillColor(medium_gray)
    c.rect(30, y_net - 5, 500, 20, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y_net + 2, "Net Pay")
    c.drawRightString(420, y_net + 2, f"${stub_data['net_pay']:,.2f}")
    
    # Check distribution line
    y_net -= 20
    c.setFillColor(light_gray)
    c.rect(30, y_net - 5, 500, 20, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    c.drawString(40, y_net + 2, "Check / Direct Deposit")
    
    # Show masked account number in Distribution if available
    # Assuming 'distribution_account' is passed in stub_data, else default
    dist_account = stub_data.get('distribution_account', 'XXXXXX1234')
    c.drawString(200, y_net + 2, f"Acct: {dist_account}")
    
    c.drawRightString(420, y_net + 2, f"${stub_data['net_pay']:,.2f}")

    # --- Perforation ---
    y_perf = 250
    c.setDash(3, 3)
    c.setLineWidth(0.5)
    c.line(0, y_perf, width, y_perf)
    c.setDash()
    
    # --- Voucher / Check ---
    # Draw security pattern
    draw_security_pattern(c, 20, 20, width - 40, y_perf - 40, pattern_type=security_pattern)

    # Draw check background (subtle pattern or security features)
    c.saveState()
    # Microprint border (fake)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    # Top border of check area
    c.line(20, y_perf - 20, width - 20, y_perf - 20)
    # Bottom border
    c.line(20, 20, width - 20, 20)
    c.restoreState()
    
    check_top = y_perf - 20
    
    # 1. Company Info (Top Left of Check)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, check_top - 30, data["company"]["name"])
    c.setFont("Helvetica", 9)
    c.drawString(40, check_top - 42, data["company"]["address_line1"])
    c.drawString(40, check_top - 54, data["company"]["address_line2"])
    
    # 2. Check Number / Date Info (Top Right)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 40, check_top - 30, f"NO. {stub_data['check_number']}")
    
    # Fractional Routing Number (Fake)
    c.setFont("Helvetica", 8)
    c.drawString(width - 150, check_top - 45, "64-80/610")
    
    c.setFont("Helvetica", 9)
    c.drawString(width - 150, check_top - 60, "DATE")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 100, check_top - 60, stub_data["pay_date"])
    c.line(width - 100, check_top - 62, width - 40, check_top - 62)

    # 3. Pay To The Order Of
    y_pay = check_top - 90
    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, y_pay, "PAY TO THE")
    c.drawString(40, y_pay - 12, "ORDER OF")
    
    # Payee Name
    c.setFont("Helvetica-Bold", 11)
    c.drawString(110, y_pay - 6, data["employee"]["name"])
    c.line(110, y_pay - 8, 350, y_pay - 8)
    
    # Amount Box (Right)
    c.rect(width - 150, y_pay - 15, 110, 25, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 45, y_pay - 6, f"${stub_data['net_pay']:,.2f}")
    
    # 4. Amount in Words Line (Second Line)
    y_words = y_pay - 35
    amount_text = num_to_words(stub_data["net_pay"])
    c.setFont("Helvetica", 10)
    c.drawString(40, y_words, amount_text)
    
    # Line under words
    c.line(40, y_words - 2, width - 160, y_words - 2)
    
    # "DOLLARS" at the end
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 40, y_words, "DOLLARS")
    
    # 5. Bank Info (Bottom Left)
    y_bank = y_words - 40
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y_bank, data["company"].get("bank_name", "Wells Fargo"))
    c.setFont("Helvetica", 9)
    c.drawString(40, y_bank - 12, data["company"].get("bank_address_line1", "333 Market Street"))
    c.drawString(40, y_bank - 24, data["company"].get("bank_address_line2", "San Francisco, CA 94105"))
    
    # 6. Signature Line (Bottom Right)
    y_sig = y_bank
    c.line(width - 250, y_sig - 10, width - 40, y_sig - 10)
    c.setFont("Helvetica", 8)
    c.drawRightString(width - 40, y_sig, "AUTHORIZED SIGNATURE")
    
    # Signature "Kent Jones"
    # Attempt to use a cursive-ish standard font if possible, or just italic
    try:
        c.setFont("ZapfChancery-MediumItalic", 16)
    except:
        c.setFont("Times-Italic", 16)
    c.drawString(width - 218, y_sig - 5, data["company"].get("signature_name", "Kent Jones"))
    
    # 7. MICR Line
    y_micr = 35
    # Use Courier to simulate MICR spacing roughly if MICR font unavailable
    c.setFont("Courier", 12)
    
    # Use provided Routing/Account or fallback
    routing = stub_data.get("company_routing", "121000248")
    account = stub_data.get("company_account", "712975555")
    check_num = stub_data["check_number"]
    
    # Format: A[Routing]A  [Account]C  [CheckNumber]
    # A = Transit, C = On-Us (Account)
    micr_sim = f"A{routing}A  {account}C  {check_num}"
    c.drawCentredString(width/2, y_micr, micr_sim)

    # Security Feature (Lock Icon placeholder)
    c.rect(width/2 - 10, y_micr + 20, 20, 20, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y_micr + 24, "MP") # MicroPrint symbol

def generate_paystubs():
    # Load Data
    with open('tifiney_data.json', 'r') as f:
        data = json.load(f)
        
    output_dir = "TiffanyPageStubs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for i, stub in enumerate(data["pay_stubs"]):
        filename = os.path.join(output_dir, f"Tifiney_Goins_Paystub_{i+1}.pdf")
        c = canvas.Canvas(filename, pagesize=LETTER)
        draw_adp_style_stub(c, data, stub)
        c.save()
        print(f"Generated {filename}")

if __name__ == "__main__":
    generate_paystubs()
