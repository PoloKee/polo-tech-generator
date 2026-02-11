import json
import math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject, DictionaryObject, ArrayObject
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Ellipse
from reportlab.graphics import renderPDF

# Define Colors
NAVY_BLUE = HexColor("#003087") # Navy Federal Blue
LIGHT_GREY = HexColor("#E0E0E0")
DARK_GREY = HexColor("#404040")

def draw_globe_watermark(c, width, height):
    """Draws a stylized wireframe globe watermark in the background using microdots."""
    # We use a Form XObject to draw the lines opaquely first, then apply transparency 
    # to the whole form. This ensures overlapping lines don't get darker (they "merge").
    
    form_name = "globe_watermark_form"
    
    # Only define the form if it hasn't been defined on this canvas yet
    if not getattr(c, '_globe_watermark_defined', False):
        c.beginForm(form_name)
        c.saveState()
        
        # Solid opaque LIGHT color for the form content
        # Using a very light grey (#F2F2F2) to simulate transparency without alpha blending artifacts (darker overlaps)
        WATERMARK_COLOR = HexColor("#F2F2F2") 
        c.setFillColor(WATERMARK_COLOR) 
        c.setStrokeColor(WATERMARK_COLOR)
        c.setFillAlpha(1.0) 
        c.setStrokeAlpha(1.0)
        c.setLineWidth(14) 

        # Helper for ellipses inside the form
        def draw_ellipse(cx, cy, rx, ry):
            c.ellipse(cx - rx, cy - ry, cx + rx, cy + ry)
            
        def draw_arc_path(cx, cy, rx, ry, start_ang_deg, end_ang_deg):
            extent = end_ang_deg - start_ang_deg
            c.arc(cx - rx, cy - ry, cx + rx, cy + ry, start_ang_deg, extent)

        # Center of the globe - positioned behind the summary table
        cx, cy = width / 2, height / 2 - 50 
        radius = 220 
        
        # Draw Sphere Outline (Circle)
        c.circle(cx, cy, radius)
        
        # Draw Center Lines (Equator and Prime Meridian)
        c.line(cx, cy - radius, cx, cy + radius) # Vertical (Prime Meridian)
        c.line(cx - radius, cy, cx + radius, cy) # Horizontal (Equator)
        
        # Draw Longitude Lines (Vertical Ellipses)
        draw_ellipse(cx, cy, 75, radius) 
        draw_ellipse(cx, cy, 150, radius) 
        
        # Draw Latitude Lines (Horizontal Arcs)
        
        # North Latitudes (Curve Up)
        lat_y = 70
        lat_w = math.sqrt(radius**2 - lat_y**2)
        draw_arc_path(cx, cy + lat_y, lat_w, 40, 0, 180) 
        
        lat_y = 140
        lat_w = math.sqrt(radius**2 - lat_y**2)
        draw_arc_path(cx, cy + lat_y, lat_w, 30, 0, 180)
        
        # South Latitudes (Curve Down)
        lat_y = 70
        lat_w = math.sqrt(radius**2 - lat_y**2)
        draw_arc_path(cx, cy - lat_y, lat_w, 40, 180, 360)
        
        lat_y = 140
        lat_w = math.sqrt(radius**2 - lat_y**2)
        draw_arc_path(cx, cy - lat_y, lat_w, 30, 180, 360)
        
        c.restoreState()
        c.endForm()
        
        # Mark as defined
        c._globe_watermark_defined = True

    # Now draw the form OPAQUELY (color is already light)
    c.saveState()
    # No transparency applied here to avoid overlap darkening
    c.setFillAlpha(1.0) 
    c.setStrokeAlpha(1.0)
    c.doForm(form_name)
    c.restoreState()



def add_calculations_to_pdf(input_path, output_path, data):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Copy pages
    for page in reader.pages:
        writer.add_page(page)

    page = writer.pages[0]
    if "/Annots" in page:
        for annot in page["/Annots"]:
            annot_obj = annot.get_object()
            if "/T" in annot_obj: # It's a field with a name
                field_name = annot_obj["/T"]
                
                # --- Row Calculations ---
                if field_name.startswith("acc_") and field_name.endswith("_ending_balance"):
                    # Extract index
                    parts = field_name.split("_")
                    idx = parts[1] # acc_0_ending_balance -> 0
                    
                    # Construct JS for Ending Balance = Prev + Dep - With
                    js_code = f'''
                    var prev = this.getField("acc_{idx}_previous_balance").value;
                    var dep = this.getField("acc_{idx}_deposits_credits").value;
                    var withdr = this.getField("acc_{idx}_withdrawals_debits").value;
                    
                    function clean(val) {{
                        var s = val.toString().replace(/[^0-9.-]/g, "");
                        return Number(s);
                    }}
                    
                    var result = clean(prev) + clean(dep) - clean(withdr);
                    event.value = util.printf("$%.2f", result);
                    '''
                    
                    # Add AA (Additional Actions) -> C (Calculate) dictionary
                    aa_dict = DictionaryObject()
                    if "/AA" in annot_obj:
                        aa_dict = annot_obj["/AA"]

                    js_action = DictionaryObject()
                    js_action.update({
                        NameObject("/S"): NameObject("/JavaScript"),
                        NameObject("/JS"): TextStringObject(js_code)
                    })
                    
                    aa_dict.update({
                        NameObject("/C"): js_action
                    })
                    
                    annot_obj[NameObject("/AA")] = aa_dict
                    
                # --- Total Calculations ---
                elif field_name.startswith("total_"):
                    # total_previous_balance
                    key = field_name.replace("total_", "")
                    
                    # Sum all accounts for this key
                    num_accounts = len(data['accounts'])
                    fields_to_sum = [f"acc_{i}_{key}" for i in range(num_accounts)]
                    
                    # Construct JS
                    js_lines = []
                    js_lines.append("var total = 0;")
                    for f_name in fields_to_sum:
                        js_lines.append(f'total += Number(this.getField("{f_name}").value.toString().replace(/[^0-9.-]/g, ""));')
                    
                    js_lines.append('event.value = util.printf("$%.2f", total);')
                    
                    js_code = "\n".join(js_lines)
                    
                    # Add AA -> C
                    aa_dict = DictionaryObject()
                    if "/AA" in annot_obj:
                        aa_dict = annot_obj["/AA"]
                        
                    js_action = DictionaryObject()
                    js_action.update({
                        NameObject("/S"): NameObject("/JavaScript"),
                        NameObject("/JS"): TextStringObject(js_code)
                    })
                    aa_dict.update({
                        NameObject("/C"): js_action
                    })
                    
                    annot_obj[NameObject("/AA")] = aa_dict

    with open(output_path, "wb") as f_out:
        writer.write(f_out)

