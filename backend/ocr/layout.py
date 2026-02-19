#ocr/layout.py
def group_words_into_lines(ocr_data, min_conf=0):
    lines = {}
    for i, text in enumerate(ocr_data["text"]):
        if not text.strip():
            continue
        y = ocr_data["top"][i]
        line_key = y // 10
        lines.setdefault(line_key, []).append({
            "text": text,
            "x": ocr_data["left"][i],
            "y": y,
            "w": ocr_data["width"][i]
        })

    # sort by average y (top) so we return top-to-bottom order
    sorted_items = sorted(lines.items(), key=lambda kv: kv[0])
    return [sorted(line_words, key=lambda w: w['x']) for _, line_words in sorted_items]
