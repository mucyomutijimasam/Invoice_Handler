import re
from parser.review import assign_review_status
from memory.corrections import load_memory, apply_known_fixes
from tenants.manager import get_tenant_paths

def is_amount(token):
    """Clean amount detection using regex to handle currency and separators."""
    clean = re.sub(r'[^\d.]', '', token)
    try:
        float(clean)
        return True
    except ValueError:
        return False

def near(x1, x2, tolerance=40):
    """Checks if two horizontal coordinates are within a specific proximity."""
    if x1 is None or x2 is None: return False
    return abs(x1 - x2) <= tolerance

def parse_table(lines, header_index, header_line, tenant_id="default_tenant"):
    """
    Parses structured tables using identified headers and tenant-specific memory.
    """
    # 1. LOAD TENANT-SPECIFIC MEMORY
    paths = get_tenant_paths(tenant_id)
    memory = load_memory(paths["memory"])
    
    columns = {}
    synonyms = {
        "name": ["client", "customer", "name", "patient"], 
        "service": ["description", "item", "product", "service", "details"], 
        "amount": ["price", "total", "cost", "amount", "charge"]
    }
    
    # Map header text to canonical keys based on horizontal position (x)
    for word in header_line:
        text = word["text"].lower()
        found_key = text
        for key, aliases in synonyms.items():
            if text in aliases:
                found_key = key
        columns[found_key] = word["x"]

    rows = []
    for line in lines[header_index + 1:]:
        full_line_text = " ".join([w["text"] for w in line]).lower()
        
        # 🟢 STOP LOGIC: Prevent parsing totals/tax as line items
        if any(kw in full_line_text for kw in ["total", "subtotal", "tax", "amount due"]): 
            break

        row_data = {"name": [], "service": [], "amount": []}
        for word in line:
            x_pos = word["x"]
            if near(x_pos, columns.get("name")):
                row_data["name"].append(word["text"])
            elif near(x_pos, columns.get("service")):
                row_data["service"].append(word["text"])
            elif near(x_pos, columns.get("amount")):
                row_data["amount"].append(word["text"])

        # Capture raw strings for comparison to detect AI modifications
        raw_name = " ".join(row_data["name"]).strip()
        raw_service = " ".join(row_data["service"]).strip()
        raw_amount = " ".join(row_data["amount"]).strip()

        if not any([raw_name, raw_service, raw_amount]):
            continue

        row = {
            "Name": raw_name,
            "Telephone": "", 
            "Service": raw_service,
            "Amount": raw_amount
        }
        
        # --- APPLY AI FIXES ---
        row = apply_known_fixes(row, memory)
        
        # --- FLAG AUTO-CORRECTIONS ---
        # Mark as 'AUTO_FIXED' if memory changed any value
        if row["Name"] != raw_name or row["Service"] != raw_service or row["Amount"] != raw_amount:
            row["Review_Status"] = "AUTO_FIXED"
        else:
            row["Review_Status"] = assign_review_status(row)
            
        rows.append(row)
    return rows

def parse_implicit_table(lines, tenant_id="default_tenant"):
    """
    Parses tables without clear headers by identifying amount-like tokens.
    """
    paths = get_tenant_paths(tenant_id)
    memory = load_memory(paths["memory"])
    rows = []

    for line in lines:
        words = [w["text"] for w in line if w["text"].strip()]
        if not words: continue

        full_text = " ".join(words).lower()
        if "total" in full_text:
            rows.append({
                "Name": "TOTAL", "Telephone": "", "Service": "", 
                "Amount": " ".join(words), "Review_Status": "CHECK_TOTAL"
            })
            break

        amount = None
        # Look for the price/amount usually on the far right of the line
        for token in reversed(words):
            if is_amount(token):
                amount = token
                break

        if amount is None: continue

        raw_name = words[0]
        amount_index = words.index(amount)
        raw_service = " ".join(words[1:amount_index])

        row = {
            "Name": raw_name,
            "Telephone": "",
            "Service": raw_service,
            "Amount": amount
        }

        # --- APPLY AI FIXES ---
        row = apply_known_fixes(row, memory)

        # --- FLAG AUTO-CORRECTIONS ---
        if row["Name"] != raw_name or row["Service"] != raw_service or row["Amount"] != amount:
            row["Review_Status"] = "AUTO_FIXED"
        else:
            row["Review_Status"] = assign_review_status(row)
        
        rows.append(row)

    return rows 