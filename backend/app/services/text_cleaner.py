import re


def clean_ocr_text(text: str) -> str:

    if not text:
        return ""

    # Windows/Linux line endings ko normalize karo
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Har line ke starting/ending spaces remove karo
    lines = []

    for line in text.split("\n"):

        line = line.strip()

        if line:
            lines.append(line)

    # Ek line ke andar multiple spaces ko single space karo
    cleaned_lines = []

    for line in lines:

        line = re.sub(r"[ \t]+", " ", line)

        # Normalize common OCR unit errors right after numbers (e.g. 96 mgldl -> 96 mg/dl, 96 mg\dl -> 96 mg/dl)
        line = re.sub(
            r'(?<=\d)\s*(?P<prefix>mg|mcg|µg|ug|ng|pg|gms|gm|g|mmol)(?:[lI1](?=[A-Za-z])|[\\|.:_-]+)(?P<rest>[A-Za-z%µ0-9^]+)\b',
            r' \g<prefix>/\g<rest>',
            line,
            flags=re.IGNORECASE
        )

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)