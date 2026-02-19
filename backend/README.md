📑 Intelligent Invoice Audit & Learning System
🎯 Project Overview

This system is an automated OCR (Optical Character Recognition) Pipeline designed to digitize, audit, and learn from invoice data. Unlike static OCR tools, this platform features a Supervised Learning Feedback Loop; it captures human corrections to handle messy text, inconsistent layouts, and low-quality scans more accurately over time.
🏗 Modular Architecture

The system is built on a modular "decoupled" architecture. This ensures that the OCR engine, the data parser, and the memory brain can be updated independently without breaking the entire system.

    ocr/: Handles image preprocessing (OpenCV) and text extraction (Tesseract).

    parser/: Logic for identifying table headers, rows, and footers.

    review/: Contains the audit engine and the "Detective" script (excel_diff.py) that identifies human corrections.

    memory/: The storage center for learned patterns (correction_memory.json).

    output/: Generates stylized, color-coded Excel reports for accountants.

    runtime/: The dynamic workspace where files are sorted into Clean, Review, and Archive folders.

🛠 Tech Stack & Dependencies

    Python 3.x: Core logic.

    Tesseract OCR: The primary optical character recognition engine.

    OpenCV (cv2): Advanced image preprocessing (Binarization, Noise reduction).

    Pandas: High-performance data manipulation for "Diff" operations.

    Openpyxl: Financial report generation with conditional formatting.

    Difflib: Fuzzy string matching for character-level error tolerance.

    Pathlib: Cross-platform filesystem management.

🚦 Operational Workflow
1. The Processing Phase

Drop invoice images or PDFs into the /uploads folder.
Bash

python batch_process.py

    The Problem it Fixes: Manual data entry and "hallucinated" OCR characters.

    The Result: Data is audited. Correct files go to runtime/clean. Files with math errors or low-confidence text go to runtime/review.

2. The Human Review Phase

    Open the Excel files in runtime/review.

    The accountant corrects any highlighted errors.

    The corrected file is re-uploaded/moved to runtime/review/corrected.

3. The Learning Phase (Automated Training)

Run the training engine to update the AI's "Brain":
Bash

python mass_train.py

    The Problem it Fixes: "Knowledge Loss." When an accountant fixes a mistake, the system now remembers that fix.

    The Result: Updates correction_memory.json. The messy original is deleted, and the corrected version is archived.

📈 Developer Guide: Adding New Math Rules

To add new audit logic (e.g., VAT verification or Discount checks), modify parser/review.py:

    Define the Rule: Create a function that takes a row and checks a condition.

    Assign Status: Update the assign_review_status function to return a new flag (e.g., CHECK_VAT).

    Update Stylist: Add a color-code for your new flag in output/excel_writer.py.

🩺 System Health Monitoring

To verify system performance and see the most frequent OCR errors being caught:
Bash

python system_health.py

🔧 Installation

    Install Tesseract OCR on your operating system.

    Clone the project and install Python requirements:
    Bash

    pip install pandas openpyxl pytesseract opencv-python

    Initialize: Run python batch_process.py to auto-generate the directory structure.