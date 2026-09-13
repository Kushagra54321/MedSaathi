"""
MedSaathi Metadata Extractor v7
================================

Goals
-----
1. Keep hospital_patient_keywords.xlsx as the source of truth for:
   - Keyword
   - Standard_Field
   - Category
   - Synonyms
   - Regex_Pattern
   - Data_Type

2. Treat Regex_Pattern as a LABEL locator, not as a value extractor.

3. Support real-world medical reports where:
   - Patient Name is not written as "Patient Name:"
   - Hospital name appears only in the top header
   - Doctor appears as Dr./Physician/Attending/Consultant
   - Test name appears as a report heading rather than "Test Name:"
   - OCR breaks labels and values across lines
   - dates/phones are noisy

4. Never accept obvious clinical prose as a patient/doctor name.

5. Do not extract medical measurements here. That belongs to the
   medical-parameter extraction stage.

The extractor is deliberately conservative: a missing value is better than
putting the wrong text into metadata.
"""

import re
from typing import Any, Optional

from app.services.knowledge_loader import load_knowledge_base


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ALLOWED_CATEGORIES = {
    "patient", "hospital", "doctor", "report", "sample",
    "identification", "specimen", "laboratory", "lab",
    "insurance", "appointment", "facility", "misc", "test",
}

MEDICAL_PREFIXES = (
    "cbc.", "liver.", "kidney.", "renal.", "lipid.", "thyroid.",
    "diabetes.", "glucose.", "urine.", "cardiac.", "electrolyte.",
    "electrolytes.", "hormone.", "hormones.", "tumor.", "infection.",
    "autoimmune.", "genetic.", "genetics.", "molecular.", "abg.",
    "pancreatic.", "respiratory.", "neurology.", "bone.", "coagulation.",
)

MEDICAL_KEYWORDS = {
    "hemoglobin", "wbc", "wbc count", "white blood cell", "rbc",
    "red blood cell", "platelets", "glucose", "glucose fasting",
    "hba1c", "creatinine", "urea", "egfr", "sodium", "potassium",
    "chloride", "calcium", "ast", "alt", "alp", "bilirubin", "ldl",
    "hdl", "cholesterol", "triglycerides", "tsh", "t3", "t4",
    "cea", "cyfra 21-1", "ca 19-9", "afp", "crp",
}

HEADER_ORG_TERMS = (
    "hospital", "medical center", "medical centre", "health center",
    "health centre", "clinic", "diagnostic", "laboratory", "lab",
    "institute", "healthcare", "health care", "health system",
    "oncology center", "oncology institute", "cancer center",
)

NON_ORG_HEADER_LINES = {
    "laboratory", "pathology", "radiology", "oncology",
    "patient diagnostic pathology summary", "final report",
    "final oncology diagnostic report", "patient report",
}

GENERIC_LABELS = {
    "name", "patient", "test", "report", "phone", "address",
    "center", "branch", "sex", "gender", "result", "reference",
    "status", "specimen", "sample",
}

BAD_PERSON_TERMS = {
    "report", "diagnosis", "history", "symptom", "clinical", "finding",
    "assessment", "plan", "mass", "lesion", "malignant", "pressure",
    "weight loss", "cough", "chest", "pain", "laboratory", "pathology",
    "radiology", "oncology", "department", "medicine", "summary",
    "result", "reference", "range", "normal", "abnormal", "pathologist", 
    "consultant", "done", "technician", "technologist", "specialist"
}

LAYOUT_ALIASES = {
    "patient.name": [
        r"patient(?:'s)?\s*(?:name|full\s*name)",
        r"pt\.?\s*(?:name|nm)",
        r"name\s+of\s+patient",
    ],
    "sample.id": [r"sample\s*(?:id|no|number)"],
    "report.report_date": [
        r"service\s*date",
        r"date\s*of\s*service",
        r"report\s*date",
        r"date\s*of\s*report",
    ],
    "doctor.name": [
        r"attending\s*(?:doctor|physician|cardiologist)",
        r"treating\s*(?:doctor|physician)",
        r"consulting\s*(?:doctor|physician)",
        r"oncologist",
        r"cardiologist",
    ],
    "doctor.referring": [
        r"ref\.?\s*by",
        r"referred\s*by",
        r"referring\s*(?:doctor|physician|md)",
    ],
}


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\x0c", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_value(value: Any) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" :|=-;,")


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean_value(value).lower())


