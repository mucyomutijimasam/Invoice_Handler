#ocr/preprocess.py
import cv2
import numpy as np

def deskew(image):
    """Straightens the image if it was scanned at an angle."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Find all foreground pixels
    coords = np.column_stack(np.where(gray > 0))
    # Calculate the minimum area rectangle around the pixels
    angle = cv2.minAreaRect(coords)[-1]

    # Adjust the angle for rotation
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated

def preprocess_image(image_path):
    # 1. Load the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found or unreadable at: {image_path}")

    # 2. Straighten it (Deskew)
    img = deskew(img)

    # 3. Resize (Scaling up helps OCR read small text)
    # This doubles the image size.
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # 4. Convert to Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 5. Improve contrast (Thresholding)

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 2
    )

    # 6. Remove Noise (Morphology)
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)


    return cleaned