def draw_change_of_address_form(c, width, bottom_y):
    """Draws the Change of Address form at the bottom of the page."""
    # Form constants
    x_left = 25
    x_right = width - 40
    form_width = x_right - x_left
    row_height = 25
    
    # Alignment Squares (Grey boxes often seen on these forms)
    c.setFillColor(colors.grey)
    c.rect(x_left, bottom_y + 5 * row_height + 15, 12, 12, fill=1, stroke=0)
    c.rect(x_right - 12, bottom_y + 5 * row_height + 15, 12, 12, fill=1, stroke=0)
    c.setFillColor(colors.black)

    # Header
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width/2, bottom_y + 5 * row_height + 25, "CHANGE OF ADDRESS")
    c.setFont("Helvetica", 7)
    c.drawCentredString(width/2, bottom_y + 5 * row_height + 15, "PLEASE PRINT. USE BLUE OR BLACK BALL POINT PEN.")
    
    # Main Box Outline
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.rect(x_left, bottom_y, form_width, 5 * row_height)
    
    # Horizontal Lines
    for i in range(1, 5):
        y = bottom_y + i * row_height
        c.line(x_left, y, x_right, y)
        
    # --- Vertical Lines and Text ---
    
    # Right column (Account Numbers Affected) - Spans top 4 rows
    x_col_right = x_right - 150
    c.line(x_col_right, bottom_y + row_height, x_col_right, bottom_y + 5 * row_height)
    
    # Row 5 (Top Row): RANK/RATE | NAME | ACC #s
    y_row5 = bottom_y + 4 * row_height
    c.line(x_left + 80, y_row5, x_left + 80, y_row5 + row_height) # Rank separator
    
    c.setFont("Helvetica", 6)
    c.drawString(x_left + 2, y_row5 + row_height - 8, "RANK/RATE")
    c.drawString(x_left + 82, y_row5 + row_height - 8, "NAME (FIRST                       MI                         LAST)")
    c.drawString(x_col_right + 2, y_row5 + row_height - 8, "ACCOUNT NUMBERS AFFECTED")
    
    # Row 4: ADDRESS
    y_row4 = bottom_y + 3 * row_height
    c.drawString(x_left + 2, y_row4 + row_height - 8, "ADDRESS (NO. STREET)")
    
    # Row 3: CITY | STATE | ZIP
    y_row3 = bottom_y + 2 * row_height
    # Vert lines
    c.line(x_left + 220, y_row3, x_left + 220, y_row3 + row_height) # After City
    c.line(x_left + 300, y_row3, x_left + 300, y_row3 + row_height) # After State
    
    c.drawString(x_left + 2, y_row3 + row_height - 8, "CITY")
    c.drawString(x_left + 222, y_row3 + row_height - 8, "STATE")
    c.drawString(x_left + 302, y_row3 + row_height - 8, "ZIP CODE")
    
    # Row 2: SIGNATURE
    y_row2 = bottom_y + 1 * row_height
    c.drawString(x_left + 2, y_row2 + row_height - 8, "SIGNATURE OF NAVY FEDERAL MEMBER")
    
    # Row 1 (Bottom): EFFECTIVE DATE | HOME PHONE | DAY PHONE
    y_row1 = bottom_y
    # Vert lines for bottom row
    c.line(x_left + 120, y_row1, x_left + 120, y_row1 + row_height)
    c.line(x_left + 320, y_row1, x_left + 320, y_row1 + row_height)
    
    c.drawString(x_left + 2, y_row1 + row_height - 8, "EFFECTIVE DATE (MO., DAY, YR.)")
    c.drawString(x_left + 122, y_row1 + row_height - 8, "HOME TELEPHONE NUMBER")
    c.drawString(x_left + 322, y_row1 + row_height - 8, "DAYTIME TELEPHONE NUMBER")
    
    # Fillers
    c.drawString(x_left + 10, y_row1 + 5, "    -        -    ")
    c.drawString(x_left + 125, y_row1 + 5, "(          )")
    c.drawString(x_left + 325, y_row1 + 5, "(          )")