def normalize_regex(pattern: Any) -> str:
    r"""
    Excel often stores regex with double escaping.

    Example:
        '(?i)\\b(?:dob|date\\s*of\\s*birth)\\b'
    becomes:
        (?i)\b(?:dob|date\s*of\s*birth)\b

    IMPORTANT:
    Never split a regex on '|'. The pipe is part of regex alternation.
    """
    if pattern is None:
        return ""

    p = str(pattern).strip()

    # Remove one pair of wrapping quotes if Excel/CSV data supplied them.
    if len(p) >= 2 and p[0] == p[-1] and p[0] in {"'", '"'}:
        p = p[1:-1]

    # Convert double escaped backslashes to regex backslashes.
    while "\\\\" in p:
        p = p.replace("\\\\", "\\")

    return p.strip()


def safe_search(pattern: str, text: str):
    p = normalize_regex(pattern)
    if not p or not text:
        return None
    try:
        return re.search(p, text, re.IGNORECASE)
    except re.error:
        return None


def split_synonyms(value) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if value is None:
        return []

    # This split is ONLY for the Synonyms column.
    # Never use this function for Regex_Pattern.
    return [x.strip() for x in re.split(r"[,;|]", str(value)) if x.strip()]


def kb_records(kb: dict, key: str) -> list[dict]:
    value = kb.get(key, [])
    return value if isinstance(value, list) else []


def find_record(records: list[dict], field: str) -> dict:
    for r in records:
        if str(r.get("standard_field") or "").strip().lower() == field.lower():
            return r
    return {}


# ---------------------------------------------------------------------------
# Knowledge-base filtering
# ---------------------------------------------------------------------------

def record_is_metadata(record: dict) -> bool:
    field = str(record.get("standard_field") or "").lower().strip()
    category = str(record.get("category") or "").lower().strip()
    keyword = str(record.get("keyword") or "").lower().strip()

    if field.startswith(MEDICAL_PREFIXES):
        return False

    if keyword in MEDICAL_KEYWORDS:
        return False

    if category in ALLOWED_CATEGORIES:
        return True

    return field.startswith((
        "patient.", "hospital.", "doctor.", "report.", "sample.",
        "specimen.", "lab.", "laboratory.", "test.", "misc."
    ))


def label_candidates(record: dict) -> list[str]:
    keyword = str(record.get("keyword") or "").strip()
    syns = split_synonyms(record.get("synonyms"))
    candidates = [keyword] + syns

    field = str(record.get("standard_field") or "").lower()

    # Dangerous generic words must not be used for these fields.
    if field == "patient.name":
        candidates = [
            x for x in candidates
            if norm(x) not in {"name", "patient"}
        ]
    elif field == "report.test_name":
        candidates = [
            x for x in candidates
            if norm(x) not in {"test"}
        ]
    elif field == "hospital.name":
        candidates = [
            x for x in candidates
            if norm(x) not in {"hospital", "lab"}
        ]

    return sorted(set(candidates), key=lambda x: len(x), reverse=True)


# ---------------------------------------------------------------------------
# Label detection
# ---------------------------------------------------------------------------

def structured_label_match(line: str, record: dict) -> bool:
    r"""
    Regex is used to identify the LABEL.

    A regex like:
        (?i)\b(?:report\s*type|type\s*of\s*report)\b\s*[:#-]?

    must be compiled as ONE regex. It must never be split on '|'.
    """
    if not line:
        return False

    candidates = label_candidates(record)
    field = str(record.get("standard_field") or "").lower()

    pattern = normalize_regex(record.get("regex_pattern"))

    if pattern:
        m = safe_search(pattern, line)
        if m:
            prefix = line[:m.start()].strip()
            suffix = line[m.end():]

            # Prevent matching a word inside clinical prose.
            if not prefix:
                if not suffix or not suffix[0].isalnum():
                    return True

    for c in candidates:
        if not c:
            continue

        # Explicit "Label: value"
        if re.match(
            r"^\s*" + re.escape(c) + r"\s*(?::|=|-)\s*.+$",
            line, re.I
        ):
            return True

        # Label on its own line.
        if re.match(
            r"^\s*" + re.escape(c) + r"\s*(?::|=|-)?\s*$",
            line, re.I
        ):
            return True

        # "Patient Name Rahul Sharma", but don't allow generic labels.
        if norm(c) not in GENERIC_LABELS and re.match(
            r"^\s*" + re.escape(c) + r"\s+.+$",
            line, re.I
        ):
            return True

    for alias in LAYOUT_ALIASES.get(field, []):
        if re.match(r"^\s*" + alias + r"\s*(?::|=|-)?\s*.+$", line, re.I):
            return True
        if re.match(r"^\s*" + alias + r"\s*(?::|=|-)?\s*$", line, re.I):
            return True

    return False


def value_after_label(line: str, record: dict) -> str:
    candidates = label_candidates(record)

    for candidate in candidates:
        if not candidate:
            continue

        # Label: value
        m = re.search(
            r"(?<!\w)" + re.escape(candidate) +
            r"(?!\w)\s*(?::|=|-)\s*(.+?)\s*$",
            line, re.I
        )
        if m:
            return clean_value(m.group(1))

        # Label value
        m = re.search(
            r"^\s*" + re.escape(candidate) +
            r"(?!\w)\s+(.+?)\s*$",
            line, re.I
        )
        if m:
            tail = clean_value(m.group(1))
            if norm(tail) != norm(candidate):
                return tail

    return ""


