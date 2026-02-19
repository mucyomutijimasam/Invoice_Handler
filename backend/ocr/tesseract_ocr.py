#ocr/tesseract_ocr.py
import pytesseract
from pytesseract import Output

# Point to the NATIVE apt installation, not the Snap one
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def extract_ocr_data(image):
    # This will now work because the apt version has access to /tmp
    data = pytesseract.image_to_data(
        image,
        output_type=Output.DICT,
        config="--oem 3 --psm 4"
    )
    return data