import re


def validate_medical_document(text: str) -> dict:

    if not text:
        return {
            "is_medical_document": False,
            "score": 0,
            "matched_keywords": [],
            "message": "No text could be extracted from the document."
        }

    text_lower = text.lower()

    medical_keywords = [
        "hemoglobin",
        "haemoglobin",
        "wbc",
        "white blood cell",
        "rbc",
        "red blood cell",
        "platelets",
        "glucose",
        "creatinine",
        "urea",
        "bilirubin",
        "cholesterol",
        "triglycerides",

        "patient",
        "doctor",
        "hospital",
        "laboratory",
        "lab",
        "specimen",
        "sample",
        "reference range",
        "result",

        "prescription",
        "medicine",
        "tablet",
        "capsule",

        "mg/dl",
        "g/dl",
        "mmhg",
        "bpm"
    ]

    matched_keywords = []

    for keyword in medical_keywords:

        pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

        if re.search(pattern, text_lower):
            matched_keywords.append(keyword)

    score = len(matched_keywords)

    is_medical = score >= 3

    return {
        "is_medical_document": is_medical,
        "score": score,
        "matched_keywords": matched_keywords
    }