def looks_like_label_or_header(line: str, record: Optional[dict] = None) -> bool:
    x = norm(line)
    if not x:
        return True

    headings = {
        "patient", "mrn", "dob", "age sex", "mobile", "phone",
        "report no", "report id", "sample", "service date",
        "referring doctor", "oncologist", "hospital", "department",
        "chief complaint", "history", "clinical indication",
        "parameter", "result", "unit", "reference", "status",
        "tumor markers", "marker", "imaging pathology molecular",
        "final report", "final diagnosis", "stage", "assessment", "plan",
    }

    if x in {norm(h) for h in headings}:
        return True

    if len(line.split()) <= 4 and line.endswith(":"):
        return True

    return False


def next_value(lines: list[str], index: int, record: dict) -> str:
    line = lines[index].strip()

    v = value_after_label(line, record)
    if v:
        return v

    field = str(record.get("standard_field") or "").lower()

    for alias in LAYOUT_ALIASES.get(field, []):
        m = re.search(alias, line, re.I)
        if m:
            tail = clean_value(line[m.end():]).lstrip(":=- ")
            if tail:
                return tail

    # Label on one line, value on next line(s).
    for j in range(index + 1, min(index + 4, len(lines))):
        nxt = lines[j].strip()
        if not nxt:
            continue

        if looks_like_label_or_header(nxt, record):
            return ""

        return clean_value(nxt)

    return ""


# ---------------------------------------------------------------------------
# Value validation
# ---------------------------------------------------------------------------

def person_value_ok(value: str) -> bool:
    value = clean_value(value)

    # Remove credentials.
    base = re.sub(
        r",?\s*(MD|MBBS|DO|DM|DNB|MS|PhD|FACC|FRCP|RN|MPH)\b.*$",
        "",
        value,
        flags=re.I,
    ).strip(" ,")

    if not base:
        return False

    words = base.split()
    # Relaxed to allow 1-word names (e.g. "Kushagra") and up to 8 words
    if not (1 <= len(words) <= 8):
        return False

    if re.search(r"[.!?]", base):
        return False

    if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ.'\- ]+", base):
        return False

    low = base.lower()

    if any(term in low for term in BAD_PERSON_TERMS):
        return False

    # Names usually contain at least one alphabetic token.
    alpha_tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+", base)
    if len(alpha_tokens) < 1:
        return False

    return True


def looks_like_person_name(value: str) -> bool:
    return person_value_ok(value)


def valid_date(value: str) -> bool:
    value = clean_value(value)

    patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|"
        r"Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|"
        r"Nov|November|Dec|December)\s+\d{1,2},?\s+\d{4}\b",
    ]

    return any(re.search(p, value, re.I) for p in patterns)


def valid_value(value: str, record: dict) -> bool:
    value = clean_value(value)
    if not value:
        return False

    keyword = str(record.get("keyword") or "")
    field = str(record.get("standard_field") or "").lower()
    dtype = str(record.get("data_type") or "").lower()

    if norm(value) == norm(keyword):
        return False

    if value.upper() in {
        "NORMAL", "HIGH", "LOW", "CRITICAL", "RESULT", "REFERENCE",
        "STATUS", "UNIT", "PARAMETER", "TEST", "REPORT",
    }:
        return False

    if field == "patient.name" and not looks_like_person_name(value):
        return False

    if field == "doctor.name" or field.startswith("doctor."):
        if not looks_like_person_name(value):
            return False

    if field in {"patient.mobile", "patient.phone", "hospital.phone"}:
        digits = re.sub(r"\D", "", value)
        if not (7 <= len(digits) <= 15):
            return False

    if field == "patient.email" or field.endswith(".email"):
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            return False

    if field == "patient.gender":
        return bool(re.fullmatch(
            r"(male|female|other|m|f|non[- ]?binary)",
            value, re.I
        ))
        
    # Prevent garbage in test name
    if field == "report.test_name":
        # Reject if it's mostly numbers/symbols like 11.0-15.5
        if len(re.sub(r'[^A-Za-z]', '', value)) < 3:
            return False

    # Prevent 'Done', 'Result', 'Values' from becoming report names/types
    if field in {"report.type", "report.test_name", "test.reference_range"}:
        if value.lower() in {"done", "result", "values", "report", "test", "complete", "normal", "abnormal", "range", "reference", "high", "low"}:
            return False
            
    # Prevent addresses from becoming hospital names
    if field == "hospital.name":
        if re.search(r"\b(avenue|street|road|floor|building|block|nagar|marg|india|delhi|mumbai|chennai|tel)\b", value, re.I):
            return False

    if field == "patient.age":
        m = re.search(r"\b(\d{1,3})\b", value)
        if not m or not (0 <= int(m.group(1)) <= 120):
            return False

    if field == "patient.dob" and not valid_date(value):
        return False

    if "number" in dtype or dtype in {"integer", "float"}:
        if not re.search(r"\d", value):
            return False

    # A metadata field should not contain an entire clinical paragraph.
    if len(value.split()) > 18:
        return False

    return True


