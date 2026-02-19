#batch_process.py
import csv
from datetime import datetime
from pathlib import Path
from main import run_pipeline

# Configuration
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("runtime/processed_originals")
REPORT_DIR = Path("runtime/reports")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

def process_batch():
    # Ensure folders exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Create a unique filename for today's report
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = REPORT_DIR / f"batch_report_{timestamp}.csv"

    # 1. Open CSV for writing
    with open(report_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        # Write Header
        writer.writerow(["Timestamp", "File Name", "Status", "Reasons"])

        # 2. Loop through files
        files = [f for f in UPLOAD_DIR.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS]
        
        if not files:
            print("No files found in uploads.")
            return

        for file in files:
            try:
                # Call main.py and get the status/reasons back
                status, reasons = run_pipeline(file)

                # 3. Log to CSV
                reason_string = " | ".join(reasons) if reasons else "None"
                writer.writerow([datetime.now().isoformat(), file.name, status, reason_string])

                # 4. Move original image to 'processed' so uploads stays empty
                file.rename(PROCESSED_DIR / file.name)
                print(f"✅ Logged and moved {file.name}")

            except Exception as e:
                print(f"❌ Error on {file.name}: {e}")
                writer.writerow([datetime.now().isoformat(), file.name, "ERROR", str(e)])

    print(f"\n--- Batch Finished. Report saved to {report_path} ---")

if __name__ == "__main__":
    process_batch()