def draw_disclosure_section(c, width, height, y_start, page_num, total_pages, data):
    """
    Draws the Disclosure Information section.
    Handles page breaks internally if needed, but primarily intended for the last page.
    Returns the new y position and current page number.
    """
    from reportlab.lib.utils import simpleSplit
    
    x_left = 25
    x_right = width - 25
    text_width = x_right - x_left
    
    # Check if we need a new page immediately
    # This section is long (~650pts), so if we are below ~700, we probably need a new page
    # But let's check properly.
    
    # Constants
    h_font = "Helvetica-Bold"
    b_font = "Helvetica"
    h_size = 9
    b_size = 7
    leading = 9
    
    # Helper to check page break
    def check_page_break(y, needed_space, p_num):
        if y < needed_space:
             c.showPage()
             p_num += 1
             draw_globe_watermark(c, width, height)
             # Use the persistent header for consistency
             new_y = draw_persistent_header(c, width, height, data, p_num, total_pages)
             return new_y, p_num
        return y, p_num

    y = y_start
    
    # 1. Header: Disclosure Information
    y, page_num = check_page_break(y, 600, page_num) # Needs a lot of space, force new page mostly
    
    c.setFont(h_font, h_size)
    c.drawString(x_left, y, "Disclosure Information")
    y -= leading + 2
    
    # Bullets
    bullets = [
        "The interest charge on the Checking Line of Credit advances begins to accrue on the date an advance is posted to your account and continues to accrue daily on the unpaid principal balance.",
        "We calculate the interest charge on your account by applying the daily periodic rate to the \"daily balance\" of your account for each day in the billing cycle. To get the \"daily balance\" we take the beginning balance of your account each day, add any new advances or fees, and subtract any payments, credits, or unpaid interest charges.",
        "You may also determine the amount of interest charges by multiplying the \"Balance Subject to Interest Rate\" by the number of days in the billing cycle and the daily periodic rate. The \"Balance Subject to Interest Rate\" disclosed in the Interest Charge Calculation table is the \"average daily balance.\" To calculate the \"average daily balance\" add up all the \"daily balances\" for the billing cycle and divide the total by the number of days in the billing cycle.",
        "If there are two or more daily periodic rates imposed during the billing cycle, you may determine the amount of interest charges by multiplying each of the \"Balances Subject to Interest Rate\" by the number of days the applicable rate was in effect and multiplying each of the results by the applicable daily periodic rate and adding the results together."
    ]
    
    c.setFont(b_font, b_size)
    for b in bullets:
        lines = simpleSplit(b, b_font, b_size, text_width - 10)
        # Check space for whole bullet
        y, page_num = check_page_break(y, len(lines) * leading + 10, page_num)
        
        # Draw Bullet dot
        c.drawString(x_left, y, "•")
        
        # Draw lines
        curr_y = y
        for line in lines:
            c.drawString(x_left + 10, curr_y, line)
            curr_y -= leading
        y = curr_y - 3 # Space after bullet
        
    y -= 5
    
    # 2. Header: What to Do...
    c.setFont(h_font, h_size)
    y, page_num = check_page_break(y, 40, page_num)
    c.drawString(x_left, y, "What to Do if You Think You Find a Mistake on Your Statement")
    y -= leading
    
    c.setFont(h_font, h_size)
    c.drawString(x_left, y, "Errors Related to a Checking Line of Credit Advance")
    y -= leading
    
    c.setFont(b_font, b_size)
    text = "If you think there is an error on your statement, write to us at:"
    c.drawString(x_left, y, text)
    y -= leading
    
    c.setFont(h_font, b_size) # Bold address
    c.drawString(x_left, y, "Navy Federal Credit Union, PO Box 3000, Merrifield, VA 22119-3000; or by fax, 1-703-206-4244.")
    y -= leading
    
    c.setFont(b_font, b_size)
    c.drawString(x_left, y, "You may also contact us on the Web: navyfederal.org.")
    y -= leading
    
    c.drawString(x_left, y, "In your letter, give us the following information:")
    y -= leading
    
    # Bullets 2
    bullets_2 = [
        ("Account information:", "Your name and account number."),
        ("Dollar amount:", "The dollar amount of the suspected error."),
        ("Description of problem:", "If you think there is an error on your bill, describe what you believe is wrong and why you believe it is a mistake.")
    ]
    
    for bold_part, rest in bullets_2:
        full_text = bold_part + " " + rest
        lines = simpleSplit(full_text, b_font, b_size, text_width - 10)
        y, page_num = check_page_break(y, len(lines)*leading + 5, page_num)
        
        c.drawString(x_left, y, "•")
        # Bold the first part manually? A bit hard with simpleSplit.
        # Simplification: Draw the whole line in normal font, but maybe overdraw the bold part?
        # Or just use bold font for the first line if it starts with it?
        # Let's just use normal font for simplicity or try to switch.
        
        # Better approach: Draw bold part, then rest.
        # But simpleSplit wraps.
        # Let's just render it all as normal text for now to be safe, or make the whole line bold? No.
        # I'll just render it normal. The user wants visual fidelity but 100% bold matching might be overkill if it breaks layout.
        # Actually, I can check if the first line contains the bold part.
        
        curr_y = y
        c.setFont(b_font, b_size)
        for i, line in enumerate(lines):
            if i == 0:
                # Hacky bolding: Draw bold part if it fits?
                # Let's just draw normal.
                pass
            c.drawString(x_left + 10, curr_y, line)
            curr_y -= leading
        y = curr_y - 2
        
    y -= 5
    
    # Text block
    block_1 = "You must contact us within 60 days after the error appeared on your statement. You must notify us of any potential errors in writing (or electronically). You may call us, but if you do, we are not required to investigate any potential error, and you may have to pay the amount in question."
    lines = simpleSplit(block_1, b_font, b_size, text_width)
    y, page_num = check_page_break(y, len(lines)*leading, page_num)
    for line in lines:
        c.drawString(x_left, y, line)
        y -= leading
    
    y -= 5
    c.drawString(x_left, y, "While we investigate whether or not there has been an error, the following are true:")
    y -= leading
    
    bullets_3 = [
        "We cannot try to collect the amount in question or report you as delinquent on that amount.",
        "The charge in question may remain on your statement, and we may continue to charge you interest on that amount. But, if we determine that we made a mistake, you will not have to pay the amount in question or any interest or other fees related to that amount.",
        "While you do not have to pay the amount in question, you are responsible for the remainder of your balance.",
        "We can apply any unpaid amount against your credit limit."
    ]
    
    for b in bullets_3:
        lines = simpleSplit(b, b_font, b_size, text_width - 10)
        y, page_num = check_page_break(y, len(lines)*leading + 5, page_num)
        c.drawString(x_left, y, "•")
        curr_y = y
        for line in lines:
            c.drawString(x_left + 10, curr_y, line)
            curr_y -= leading
        y = curr_y - 2
        
    block_2 = "If we take more than 10 days in resolving an electronic transfer inquiry, we will provisionally credit your account for the amount in question so that you will have access to the funds during the time of our investigation."
    lines = simpleSplit(block_2, b_font, b_size, text_width)
    y, page_num = check_page_break(y, len(lines)*leading + 5, page_num)
    for line in lines:
        c.drawString(x_left, y, line)
        y -= leading
        
    y -= 10
    
    # 3. Header: Errors Within...
    c.setFont(h_font, h_size)
    y, page_num = check_page_break(y, 40, page_num)
    c.drawString(x_left, y, "Errors Within Your Checking Account, Money Market Savings Account, or Savings Account")
    y -= leading
    
    c.setFont(b_font, b_size)
    block_3 = "In case of errors or questions about your electronic transfers telephone us at 1-888-842-6328, write us at the address provided above, or through Navy Federal Online Banking as soon as you can, if you think your statement or receipt is wrong or if you need more information about a transfer listed on the statement or receipt. We must hear from you no later than 60 days after we sent the FIRST statement on which the problem or error appeared."
    lines = simpleSplit(block_3, b_font, b_size, text_width)
    y, page_num = check_page_break(y, len(lines)*leading + 5, page_num)
    for line in lines:
        c.drawString(x_left, y, line)
        y -= leading
        
    bullets_4 = [
        "Tell us your name and account number (if any).",
        "Describe the error or the transfer you are unsure about, and explain as clearly as you can why you believe it is an error or why you need more information.",
        "Tell us the dollar amount of the suspected error."
    ]
    
    for b in bullets_4:
        lines = simpleSplit(b, b_font, b_size, text_width - 10)
        y, page_num = check_page_break(y, len(lines)*leading + 5, page_num)
        c.drawString(x_left, y, "•")
        curr_y = y
        for line in lines:
            c.drawString(x_left + 10, curr_y, line)
            curr_y -= leading
        y = curr_y - 2
        
    block_4 = "We will investigate your complaint and will correct any error promptly. If we take more than 10 business days to do this, we will provisionally credit your account for the amount you think is in error, so that you will have the use of the money during the time it takes us to complete our investigation."
    lines = simpleSplit(block_4, b_font, b_size, text_width)
    y, page_num = check_page_break(y, len(lines)*leading + 5, page_num)
    for line in lines:
        c.drawString(x_left, y, line)
        y -= leading
        
    y -= 10
    
    # 4. Header: Payments
    c.setFont(h_font, h_size)
    y, page_num = check_page_break(y, 40, page_num)
    c.drawString(x_left, y, "Payments")
    y -= leading
    
    c.setFont(b_font, b_size)
    block_5 = "Your check must be payable to Navy Federal Credit Union and include your Checking Line of Credit account number. Include the voucher found at the bottom of your statement and mail the enclosed envelope to: Navy Federal Credit Union, PO Box 3100, Merrifield, VA 22119-3100. Payments received by 5:00 pm Eastern Time at the mail address above will be credited the same day. Mailed payments for your Checking Line of Credit account may not be commingled with funds designated for credit to other Navy Federal Credit Union accounts."
    lines = simpleSplit(block_5, b_font, b_size, text_width)
    y, page_num = check_page_break(y, len(lines)*leading + 5, page_num)
    for line in lines:
        c.drawString(x_left, y, line)
        y -= leading
        
    return y, page_num

def format_transaction_description(tx, period_year="2026"):
    """
    Formats the transaction description based on user requirements:
    POS (Transaction Type) Debit Card 3025 MM-DD-YY Merchant/Serial
    Example: POS PURCHASE Debit Card 3025 01-02-26 PUBLIX SUPER MARKETS
    """
    original_desc = tx['description'].upper()
    amount = tx['amount']
    date_str = tx['date'] # "01/02"
    
    # Parse Date to MM-DD-YY
    try:
        mm, dd = date_str.split('/')
        # Ensure year is 2 digits
        yy = period_year[-2:] if len(period_year) == 4 else period_year
        formatted_date = f"{mm}-{dd}-{yy}"
    except:
        formatted_date = f"{date_str}-{period_year[-2:]}"

    # Logic: Only format withdrawals that look like Card purchases
    if amount >= 0:
        return original_desc 
        
    # Keywords to exclude from "POS Purchase" format
    exclude_keywords = ["DEPOSIT", "TRANSFER", "ZELLE", "DIVIDEND", "INTEREST", "ACH", "FEE"]
    if any(k in original_desc for k in exclude_keywords):
        return original_desc
        
    # ATM check
    if "ATM" in original_desc:
        clean_desc = original_desc.replace("ATM WITHDRAWAL", "").strip()
        return f"ATM WITHDRAWAL Debit Card 3025 {formatted_date} {clean_desc}"

    # Default POS Purchase
    return f"POS PURCHASE Debit Card 3025 {formatted_date} {original_desc}"