def convert_value(value: str, record: dict):
    value = clean_value(value)
    dtype = str(record.get("data_type") or "").lower()
    field = str(record.get("standard_field") or "").lower()

    if field == "patient.age":
        m = re.search(r"\d{1,3}", value)
        return int(m.group()) if m else value

    if "number" in dtype or dtype in {"integer", "float"}:
        m = re.search(r"[-+]?\d+(?:\.\d+)?", value.replace(",", ""))
        if m:
            n = m.group()
            return float(n) if "." in n else int(n)

    return value


# ---------------------------------------------------------------------------
# Header / context extraction
# ---------------------------------------------------------------------------

def header_hospital(lines: list[str]) -> Optional[str]:
    best = None
    best_score = -1

    for i, line in enumerate(lines[:15]):
        x = clean_value(line)
        low = x.lower()

        if not x or len(x) < 5 or len(x) > 100:
            continue

        if low in NON_ORG_HEADER_LINES:
            continue

        # Do not treat obvious patient/report content as hospital.
        if re.search(
            r"\b(patient|dob|mrn|diagnosis|history|chief complaint)\b",
            low, re.I
        ):
            continue

        score = 0

        if i == 0:
            score += 3

        if any(term in low for term in HEADER_ORG_TERMS):
            score += 6

        if re.search(
            r"\b(hospital|center|centre|clinic|institute|lab|laboratory)\b",
            low
        ):
            score += 2

        if "phone" in low or "tel" in low or "@" in low:
            score -= 4

        if low.startswith((
            "department", "patient", "final",
            "laboratory •", "laboratory,"
        )):
            score -= 5

        if score > best_score:
            best_score = score
            best = x

    return best if best_score >= 6 else None


def extract_header_phone(lines: list[str]) -> Optional[str]:
    for line in lines[:12]:
        m = re.search(
            r"(?:phone|tel|telephone|contact)\s*[:\-]?\s*"
            r"([+\d][\d\s().\-]{6,})",
            line, re.I
        )
        if m:
            return clean_value(m.group(1))
    return None


def extract_date_after_context(lines: list[str], contexts: tuple[str, ...]) -> Optional[str]:
    date_pattern = (
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}|"
        r"(?:Jan|January|Feb|February|Mar|March|Apr|April|May|"
        r"Jun|June|Jul|July|Aug|August|Sep|Sept|September|"
        r"Oct|October|Nov|November|Dec|December)\s+"
        r"\d{1,2},?\s+\d{4})\b"
    )

    for i, line in enumerate(lines):
        if re.search("|".join(contexts), line, re.I):
            m = re.search(date_pattern, line, re.I)
            if m:
                return clean_value(m.group(0))

            for j in range(i + 1, min(i + 3, len(lines))):
                m = re.search(date_pattern, lines[j], re.I)
                if m:
                    return clean_value(m.group(0))

    return None

