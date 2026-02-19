import os
import sys
from pathlib import Path

# OCR & Parsing Imports
from ocr.preprocess import preprocess_image
from ocr.tesseract_ocr import extract_ocr_data
from ocr.layout import group_words_into_lines
from parser.header import detect_table_header
from parser.table import parse_table, parse_implicit_table
from parser.footer import extract_footer
from output.excel_writer import write_excel
from review.invoice_review import evaluate_invoice

# Logic & Memory Imports (Commented out until fully implemented)
# from parser.review import assign_review_status 
# from memory.corrections import load_memory, apply_known_fixes

# --- PATH CONFIGURATION ---
# Internal storage for the engine before the worker moves files to tenant folders
TEMP_PROCESSING_DIR = Path("runtime/temp_processing")
TEMP_PROCESSING_DIR.mkdir(parents=True, exist_ok=True)

def run_pipeline(image_path, tenant_id="default_tenant"):
    """
    The Core Engine: Processes a single image and returns metadata + temp file path.
    Designed to be called by jobs/worker.py.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")

    print(f"--- ⚙️ Processing: {image_path.name} (Tenant: {tenant_id}) ---")

    # 1-3. OCR Steps
    image = preprocess_image(str(image_path))
    ocr_data = extract_ocr_data(image)
    lines = group_words_into_lines(ocr_data)

    # 4. Table Parsing
    header_index, header_line = detect_table_header(lines)
    rows = parse_table(lines, header_index, header_line) if header_index else parse_implicit_table(lines)

    if not rows:
        print(f"❌ Failed: No rows found in {image_path.name}")
        # Return a failure tuple so the worker can update DB status to FAILED
        return "FAILED", "Unknown-Company", None

    # 5. Header & Footer extraction
    invoice_header = [] # Placeholder for your header extraction logic
    footer = extract_footer(lines)
    
    # 🟢 ALIGNMENT FIX: Extract Company Name safely
    company_name = invoice_header[0] if invoice_header else "Unknown-Company"

    # 6. Audit & Review Logic
    # evaluate_invoice returns (status, reasons) e.g., ("OK", []) or ("FLAGGED", ["Total Mismatch"])
    invoice_status, review_reasons = evaluate_invoice(rows, footer)

    # 7. Generate Temporary Output
    # The worker will handle renaming and moving this to the final tenant destination
    excel_name = f"{image_path.stem}_temp.xlsx"
    temp_final_path = TEMP_PROCESSING_DIR / excel_name

    write_excel(
        invoice_header, 
        rows, 
        footer, 
        str(temp_final_path), 
        invoice_status=invoice_status, 
        review_reasons=review_reasons,  
        tenant_id=tenant_id
    )
    
    print(f"✅ Generated Temp Excel: {temp_final_path} | Status: {invoice_status}")

    # 🟢 RETURN FOR WORKER: Return exactly what jobs/worker.py expects to unpack
    return invoice_status, company_name, str(temp_final_path)

if __name__ == "__main__":
    # Manual debugging mode
    # Usage: python main.py uploads/my_invoice.jpg
    if len(sys.argv) > 1:
        run_pipeline(sys.argv[1])
    else:
        print("Usage: python main.py <path_to_image>")