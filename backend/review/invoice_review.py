#review/invoice_review
import re

def evaluate_invoice(rows, footer):
    reasons = []
    if not rows:
        reasons.append("No rows extracted")
        return "NEEDS_REVIEW", reasons

    calculated_total = 0
    
    for idx, row in enumerate(rows, start=1):
        # 1. Missing fields check
        for field in ["Name", "Service", "Amount"]:
            if not row.get(field):
                reasons.append(f"Row {idx}: Missing {field}")

        # 2. Status check (using your parser/review.py labels)
        status = row.get("Review_Status")
        if status in ["CHECK_OCR", "CHECK_AMOUNT"]:
            reasons.append(f"Row {idx}: Flagged as {status}")

        # 3. Summing for total check
        try:
            amt_str = str(row.get("Amount", "0")).replace(",", "").strip()
            calculated_total += float(amt_str)
        except:
            pass # Invalid amounts are already caught by Review_Status

    # --- THE TOTAL MATCH CHECK ---
    # Look for "Total" in the footer keys
    printed_total_str = footer.get("Total") or footer.get("TOTAL") or "0"
    try:
        # Clean the printed total (e.g., "RWF 50,000" -> 50000)
        printed_total = float(re.sub(r"[^\d.]", "", str(printed_total_str)))
        
        if abs(calculated_total - printed_total) > 0.01:
            reasons.append(f"Math Mismatch: Rows sum to {calculated_total}, but Invoice says {printed_total}")
    except:
        reasons.append("Could not verify Total: Printed total is not a valid number")

    invoice_status = "NEEDS_REVIEW" if reasons else "OK"
    return invoice_status, reasons