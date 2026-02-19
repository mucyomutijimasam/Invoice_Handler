#parser/header.py
def detect_table_header(lines):
    # Define groups of synonyms for your required columns
    expected_headers = [
        ["name", "client", "customer"],
        ["service", "description", "item", "product"],
        ["amount", "price", "total", "cost"],
        ["telephone", "phone", "tel"], # Added this
        ["sign", "signature"]           # Added this
    ]

    for idx, line in enumerate(lines):
        # Join all text in the line to search within it
        full_line_text = " ".join([w["text"].lower() for w in line])
        
        matches = 0
        for synonyms in expected_headers:
            # Check if ANY of the synonyms for a column appear in this line
            if any(syn in full_line_text for syn in synonyms):
                matches += 1
        
        # If we found at least 2 or 3 of our columns, this is likely the header
        if matches >= 2: 
            return idx, line
            
    return None, None