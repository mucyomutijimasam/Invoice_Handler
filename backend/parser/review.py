#parser/review.py
import re

def normalize_amount(raw):
    if not raw:
        return None

    cleaned = re.sub(r"[^\d]", "", raw)

    # Too short to be a real monetary value
    if len(cleaned) < 3:
        return None

    return int(cleaned)


def is_noisy(text):
    if not text:
        return True

    non_alnum = sum(
        1 for c in text
        if not c.isalnum() and c not in ",."
    )

    noise_ratio = non_alnum / max(len(text), 1)
    return noise_ratio > 0.4


def assign_review_status(row):
    """
    Determines whether a row is safe or needs review.
    """

    # 1️⃣ OCR noise in critical text fields
    if is_noisy(row.get("Name", "")) or is_noisy(row.get("Service", "")):
        return "CHECK_OCR"

    # 2️⃣ Amount validation
    normalized = normalize_amount(row.get("Amount", ""))
    if normalized is None:
        return "CHECK_AMOUNT"

    # 3️⃣ Everything looks safe
    return "OK"