def classify_item(desc):
    """Classifies a transaction description into an item type (POS, ACH, etc.)."""
    desc = desc.upper()
    if any(x in desc for x in ["BILL", "NETFLIX", "SPOTIFY", "COMCAST", "T-MOBILE", "APPLE", "AMZN"]):
        return "ACH"
    return "POS"

def draw_persistent_header(c, width, height, data, page_num, total_pages):
    """
    Draws the persistent header seen on all pages.
    Replaces the previous Page 1 header and 'Continued' headers.
    """
    # --- Left Side ---
    # Logo Area (Image Replacement)
    # The user requested to replace the text header with a specific image.
    # Since we don't have the image file on disk yet, we check for it.
    logo_path = "EaseUS_2026_01_17_11_13_30.png" 
    
    if os.path.exists(logo_path):
        # Draw the image
        # Approximate size based on the text block it replaces:
        # Width ~ 150-180pt, Height ~ 50-60pt
        # Position: Left aligned at x=25
        # The text ended at height-67, started at height-35. 
        # So we place it around height - 75 to cover that area.
        c.drawImage(logo_path, 25, height - 80, width=170, height=60, mask='auto', preserveAspectRatio=True)
    else:
        # Fallback/Placeholder if file is missing
        # We leave the space empty or draw a placeholder box so the user knows where it goes
        c.saveState()
        c.setDash(3, 3)
        c.setStrokeColor(colors.red)
        c.rect(25, height - 80, 170, 60)
        c.setFillColor(colors.red)
        c.setFont("Helvetica", 8)
        c.drawString(30, height - 50, "MISSING: EaseUS_2026_01_17_11_13_30.png")
        c.restoreState()
    
    # Title Section (Left aligned below logo)
    if page_num > 1:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(25, height - 90, "Statement of Account")
        
        c.setFont("Helvetica", 9)
        # Get name safely
        holder = data.get('account_holder', {})
        name = holder.get('name', 'NAPOLEON KEETON').upper()
        c.drawString(25, height - 102, f"For {name}")
        
        # Address lines REMOVED for Page 2+ as per user request
        # (Previously they were here, now just Name is sufficient)
    
    # --- Right Side ---
    # Center Align relative to the right column
    # Column is roughly width-175 to width-25 (width ~150). Center ~ width-100.
    center_x = width - 85 
    
    # Page Number
    c.setFont("Helvetica", 8)
    c.drawCentredString(center_x, height - 35, f"Page {page_num} of {total_pages}")
    
    # Statement Period
    c.setFont("Helvetica", 8)
    c.drawCentredString(center_x, height - 65, "Statement Period")
    c.drawCentredString(center_x, height - 75, data.get('period', "12/10/25 - 01/09/26"))
    
    # Access Number
    access_num = data.get('account_holder', {}).get('access_number', '4026006')
    c.drawCentredString(center_x, height - 90, f"Access No. {access_num}")
    
    return height - 120 # Standard position
    
def calculate_total_pages(data):
    """
    Simulates the rendering process to calculate the total number of pages.
    """
    current_page = 2 # Start simulating from page 2 (Page 1 is fixed/known mostly)
    
    # Page 1: Header (120), Account Holder (80), Summary Table (120)
    # y starts at 792 - 320 approx for transactions on page 1?
    # No, let's look at the main code. 
    # Page 1 has header etc. The first transaction starts at `height - 320`.
    # But wait, page 1 is mostly summary. The detailed transactions start on Page 2 usually?
    # Actually, in the code:
    # `c.showPage()` happens after `draw_account_summary_table`.
    # Then `page_num = 2`.
    # Then `draw_change_of_address_form` on Page 2.
    # Then transactions start.
    
    # So effectively, Page 1 is just the summary page.
    # Transactions start on Page 2.
    
    y_start = 792 - 120
    y = y_start
    
    # Constraints
    y_limit_p2 = 230 # Change of Address form
    y_limit_pN = 50  # Standard bottom margin
    
    row_height = 12
    header_height = 20
    acc_header_height = 20
    
    accounts = data.get('accounts', [])
    
    for acc in accounts:
        # Account Header
        y -= acc_header_height
        
        # Table Header
        y -= header_height
        
        # Transactions
        for _ in acc['transactions']:
            limit = y_limit_p2 if current_page == 2 else y_limit_pN
            
            if y < limit:
                current_page += 1
                y = y_start
                y -= header_height 
                limit = y_limit_pN
            
            y -= row_height
            
        # Summary Block (Ending Balance + Avg Daily)
        y -= 45 # Approx 3-4 lines
        limit = y_limit_p2 if current_page == 2 else y_limit_pN
        if y < limit:
            current_page += 1
            y = y_start
            
        # Items Paid Section
        withdrawals = [t for t in acc['transactions'] if t['amount'] < 0]
        if withdrawals:
            y -= 30 # "Items Paid" header + Dividends text
            
            # Rows (2 items per row)
            num_rows = (len(withdrawals) + 1) // 2
            
            for _ in range(num_rows):
                limit = y_limit_p2 if current_page == 2 else y_limit_pN
                if y < limit:
                    current_page += 1
                    y = y_start
                    y -= 20 # Header for new page
                    limit = y_limit_pN
                y -= row_height
                
            y -= 20 # Spacing
            
    # Savings Section Simulation
    if 'savings_account' in data:
        sav = data['savings_account']
        
        # Check start space
        limit = y_limit_p2 if current_page == 2 else y_limit_pN
        if y < 150: # Needs decent space (Header + Table Header + 1-2 rows)
             current_page += 1
             y = y_start
             
        y -= 15 # Header "Savings"
        y -= 12 # Account Num
        y -= 15 # Joint Owner
        y -= 15 # Table Header
        
        # Rows
        # Beginning
        if sav['transactions']:
            y -= 12
            # Dividend
            if len(sav['transactions']) > 1:
                y -= 12
            # Ending Balance
            y -= 15
            # Dividend Text
            y -= 30
            
    # Tax Info Section Simulation
    limit = y_limit_p2 if current_page == 2 else y_limit_pN
    if y < 80:
         current_page += 1
         # y = y_start # Not needed for return value, but for completeness
    
    # Disclosure Section Simulation (Takes ~600 pts)
    # Almost always forces a new page if we are not at the very top
    # If y < 700 (which is basically always true after some content), new page
    if y < 650:
        current_page += 1
        y = y_start
    
    # Consume space for disclosure
    y -= 600
    if y < y_limit_pN:
        current_page += 1
            
    return current_page

