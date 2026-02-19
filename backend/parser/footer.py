#parser/footer.py
def extract_footer(lines):
    footer_data = {}
    keywords = ["requested", "approved", "authorized"]
    
    for i, line in enumerate(lines):
        line_text = " ".join(w["text"] for w in line).lower()
        
        for key in keywords:
            if key in line_text:
                # 1. Capture the current line
                current_val = " ".join(w["text"] for w in line)
                
                # 2. Lookahead: Check the next line for the actual name/signature
                # This handles cases where the name is below the label
                next_val = ""
                if i + 1 < len(lines):
                    next_val = " ".join(w["text"] for w in lines[i+1])
                
                footer_data[key] = f"{current_val} | Follow-up: {next_val}"
                
    return footer_data