def extract_mrn(lines: list[str]) -> Optional[str]:
    # TEACHING POINT: MRN/Patient ID is often merged with DOB like "MRN/DOB: 12345 / 01-01-2000"
    for line in lines[:40]:
        # Look for MRN, PID, Patient ID
        m = re.search(r"\b(MRN|PID|Patient\s*ID|ID\s*No|Registration\s*No)\s*[:/-]?\s*([#A-Z0-9\-]{4,15})", line, re.I)
        if m:
            val = m.group(2).strip()
            if not re.fullmatch(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", val): # Ignore if it caught the date
                return clean_value(val)
    return None

def extract_age_gender_robust(lines: list[str]) -> tuple[Optional[str], Optional[str]]:
    # TEACHING POINT: Age and gender are often squashed together e.g., "67Y/M" or "Age/Sex: 45 / Male"
    age = None
    gender = None
    for line in lines[:40]:
        # Look for (67Y) or 67 Yrs or Age: 67
        age_m = re.search(r"\b(?:age\s*[:=]?\s*)?(\d{1,3})\s*(?:Y|Yrs|Years?|/)\b", line, re.I)
        if age_m and not age:
            age = age_m.group(1)
            
        # Look for M, F, Male, Female usually near Age or Sex label
        gen_m = re.search(r"\b(?:sex|gender)\s*[:=]?\s*(Male|Female|M|F|Other)\b", line, re.I)
        if not gen_m:
            # Fallback for "45/M" or "45 Yrs M"
            gen_m = re.search(r"\b\d{1,3}\s*(?:Y|Yrs|Years?|/|-)?\s*(Male|Female|M|F)\b", line, re.I)
            if gen_m:
                gender = gen_m.group(1)
        else:
            gender = gen_m.group(1)
            
        if age and gender:
            break
    
    # Normalize gender
    if gender:
        gender = gender.upper()
        if gender.startswith('M'): gender = 'Male'
        elif gender.startswith('F'): gender = 'Female'
        
    return age, gender

def extract_department(lines: list[str]) -> Optional[str]:
    # Departments are usually in the top 20 lines, often with the word Department or specific specialties
    specialties = (
        r"\b(Cardiology|Cardiovascular|Radiology|Pathology|Oncology|Hematology|Biochemistry|"
        r"Microbiology|Immunology|Neurology|Orthopedics|Gastroenterology|Endocrinology|Outpatient|"
        r"Inpatient|Emergency)\b"
    )
    for line in lines[:20]:
        # "Department of Cardiology"
        m = re.search(r"\bDepartment\s+of\s+([A-Za-z\s]+)\b", line, re.I)
        if m and len(m.group(1).split()) <= 4:
            return clean_value(m.group(0))
        
        # Or just isolated specialty names
        m2 = re.search(specialties, line, re.I)
        if m2 and len(line.split()) <= 5: # It's a header line
            return clean_value(line)
            
    return None


def special_patient_name(lines: list[str]) -> Optional[str]:
    """
    Patient-name extraction in increasing order of confidence.

    A) Explicit label:
       Patient Name: Rahul Sharma

    B) Common two-column OCR:
       PATIENT
       Rahul Sharma

    C) Label-less patient header:
       Patient
       MONTGOMERY, ARTHUR E.
       MRN/DOB: ...

    The last case is common in real reports and is why v6 missed some
    genuine reports.
    """
    labels = (
        r"patient(?:'s)?\s*name",
        r"full\s*name",
        r"patient\s*name",
        r"pt\.?\s*(?:name|nm)",
        r"name\s+of\s+patient",
        r"^name\b",
    )

    # A: explicit label.
    for i, line in enumerate(lines):
        for pat in labels:
            m = re.search(pat, line, re.I)
            if not m:
                continue

            tail = clean_value(line[m.end():]).lstrip(":=- ")
            
            # TEACHING POINT: OCR often puts two columns on the same line
            # e.g., "Patient Name: MONTGOMERY ARTHUR MRN / DOB: 11/14/1958"
            # We must split the tail if it contains another common label.
            split_match = re.search(r"\b(MRN|DOB|Date of Birth|Age|Gender|Sex|Phone|Mobile)\b", tail, re.I)
            if split_match:
                tail = tail[:split_match.start()].strip(" |,-/\\")

            if tail and looks_like_person_name(tail):
                return tail

            for j in range(i + 1, min(i + 4, len(lines))):
                cand = clean_value(lines[j])
                
                # Also split candidate lines just in case
                split_match = re.search(r"\b(MRN|DOB|Date of Birth|Age|Gender|Sex|Phone|Mobile)\b", cand, re.I)
                if split_match:
                    cand = cand[:split_match.start()].strip(" |,-/\\")

                if looks_like_person_name(cand):
                    return cand

    # B/C: patient marker followed by a likely name.
    for i, line in enumerate(lines[:40]):
        if not re.fullmatch(
            r"(patient|patient information|patient demographics|"
            r"patient details|demographics)\s*:?",
            line, re.I
        ):
            continue

        for j in range(i + 1, min(i + 5, len(lines))):
            cand = clean_value(lines[j])

            # Stop if the next line is clearly another field.
            if re.match(
                r"^(mrn|dob|date of birth|age|gender|sex|phone|"
                r"mobile|address|hospital|department)\b",
                cand, re.I
            ):
                break

            # Real reports sometimes print SURNAME, GIVEN NAME.
            candidate_for_check = cand.replace(",", " ")
            if looks_like_person_name(candidate_for_check):
                return cand

    # D: line immediately before MRN/DOB can be the patient name.
    for i, line in enumerate(lines[:50]):
        if re.search(r"\b(?:mrn|medical record|dob|date of birth)\b", line, re.I):
            for j in range(max(0, i - 2), i):
                cand = clean_value(lines[j])

                if re.search(
                    r"^(patient|demographics|medical record|mrn)\b",
                    cand, re.I
                ):
                    continue

                candidate_for_check = cand.replace(",", " ")
                if looks_like_person_name(candidate_for_check):
                    return cand

    return None


def special_doctors(lines: list[str]) -> list[tuple[str, str, str]]:
    patterns = [
        (
            "doctor.name",
            r"(?:doctor(?:\s*name)?|attending\s*(?:doctor|physician|"
            r"cardiologist)|treating\s*(?:doctor|physician)|"
            r"consulting\s*(?:doctor|physician)|oncologist|cardiologist)"
        ),
        (
            "doctor.referring",
            r"(?:ref\.?\s*by|referred\s*by|"
            r"referring\s*(?:doctor|physician|md))"
        ),
        ("doctor.physician", r"(?:physician)"),
        ("doctor.pathologist", r"(?:pathologist)"),
        ("doctor.consultant", r"(?:consultant)"),
        ("doctor.signatory", r"(?:authorized\s*signatory)"),
        ("doctor.verified_by", r"(?:verified\s*by)"),
        ("doctor.approved_by", r"(?:approved\s*by)"),
        ("procedure.surgeon", r"(?:surgeon)"),
    ]

    out = []

    for i, line in enumerate(lines):
        for field, pat in patterns:
            m = re.match(r"^\s*" + pat + r"\s*:?\s*", line, re.I)
            if not m:
                continue

            tail = clean_value(line[m.end():])

            if tail.lower().startswith("dr"):
                tail = re.sub(r"^\s*dr\.?\s*", "", tail, flags=re.I)

            cand = tail if tail else (
                clean_value(lines[i + 1]) if i + 1 < len(lines) else ""
            )

            cand = re.sub(r"^\s*dr\.?\s*", "", cand, flags=re.I)

            if looks_like_person_name(cand):
                out.append((field, cand, "doctor_context"))

    # Also support:
    # Dr. John Smith
    # Physician: Dr. John Smith
    # but only near the header/metadata portion.
    for i, line in enumerate(lines[:60]):
        # Match 'Dr. Name' but ignore if it has other columns on the same line
        m = re.search(r"(?:dr|doctor)\.?\s+([A-Za-zÀ-ÖØ-öø-ÿ.'\- ]{3,40})", line, re.I)
        if m:
            cand = clean_value(m.group(1))
            # Split if there's a medical label merged by OCR
            split_match = re.search(r"\b(Referring|Date|MRN|DOB|Age|Patient)\b", cand, re.I)
            if split_match:
                cand = cand[:split_match.start()].strip(" |,-/\\")
                
            if looks_like_person_name(cand):
                out.append(("doctor.name", cand, "doctor_prefix"))

    return out


# ---------------------------------------------------------------------------
# Test-name fallback
# ---------------------------------------------------------------------------

def record_terms(record: dict) -> list[str]:
    terms = [
        str(record.get("keyword") or "").strip(),
        *split_synonyms(record.get("synonyms")),
        str(record.get("parameter") or "").strip(),
        str(record.get("medical_term") or "").strip(),
    ]
    return sorted(
        {x for x in terms if x},
        key=lambda x: len(x),
        reverse=True,
    )


def medical_test_candidates(kb: dict) -> list[str]:
    """
    Build candidate test names from medical_master and healthcare_services.

    This is a FALLBACK only. It is not used to extract numerical values.
    """
    candidates = []

    for key in (
        "medical_master",
        "medical_master1",
        "medical_terms",
        "medical_terms1",
        "healthcare_services",
        "healthcare_services1",
    ):
        for record in kb_records(kb, key):
            candidates.extend(record_terms(record))

    # Longest first avoids matching "test" before "high-sensitivity troponin".
    cleaned = []
    seen = set()

    for x in candidates:
        x = clean_value(x)
        k = norm(x)
        if not k or k in seen:
            continue
        if len(x) < 3:
            continue
        seen.add(k)
        cleaned.append(x)

    return sorted(cleaned, key=len, reverse=True)


def score_test_line(line: str, line_index: int, term: str) -> int:
    low = line.lower()
    t = term.lower()

    score = 0

    if t in low:
        score += min(40, len(term))

    # Header/title positions are more likely to contain report/test names.
    if line_index < 20:
        score += 15

    if line_index < 50:
        score += 5

    if re.search(
        r"\b(test|investigation|examination|procedure|panel|assay|"
        r"study|diagnostic|troponin|cbc|mri|ct|x[- ]?ray)\b",
        low, re.I
    ):
        score += 10

    # A test heading should not look like a numeric result row.
    if re.search(r"\b\d+(?:\.\d+)?\s*(?:mg|g|ml|dl|mmhg|bpm|/ul|%)\b", low):
        score -= 20

    if re.search(
        r"\b(reference range|normal range|result|status|unit|"
        r"interpretation|diagnosis|clinical indication)\b",
        low, re.I
    ):
        score -= 15

    return score


def fallback_test_name(lines: list[str], kb: dict) -> Optional[str]:
    """
    Handles reports where there is no "Test Name:" label.

    Example:
        CARDIOVASCULAR MEDICINE & ELECTROPHYSIOLOGY
        HIGH-SENSITIVITY TROPONIN
        Result: 23 ng/L

    We look for known medical terms/services in report headings.
    """
    terms = medical_test_candidates(kb)

    best_term = None
    best_score = 0

    # First 80 lines gives enough header/body context without scanning
    # every clinical sentence equally.
    for i, line in enumerate(lines[:80]):
        x = clean_value(line)

        if not x or len(x) > 120:
            continue

        # Skip obvious metadata labels.
        if re.match(
            r"^(patient|mrn|dob|age|gender|sex|phone|mobile|address|"
            r"hospital|department|doctor|physician|referring|"
            r"reference|result|status|unit)\b",
            x, re.I
        ):
            continue

        for term in terms:
            if len(term) < 4:
                continue

            if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", x, re.I):
                s = score_test_line(x, i, term)

                # Prefer a line that is mostly the test name rather than
                # a long paragraph containing the test term.
                if len(x.split()) <= 8:
                    s += 10

                if s > best_score:
                    best_score = s
                    best_term = x

    return best_term if best_score >= 20 else None


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def extract_metadata(text: str) -> dict:
    result = {
        "patient": {},
        "hospital": {},
        "doctor": {},
        "report": {},
        "sample": {},
        "other": {},
        "extracted_fields": [],
    }

    text = normalize_text(text)
    if not text:
        return result

    lines = [x.strip() for x in text.splitlines() if x.strip()]

    try:
        kb = load_knowledge_base()
    except Exception:
        kb = {}

    records = kb_records(kb, "hospital_patient_keywords")
    if not records:
        records = kb_records(kb, "hospital_patient_keywords")

    def add(
        field: str,
        value: Any,
        record: Optional[dict] = None,
        source: str = "context",
        confidence: float = 0.8,
    ):
        if value is None or value == "":
            return

        record = record or {
            "data_type": "Text",
            "standard_field": field,
            "keyword": field.split(".")[-1],
            "category": "",
        }

        converted = convert_value(str(value), record)

        # Existing strong value wins.
        existing = result
        for part in field.split("."):
            if isinstance(existing, dict):
                existing = existing.get(part)
            else:
                existing = None

        if existing not in (None, "", {}):
            return

        cur = result
        parts = field.split(".")

        for part in parts[:-1]:
            cur = cur.setdefault(part, {})

        cur[parts[-1]] = converted

        result["extracted_fields"].append({
            "keyword": record.get("keyword", parts[-1]),
            "standard_field": field,
            "category": record.get("category", ""),
            "value": converted,
            "data_type": record.get("data_type", "Text"),
            "source": source,
            "confidence": confidence,
        })

    # ------------------------------------------------------------------
    # 1. Strong contextual extraction
    # ------------------------------------------------------------------

    patient_name = special_patient_name(lines)
    if patient_name:
        rec = find_record(records, "patient.name")
        add("patient.name", patient_name, rec, "patient_context", 0.98)

    hospital_name = header_hospital(lines)
    if hospital_name:
        rec = find_record(records, "hospital.name")
        add("hospital.name", hospital_name, rec, "top_header", 0.96)

    hospital_phone = extract_header_phone(lines)
    if hospital_phone:
        rec = find_record(records, "hospital.phone")
        add("hospital.phone", hospital_phone, rec, "top_header_phone", 0.96)

    # DOB is explicitly validated as a date.
    dob = extract_date_after_context(
        lines,
        (
            r"\bdob\b",
            r"\bdate\s+of\s+birth\b",
            r"\bbirth\s+date\b",
        ),
    )
    if dob:
        rec = find_record(records, "patient.dob")
        add("patient.dob", dob, rec, "date_context", 0.97)

    # Robust MRN / Patient ID
    mrn = extract_mrn(lines)
    if mrn:
        rec = find_record(records, "patient.id")
        add("patient.id", mrn, rec, "mrn_context", 0.98)

    # Robust Age & Gender
    age, gender = extract_age_gender_robust(lines)
    if age:
        rec = find_record(records, "patient.age")
        add("patient.age", age, rec, "age_context", 0.96)
    if gender:
        rec = find_record(records, "patient.gender")
        add("patient.gender", gender, rec, "gender_context", 0.96)
        
    # Department / Specialty
    department = extract_department(lines)
    if department:
        rec = find_record(records, "hospital.department")
        add("hospital.department", department, rec, "department_context", 0.90)

    # Report date.
    report_date = extract_date_after_context(
        lines,
        (
            r"\breport\s+date\b",
            r"\bdate\s+of\s+report\b",
            r"\bservice\s+date\b",
            r"\bdate\s+of\s+service\b",
        ),
    )
    if report_date:
        rec = find_record(records, "report.report_date")
        add("report.report_date", report_date, rec, "date_context", 0.96)

    # Doctor context.
    for field, value, source in special_doctors(lines):
        rec = find_record(records, field)
        if valid_value(
            value,
            rec or {
                "standard_field": field,
                "data_type": "Text",
                "keyword": "",
            },
        ):
            add(field, value, rec, source, 0.95)

    # ------------------------------------------------------------------
    # 2. KB-driven explicit label/value extraction
    # ------------------------------------------------------------------

    for record in records:
        if not record_is_metadata(record):
            continue

        field = str(record.get("standard_field") or "").strip()
        if not field:
            continue

        # Strong contextual fields already handled.
        if field in {
            "patient.name",
            "hospital.name",
            "hospital.phone",
            "patient.dob",
            "report.report_date",
        }:
            # Only skip if we already found a value for this field contextually
            parts = field.split('.')
            if result.get(parts[0], {}).get(parts[1]):
                continue

        found = None

        for idx, line in enumerate(lines):
            if not structured_label_match(line, record):
                continue

            value = next_value(lines, idx, record)
            if not value:
                continue

            # Combined Age/Sex.
            if field == "patient.age_gender":
                m = re.match(
                    r"(\d{1,3})\s*/\s*"
                    r"(male|female|m|f|other)",
                    value,
                    re.I,
                )
                if m:
                    age_rec = find_record(records, "patient.age")
                    gender_rec = find_record(records, "patient.gender")

                    add(
                        "patient.age",
                        m.group(1),
                        age_rec,
                        "age_sex_context",
                        0.98,
                    )
                    add(
                        "patient.gender",
                        m.group(2),
                        gender_rec,
                        "age_sex_context",
                        0.98,
                    )
                continue

            if not valid_value(value, record):
                continue

            # Patient contact information must be near patient context.
            if field in {
                "patient.phone", "patient.mobile",
                "patient.email", "patient.address",
            }:
                neighborhood = " ".join(
                    lines[max(0, idx - 2):min(len(lines), idx + 3)]
                )

                if not re.search(
                    r"mobile|contact|phone|email|address",
                    line,
                    re.I,
                ):
                    continue

                if idx > 30 and not re.search(
                    r"patient|demographic",
                    neighborhood,
                    re.I,
                ):
                    continue

            # Hospital contact information must be near hospital context.
            if field in {
                "hospital.phone",
                "hospital.email",
                "hospital.address",
            }:
                neighborhood = " ".join(
                    lines[max(0, idx - 4):min(len(lines), idx + 5)]
                )

                if not re.search(
                    r"hospital|laboratory|lab|center|centre|institute",
                    neighborhood,
                    re.I,
                ):
                    continue

            # Hospital lab/service headers are not lab names.
            if field == "hospital.lab_name":
                if (
                    "•" in value
                    or "radiology" in value.lower()
                    or "pathology" in value.lower()
                ):
                    continue

            found = value
            break

        if found:
            add(field, found, record, "kb_label_value", 0.90)

    # ------------------------------------------------------------------
    # 3. Test-name fallback
    # ------------------------------------------------------------------

    if not result.get("report", {}).get("test_name"):
        test_name = fallback_test_name(lines, kb)

        if test_name:
            rec = find_record(records, "report.test_name")
            add(
                "report.test_name",
                test_name,
                rec,
                "medical_kb_header",
                0.86,
            )

    # ------------------------------------------------------------------
    # 4. Lightweight report-title fallback
    # ------------------------------------------------------------------

    if not result.get("report", {}).get("title"):
        # Pick a strong all-caps/organization-like heading, but never
        # overwrite a real report title from the KB.
        for line in lines[:25]:
            x = clean_value(line)

            if not x or len(x) > 100:
                continue

            if hospital_name and x == hospital_name:
                continue

            if re.search(
                r"\b(final report|diagnostic report|pathology report|"
                r"radiology report|laboratory report|cardiology report|"
                r"oncology report)\b",
                x,
                re.I,
            ):
                rec = find_record(records, "report.title")
                add("report.title", x, rec, "report_header", 0.80)
                break

    return result


# ---------------------------------------------------------------------------
# Optional standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    demo = """
    ST. JUDE MEDICAL CENTER
    CARDIOVASCULAR MEDICINE & ELECTROPHYSIOLOGY

    PATIENT
    MONTGOMERY, ARTHUR E.
    MRN/DOB: #984-110-42 / 11/14/1958

    Attending Cardiologist: Dr. Eleanor Vance
    High-Sensitivity Troponin
    Result: 23 ng/L
    """

    print(json.dumps(extract_metadata(demo), indent=2, ensure_ascii=False))