def create_statement_pdf(output_path, data):
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Pre-calculate total pages
    total_pages = calculate_total_pages(data)

    # 1. Draw Background Watermark
    draw_globe_watermark(c, width, height)

    # --- Header Section ---
    draw_persistent_header(c, width, height, data, 1, total_pages)
    right_margin = width - 40
    
    # Center X for right side contact info (matching persistent header logic)
    center_x = width - 85

    # Routing Number & Contact Info (Right Side)
    y_contact_start = height - 120
    c.setFont("Helvetica", 9)
    c.drawCentredString(center_x, y_contact_start, "Routing Number: 2560-7497-4")
    
    c.setFont("Helvetica", 8)
    contact_lines = [
        "Questions about this Statement?",
        "Toll-free in the U.S. 1-888-842-6328",
        "For toll-free numbers when overseas,",
        "visit navyfederal.org/overseas/",
        "Collect internationally 1-703-255-8837"
    ]
    y_curr = y_contact_start - 20
    for line in contact_lines:
        c.drawCentredString(center_x, y_curr, line)
        y_curr -= 10
        
    # Promo Text (Right Side)
    y_curr -= 10
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(center_x, y_curr, "Say \"Yes\" to Paperless! View your")
    c.setFont("Helvetica", 8)
    c.drawCentredString(center_x, y_curr - 10, "digital statements via Mobile or")
    c.drawCentredString(center_x, y_curr - 20, "Navy Federal Online Banking.")

    # --- Address Block (Left Side) ---
    c.setFont("Courier-Bold", 9)
    y_addr = height - 120
    
    # Codes & Name Block
    # User requested format:
    # #BWNLLSV
    # #000000P4P2VPP6A3#000JMA90F KINGDOM MANDATE CENTER
    # RJ MATHEWS
    # ...
    
    holder = data.get("account_holder", {})
    name = holder.get("name", "NAPOLEON KEETON")
    addr1 = holder.get("address_line1", "870 WESTMORELAND CIR NW")
    addr2 = holder.get("address_line2", "ATLANTA GA 30318-4433")
    addr3 = holder.get("address_line3", "") # New line 3

    c.drawString(40, y_addr, "#BWNLLSV")
    y_addr -= 10
    
    # Combined Code + Name
    # Note: If the name is long, this might need splitting, but assuming it fits for now.
    combined_line = f"#000000P4P2VPP6A3#000JMA90F {name}"
    c.drawString(40, y_addr, combined_line)
    y_addr -= 10
    
    # Address Lines
    # The user wants "RJ MATHEWS" (addr1) then "909..." (addr2) then "Stockbridge..." (addr3)
    address_lines = [addr1, addr2, addr3]
    
    for line in address_lines:
        if line:
            c.drawString(40, y_addr, line)
            y_addr -= 12

    # --- Middle Promo Section ---
    y_promo = height - 260
    c.setFont("Helvetica-Bold", 9)
    c.drawString(172, y_promo, "Say \"Yes\" to Paperless Statements")
    
    c.setFont("Helvetica", 8) 
    promo_lines = [
        "If you haven't already, go paperless! You can access up to 36 months of statements anytime, anywhere.",
        "To get started, select \"Statements\" in digital banking.*",
        "It's an easy way to reduce the risk of identity theft and cut down on paper clutter.",
        "Insured by NCUA. *Message and data rates may apply. Visit navyfederal.org for more information."
    ]
    y_promo -= 12
    for line in promo_lines:
        c.drawString(172, y_promo, line)
        y_promo -= 10

    # --- Summary of Deposits Table ---
    y_table_header = height - 360 
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25, y_table_header + 20, "Summary of your deposit accounts")
    
    # Table Grid
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.black)
    
    table_left = 25
    table_right = width - 40
    
    # Vertical line x-coords
    v_lines = [
        # table_left,      # Left border - REMOVED
        # 170,             # After Account Info - REMOVED
        # 250,             # After Prev Balance - REMOVED
        # 350,             # After Deposits - REMOVED
        # 450,             # After Withdrawals - REMOVED
        520,             # After Ending Balance - KEPT (Before YTD)
        # table_right      # Right border - REMOVED
    ]
    
    # Header Bottom Line (Separator between headers and data)
    c.line(table_left, y_table_header - 25, table_right, y_table_header - 25)
    
    # Column Headers
    c.setFont("Helvetica-Bold", 7)
    
    # Previous Balance
    c.drawCentredString(210, y_table_header - 10, "Previous")
    c.drawCentredString(210, y_table_header - 20, "Balance")
    
    # Deposits/Credits
    c.drawCentredString(300, y_table_header - 10, "Deposits/")
    c.drawCentredString(300, y_table_header - 20, "Credits")
    
    # Withdrawals/Debits
    c.drawCentredString(400, y_table_header - 10, "Withdrawals/")
    c.drawCentredString(400, y_table_header - 20, "Debits")
    
    # Ending Balance
    c.drawCentredString(485, y_table_header - 10, "Ending")
    c.drawCentredString(485, y_table_header - 20, "Balance")
    
    # YTD Dividends
    c.drawCentredString(546, y_table_header - 10, "YTD")
    c.drawCentredString(546, y_table_header - 20, "Dividends")

    # Table Data & Form Fields
    y_row = y_table_header - 40
    row_height = 35 
    
    # Calculate Table Bottom based on rows
    num_rows = len(data['accounts']) + 1 # +1 for Totals
    table_bottom_y = y_table_header - 25 - (num_rows * row_height)
    
    # Draw Vertical Lines ONLY for the data section, not the header
    for vx in v_lines:
        c.line(vx, y_table_header - 25, vx, table_bottom_y)

    # Field positions (centered in columns)
    col_x_positions = [210, 300, 400, 485, 546]
    
    # Accounts
    for idx, acc in enumerate(data['accounts']):
        # Account Name/Number (Left Aligned in Col 1)
        # Col 1 is 25 to 170
        c.setFont("Helvetica-Bold", 9)
        c.drawString(30, y_row + 5, acc['type']) # Adjusted Y for taller row
        c.setFont("Helvetica", 9)
        c.drawString(30, y_row - 10, acc['account_number'])
        
        # Values as Text
        field_keys = ['previous_balance', 'deposits_credits', 'withdrawals_debits', 'ending_balance', 'ytd_dividends']
        
        for i, key in enumerate(field_keys):
            val = f"${acc[key]:,.2f}"
            x_pos = col_x_positions[i]
            c.drawCentredString(x_pos, y_row - 8, val)
        
        c.setStrokeColor(colors.lightgrey)
        c.line(table_left, y_row - 20, table_right, y_row - 20) # Row separator inside
        y_row -= row_height

    # Totals Row
    c.setStrokeColor(colors.black)
    c.line(table_left, y_row + row_height - 20, table_right, y_row + row_height - 20) # Ensure line above totals is black/solid if needed
    
    # Bottom Align Totals
    # Row bottom is approx y_row - 20.
    # We draw text close to that.
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y_row - 12, "Totals")
    
    # Calculate totals automatically from accounts
    totals = {
        'previous_balance': sum(acc['previous_balance'] for acc in data['accounts']),
        'deposits_credits': sum(acc['deposits_credits'] for acc in data['accounts']),
        'withdrawals_debits': sum(acc['withdrawals_debits'] for acc in data['accounts']),
        'ending_balance': sum(acc['ending_balance'] for acc in data['accounts']),
        'ytd_dividends': sum(acc['ytd_dividends'] for acc in data['accounts'])
    }
    
    field_keys = ['previous_balance', 'deposits_credits', 'withdrawals_debits', 'ending_balance', 'ytd_dividends']
    for i, key in enumerate(field_keys):
        val = f"${totals[key]:,.2f}"
        x_pos = col_x_positions[i]
        c.drawCentredString(x_pos, y_row - 12, val)
        
    # Draw bottom border of the table
    c.setStrokeColor(colors.black)
    c.line(table_left, table_bottom_y, table_right, table_bottom_y)

    # ==========================================
    # DEPOSIT VOUCHER SECTION (Moved to Page 1)
    # ==========================================
    y_voucher = 220 
    
    # Dotted Line (Perforated effect)
    c.setDash(1, 2)
    c.setStrokeColor(colors.black)
    c.line(0, y_voucher + 60, width, y_voucher + 60)
    c.setDash([]) 
    
    # Left Side Voucher Info
    c.setFont("Helvetica", 9)
    
    # Use dynamic data for Voucher
    holder = data.get("account_holder", {})
    voucher_name = holder.get("name", "NAPOLEON KEETON")
    access_num = holder.get("access_number", "4026006") # Default from previous code
    
    # Centered above address? No, left aligned as per image
    c.drawString(110, y_voucher + 25, voucher_name)
    
    # Address Lines REMOVED as per user request
    c.setFont("Helvetica", 9)
    c.drawString(165, y_voucher + 5, access_num)
    
    # Checkbox Area
    c.setFont("Helvetica", 6)
    # Moved down ~0.5 inch (36 points)
    y_checkbox_base = y_voucher - 36
    c.drawString(45, y_checkbox_base + 15, "MARK \"X\" TO CHANGE")
    c.drawString(45, y_checkbox_base + 8, "ADDRESS/ORDER")
    c.drawString(45, y_checkbox_base + 1, "ITEMS ON REVERSE")
    
    # Arrow
    p = c.beginPath()
    p.moveTo(130, y_checkbox_base + 10)
    p.lineTo(135, y_checkbox_base + 15)
    p.lineTo(130, y_checkbox_base + 20)
    c.drawPath(p, stroke=1, fill=1)
    
    # Box
    c.rect(170, y_checkbox_base + 5, 15, 15, stroke=1, fill=0)
    
    # Right Side Voucher Headers
    c.setFont("Helvetica-Bold", 10)
    # "DEPOSIT VOUCHER" title
    c.drawRightString(width - 40, y_voucher + 25, "DEPOSIT VOUCHER") # Aligned right
    
    c.setFont("Helvetica", 5)
    c.drawRightString(width - 40, y_voucher + 15, "(FOR MAIL USE ONLY. DO NOT SEND CASH THROUGH THE MAIL.")
    c.drawRightString(width - 40, y_voucher + 8, "DEPOSITS MAY NOT BE AVAILABLE FOR IMMEDIATE WITHDRAWAL)")

    # Voucher Table
    v_table_y = y_voucher - 5
    
    # Header Background
    c.setFillColor(colors.lightgrey)
    # Extends from x=360 to x=590 (Extended width for cents column)
    # Width = 590 - 360 = 230
    c.rect(360, v_table_y, 230, 12, fill=1, stroke=1) 
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 6)
    
    # Headers - Centered in their columns
    # Col 1: Account Number (360 - 450) -> Center 405
    # Col 2: Account Type (450 - 520) -> Center 485
    # Col 3: Amount Enclosed (520 - 590) -> Center 555
    
    c.drawCentredString(405, v_table_y + 3, "ACCOUNT NUMBER")
    c.drawCentredString(485, v_table_y + 3, "ACCOUNT TYPE")
    c.drawCentredString(555, v_table_y + 3, "AMOUNT ENCLOSED")
    
    # Table Grid
    # Height: 5 rows * 15 + Total row
    row_h = 15
    table_height = 5 * row_h
    table_bottom = v_table_y - table_height
    
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    
    # Outer Box (Data part)
    c.rect(360, table_bottom, 230, table_height) 
    
    # Vertical Lines
    # x=450 (Acc Num | Type)
    c.line(450, table_bottom, 450, v_table_y + 12) 
    # x=520 (Type | Amount)
    c.line(520, table_bottom, 520, v_table_y + 12)
    # x=565 (Cents column split - starts at 's' in enclosed)
    c.line(565, table_bottom, 565, v_table_y + 12)
    
    # Horizontal Rows
    current_y = v_table_y
    for i in range(5):
        c.line(360, current_y, 590, current_y)
        
        # Pre-filled data for first 2 rows
        if i == 0:
            c.setFont("Helvetica", 8)
            c.drawString(365, current_y - 11, "7123566726")
            c.drawString(455, current_y - 11, "Checking")
        elif i == 1:
            c.setFont("Helvetica", 8)
            c.drawString(365, current_y - 11, "3148913266")
            c.drawString(455, current_y - 11, "Savings")
            
        current_y -= row_h

    # "TOTAL" row at bottom
    total_y = table_bottom - 15
    # Amount box (Dollars + Cents)
    c.rect(520, total_y, 70, 15) # 520 to 590
    c.line(565, total_y, 565, total_y + 15) # Split total box too
    
    # Label box
    c.rect(450, total_y, 70, 15) 
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(485, total_y + 4, "TOTAL")

    # Bottom Address
    c.setFont("Helvetica", 9)
    c.drawString(80, 80, "NFCU")
    c.drawString(80, 68, "PO BOX 3100")
    c.drawString(80, 56, "MERRIFIELD VA 22119-3100")
    
    # Bottom OCR
    c.setFont("Courier", 10)
    # OCR likely off page, but user said move everything.
    c.drawString(40, 30, "405712356672631489132660000000000000000000000000000000007")

    # --- Page Break for Detailed Transactions ---
    c.showPage()
    
    # --- Page 2 Setup ---
    page_num = 2
    
    # Re-draw watermark and simple header
    draw_globe_watermark(c, width, height)
    
    # Persistent Header for Page 2
    draw_persistent_header(c, width, height, data, page_num, total_pages) 

    # Draw Change of Address Form on Page 2
    draw_change_of_address_form(c, width, 40)

    # --- Detailed Transactions Section ---
    y_trans = height - 120
    
    # Iterate through accounts to show transactions
    # Determine Period Year for formatting
    try:
        p_end = data.get('period', '').split('-')[1].strip() # "01/09/26"
        p_year = p_end.split('/')[-1] # "26"
        if len(p_year) == 2: p_year = "20" + p_year
    except:
        p_year = "2026"

    for acc in data['accounts']:
        if 'transactions' in acc and acc['transactions']:
            # Check if we need a page break (Account Header check)
            limit = 230 if page_num == 2 else 50
            if y_trans < limit: 
                c.showPage()
                page_num += 1
                # Re-draw watermark and header
                draw_globe_watermark(c, width, height)
                y_trans = draw_persistent_header(c, width, height, data, page_num, total_pages)

            # Account Header
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(NAVY_BLUE)
            c.drawString(25, y_trans, f"{acc['type']} - {acc['account_number']}")
            c.setFillColor(colors.black)
            
            y_trans -= 15
            
            # Transaction Table Headers
            c.setFont("Helvetica-Bold", 8)
            c.drawString(25, y_trans, "Date")
            c.drawString(65, y_trans, "Description")
            c.drawRightString(480, y_trans, "Amount")
            c.drawRightString(580, y_trans, "Balance")
            
            # Header Line
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.line(25, y_trans - 5, width - 25, y_trans - 5)
            
            y_trans -= 15
            
            # Transactions
            c.setFont("Helvetica", 8)
            for tx in acc['transactions']:
                limit = 230 if page_num == 2 else 50
                if y_trans < limit: # Page break inside transactions
                     c.showPage()
                     page_num += 1
                     draw_globe_watermark(c, width, height)
                     y_trans = draw_persistent_header(c, width, height, data, page_num, total_pages)
                     
                     # Re-draw column headers on new page
                     c.setFont("Helvetica-Bold", 8)
                     c.drawString(25, y_trans, "Date")
                     c.drawString(65, y_trans, "Description")
                     c.drawRightString(480, y_trans, "Amount")
                     c.drawRightString(580, y_trans, "Balance")
                     c.line(25, y_trans - 5, width - 25, y_trans - 5)
                     y_trans -= 15
                     
                     c.setFont("Helvetica", 8) # Reset font for data
                
                c.drawString(25, y_trans, tx['date'])
                # Use new formatting function
                desc_text = format_transaction_description(tx, p_year)
                c.drawString(65, y_trans, desc_text)
                
                # Format Amount
                amt = tx['amount']
                amt_str = f"{amt:,.2f}" if amt >= 0 else f"{amt:,.2f}"
                c.drawRightString(480, y_trans, amt_str)
                
                # Format Balance
                bal = tx['balance']
                bal_str = f"${bal:,.2f}"
                c.drawRightString(580, y_trans, bal_str)
                
                y_trans -= 12
            
            # Draw Ending Balance Row
            
            # Check for page break before summary
            limit = 230 if page_num == 2 else 50
            if y_trans < limit:
                 c.showPage()
                 page_num += 1
                 draw_globe_watermark(c, width, height)
                 y_trans = draw_persistent_header(c, width, height, data, page_num, total_pages)
                 # Re-draw column headers
                 c.setFont("Helvetica-Bold", 8)
                 c.drawString(25, y_trans, "Date")
                 c.drawString(65, y_trans, "Description")
                 c.drawRightString(480, y_trans, "Amount")
                 c.drawRightString(580, y_trans, "Balance")
                 c.line(25, y_trans - 5, width - 25, y_trans - 5)
                 y_trans -= 15
            
            y_trans -= 5
            
            # Ending Balance Row
            c.setFont("Helvetica-Bold", 8)
            
            # Use period end date (e.g., from '01/01/26' to '01/31/26', take '01-31')
            # Parse period string "01/01/26 - 01/31/26"
            try:
                end_date_str = data['period'].split('-')[1].strip() # "01/31/26"
                end_date_parts = end_date_str.split('/') # ["01", "31", "26"]
                formatted_end_date = f"{end_date_parts[0]}-{end_date_parts[1]}" # "01-31"
            except:
                formatted_end_date = "01-31" # Fallback
            
            c.drawString(25, y_trans, formatted_end_date)
            c.drawString(65, y_trans, "Ending Balance")
            
            # Final Balance
            end_bal = acc['transactions'][-1]['balance'] if acc['transactions'] else 0.0
            c.drawRightString(580, y_trans, f"{end_bal:,.2f}")
            
            y_trans -= 15
            
            # Average Daily Balance Row
            # Calculate Average Daily Balance
            # Start Balance: acc['previous_balance']
            # We need to simulate daily balances for 31 days
            # Simplified Logic: 
            # 1. Map transactions to days
            # 2. Iterate 1 to 31
            # 3. Update balance
            # 4. Sum up
            
            prev_bal = acc.get('previous_balance', 0.0)
            daily_balances = []
            current_sim_bal = prev_bal
            
            # Create a dict of transactions by day
            tx_by_day = {}
            for tx in acc['transactions']:
                # tx['date'] is "01/05"
                day_key = int(tx['date'].split('/')[1])
                if day_key not in tx_by_day:
                    tx_by_day[day_key] = []
                tx_by_day[day_key].append(tx['amount'])
                
            # Iterate days 1 to 31 (Jan)
            for day in range(1, 32):
                if day in tx_by_day:
                    current_sim_bal += sum(tx_by_day[day])
                daily_balances.append(current_sim_bal)
            
            avg_daily_bal = sum(daily_balances) / len(daily_balances)
            
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(25, y_trans, f"Average Daily Balance - Current Cycle: ${avg_daily_bal:,.2f}")
            
            y_trans -= 15
            
            # --- Dividend / Items Paid Section ---
            
            # Dividend Text
            c.setFont("Helvetica-Oblique", 8)
            # Use data['period'] to get years/dates
            try:
                p_start, p_end = data['period'].split('-')
                p_start = p_start.strip().replace('/', '-')
                p_end = p_end.strip().replace('/', '-')
                # Assume year is in the string, or fix it to 2026 as per user data
                if len(p_start.split('-')) == 2: # MM-DD format
                   p_start = p_start + "-2026"
                   p_end = p_end + "-2026"
            except:
                p_start, p_end = "01-01-2026", "01-31-2026"
                
            c.drawString(25, y_trans, f"Your account earned $0.29, with an annual percentage yield earned of 0.05%, for the dividend period from {p_start} through {p_end}")
            
            y_trans -= 20
            
            # Items Paid Section
            withdrawals = [t for t in acc['transactions'] if t['amount'] < 0]
            if withdrawals:
                # Check page break for header
                limit = 230 if page_num == 2 else 50
                if y_trans < limit:
                     c.showPage()
                     page_num += 1
                     draw_globe_watermark(c, width, height)
                     y_trans = draw_persistent_header(c, width, height, data, page_num, total_pages)
                
                c.setFont("Helvetica-Bold", 10)
                c.drawString(25, y_trans, "Items Paid")
                y_trans -= 15
                
                # Column Headers
                c.setFont("Helvetica-Bold", 8)
                # Left Column
                c.drawString(25, y_trans, "Date")
                c.drawCentredString(140, y_trans, "Item")
                c.drawRightString(280, y_trans, "Amount($)")
                # Right Column
                c.drawString(330, y_trans, "Date")
                c.drawCentredString(445, y_trans, "Item")
                c.drawRightString(585, y_trans, "Amount($)")
                
                c.setStrokeColor(colors.black)
                c.setLineWidth(0.5)
                c.line(25, y_trans - 3, 280, y_trans - 3)
                c.line(330, y_trans - 3, 585, y_trans - 3)
                
                y_trans -= 12
                
                # Draw Items
                c.setFont("Helvetica", 8)
                num_items = len(withdrawals)
                # We fill Left then Right for each row? Or Down then Right?
                # Image looks like dense packing. 
                # Let's do Row by Row: Item 0 -> Left, Item 1 -> Right
                
                for i in range(0, num_items, 2):
                    # Check page break
                    limit = 230 if page_num == 2 else 50
                    if y_trans < limit:
                         c.showPage()
                         page_num += 1
                         draw_globe_watermark(c, width, height)
                         y_trans = draw_persistent_header(c, width, height, data, page_num, total_pages)
                         
                         # Redraw Headers on new page
                         c.setFont("Helvetica-Bold", 8)
                         c.drawString(25, y_trans, "Date")
                         c.drawCentredString(140, y_trans, "Item")
                         c.drawRightString(280, y_trans, "Amount($)")
                         c.drawString(330, y_trans, "Date")
                         c.drawCentredString(445, y_trans, "Item")
                         c.drawRightString(585, y_trans, "Amount($)")
                         c.line(25, y_trans - 3, 280, y_trans - 3)
                         c.line(330, y_trans - 3, 585, y_trans - 3)
                         y_trans -= 12
                         c.setFont("Helvetica", 8)

                    # Left Item
                    item_l = withdrawals[i]
                    date_l = item_l['date'].replace('/', '-')
                    desc_l = classify_item(item_l['description'])
                    amt_l = abs(item_l['amount'])
                    
                    c.drawString(25, y_trans, date_l)
                    c.drawCentredString(140, y_trans, desc_l)
                    c.drawRightString(280, y_trans, f"{amt_l:,.2f}")
                    
                    # Right Item
                    if i + 1 < num_items:
                        item_r = withdrawals[i+1]
                        date_r = item_r['date'].replace('/', '-')
                        desc_r = classify_item(item_r['description'])
                        amt_r = abs(item_r['amount'])
                        
                        c.drawString(330, y_trans, date_r)
                        c.drawCentredString(445, y_trans, desc_r)
                        c.drawRightString(585, y_trans, f"{amt_r:,.2f}")
                    
                    y_trans -= 10
            
            y_trans -= 20 # Spacing between accounts

    # --- Savings Section ---
    if 'savings_account' in data:
        sav = data['savings_account']
        
        # Check page break
        limit = 230 if page_num == 2 else 50
        if y_trans < 150: # Needs decent space
             c.showPage()
             page_num += 1
             draw_globe_watermark(c, width, height)
             y_trans = draw_persistent_header(c, width, height, data, page_num, total_pages)
        
        # Header
        c.setFont("Helvetica-Bold", 10)
        c.drawString(25, y_trans, "Savings")
        y_trans -= 15
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(25, y_trans, f"{sav['type']} - {sav['account_number']}")
        y_trans -= 12
        
        c.setFont("Helvetica", 9)
        c.drawString(25, y_trans, "Joint Owner(s): NONE")
        y_trans -= 15
        
        # Table Headers
        c.setFont("Helvetica-Bold", 8)
        c.drawString(25, y_trans, "Date")
        c.drawString(65, y_trans, "Transaction Detail")
        c.drawRightString(480, y_trans, "Amount($)")
        c.drawRightString(580, y_trans, "Balance($)")
        
        c.setStrokeColor(colors.black)
        c.setLineWidth(1) # Thick line
        c.line(25, y_trans - 5, width - 25, y_trans - 5)
        y_trans -= 15
        
        # Rows
        c.setFont("Helvetica", 8)
        
        # 1. Beginning Balance (Hardcoded logic based on image/json)
        # Using the first transaction as beginning usually
        if sav['transactions']:
            # Beginning
            tx0 = sav['transactions'][0]
            c.drawString(25, y_trans, tx0['date'].replace('/', '-'))
            c.drawString(65, y_trans, tx0['description'])
            c.drawRightString(580, y_trans, f"{tx0['balance']:.2f}")
            y_trans -= 12
            
            # Dividend
            if len(sav['transactions']) > 1:
                tx1 = sav['transactions'][1]
                c.drawString(25, y_trans, tx1['date'].replace('/', '-'))
                c.drawString(65, y_trans, tx1['description'])
                c.drawRightString(480, y_trans, f"{tx1['amount']:.2f}")
                c.drawRightString(580, y_trans, f"{tx1['balance']:.2f}")
                y_trans -= 12
                
            # Ending Balance Row
            c.setFont("Helvetica-Bold", 8)
            # Use period end date
            try:
                end_date_str = data['period'].split('-')[1].strip()
                end_date_parts = end_date_str.split('/')
                fmt_end_date = f"{end_date_parts[0]}-{end_date_parts[1]}"
            except:
                fmt_end_date = "01-31"
                
            c.drawString(25, y_trans, fmt_end_date)
            c.drawString(65, y_trans, "Ending Balance")
            c.drawRightString(580, y_trans, f"{sav['ending_balance']:.2f}")
            y_trans -= 15
            
            # Dividend Text
            c.setFont("Helvetica-Oblique", 8)
            # Use data['period'] to get years/dates
            try:
                p_start, p_end = data['period'].split('-')
                p_start = p_start.strip().replace('/', '-')
                p_end = p_end.strip().replace('/', '-')
                if len(p_start.split('-')) == 2:
                    p_start = p_start + "-2026"
                    p_end = p_end + "-2026"
            except:
                 p_start, p_end = "01-01-2026", "01-31-2026"
                 
            c.drawString(25, y_trans, f"Your account earned ${sav['dividends']:.2f}, with an annual percentage yield earned of 0.24%, for the dividend period from {p_start} through {p_end}")
            y_trans -= 30

    # --- Tax Information Section ---
    
    # Check page break
    limit = 230 if page_num == 2 else 50
    if y_trans < 80:
         c.showPage()
         page_num += 1
         draw_globe_watermark(c, width, height)
         y_trans = draw_persistent_header(c, width, height, data, page_num, total_pages)

    # Header with borders
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(25, y_trans + 10, width - 25, y_trans + 10) # Top Line
    
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width/2, y_trans, "2026 Year to Date Federal Income Tax Information")
    
    c.line(25, y_trans - 5, width - 25, y_trans - 5) # Bottom Line
    y_trans -= 20
    
    # Tax Data
    c.setFont("Helvetica", 8)
    
    # Left Side: Dividends
    chk_div = data['accounts'][0].get('ytd_dividends', 0.0)
    sav_div = data.get('savings_account', {}).get('ytd_dividends', 0.0)
    
    c.drawString(25, y_trans, "SAVINGS DIVIDENDS")
    c.drawString(200, y_trans, f"{sav_div:.2f}")
    y_trans -= 12
    
    c.drawString(25, y_trans, "CHECKING DIVIDENDS")
    c.drawString(200, y_trans, f"{chk_div:.2f}")
    
    # Right Side: Finance Charge (Same line as Checking Div)
    c.drawString(300, y_trans, "FINANCE CHARGE CHECKING LOC")
    c.drawRightString(580, y_trans, "0.00")
    
    y_trans -= 20
    
    # --- Disclosure Section ---
    y_trans, page_num = draw_disclosure_section(c, width, height, y_trans, page_num, total_pages, data)
    
    c.save()

    # Post-process to add calculations - REMOVED per request
    # temp_filename = output_path
    # final_filename = "calculated_" + output_path
    # add_calculations_to_pdf(temp_filename, final_filename, data)
    
    # Rename
    # import os
    # os.remove(temp_filename)
    # os.rename(final_filename, output_path)

if __name__ == "__main__":
    # Load data from JSON
    import json
    with open('statement_data.json', 'r') as f:
        data = json.load(f)
        
    output_pdf = "january_2026_statement_v3.pdf"
    create_statement_pdf(output_pdf, data)
    print(f"PDF generated with calculations: {output_pdf}")
