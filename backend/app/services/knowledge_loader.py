import re
import pandas as pd
from pathlib import Path
from functools import lru_cache


# =========================================================
# MEDSAATHI KNOWLEDGE BASE LOADER - V2
# =========================================================
# Expected structure:
#
# backend/
#   app/
#     services/
#       knowledge_loader.py
#
# backend/
#   data/
#       medical_master.xlsx
#       medical_terms.xlsx
#       healthcare_services.xlsx
#       hospital_patient_keywords.xlsx
#
# This loader DOES NOT extract values from reports.
# It only loads and normalizes the knowledge base so that
# metadata_extractor.py can use:
#   - synonyms
#   - regex patterns
#   - value regex
#   - location hints
#   - priority
#   - validation rules
#   - examples
#
# =========================================================


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def clean_value(value):
    """Convert an Excel cell into a clean string."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def split_values(value):
    """
    Split synonyms/keywords written with:
        |
        ,
        ;

    Example:
        Hb|HGB
    -> ["Hb", "HGB"]
    """

    value = clean_value(value)

    if not value:
        return []

    parts = re.split(r"[|,;]", value)

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def normalize_bool(value):
    """Convert common Excel Yes/No values into bool."""
    value = clean_value(value).lower()

    if value in {"yes", "y", "true", "1", "mandatory"}:
        return True

    if value in {"no", "n", "false", "0", "optional"}:
        return False

    return None


def normalize_number(value, default=None):
    """Safely convert Excel number-like values."""
    value = clean_value(value)

    if not value:
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def get_column(row, *names):
    """
    Safely get a value from a row using multiple possible
    column-name variations.

    This makes the loader tolerant of small Excel header
    naming differences.
    """

    # Build normalized lookup once for this row.
    normalized = {
        re.sub(r"[\s_]+", "", str(column).strip().lower()): column
        for column in row.index
    }

    for name in names:
        if name in row.index:
            return clean_value(row[name])

        key = re.sub(r"[\s_]+", "", str(name).strip().lower())

        if key in normalized:
            return clean_value(row[normalized[key]])

    return ""


def validate_regex(pattern):
    """
    Validate a regex before sending it to the extraction engine.

    Important:
    - Excel should contain a REAL regex.
    - Do not store a Python repr such as:
        '(?i)\\b...'
      if the actual cell contains literal double backslashes.
    """

    pattern = clean_value(pattern)

    if not pattern:
        return ""

    try:
        re.compile(pattern)
        return pattern
    except re.error as exc:
        print(
            f"[WARNING] Invalid regex skipped: {pattern!r} | {exc}"
        )
        return ""


def read_excel(filename):
    """
    Read an Excel knowledge-base file safely.
    Handles Windows PermissionError by copying the file to a temp location.
    """
    import shutil
    import tempfile
    
    path = DATA_DIR / filename

    if not path.exists():
        print(f"[WARNING] File not found: {path}")
        return pd.DataFrame()

    temp_path = None
    try:
        try:
            df = pd.read_excel(path)
        except PermissionError:
            # File is likely open in Excel, create a temp copy to read
            print(f"[INFO] {filename} is locked. Creating a temporary copy to read...")
            temp_fd, temp_path_str = tempfile.mkstemp(suffix=".xlsx")
            import os
            os.close(temp_fd)
            temp_path = Path(temp_path_str)
            shutil.copy2(path, temp_path)
            df = pd.read_excel(temp_path)

        # Remove completely empty rows.
        df = df.dropna(how="all")

        # Normalize column names.
        df.columns = [
            str(column).strip()
            for column in df.columns
        ]

        print(
            f"[OK] Loaded {filename} "
            f"({len(df)} rows)"
        )

        return df

    except Exception as e:
        print(
            f"[ERROR] Could not read {filename}: {e}"
        )
        return pd.DataFrame()
    finally:
        # Cleanup temp file if created
        if temp_path and temp_path.exists():
            try:
                import os
                os.remove(temp_path)
            except Exception:
                pass


# ---------------------------------------------------------
# MEDICAL MASTER
# ---------------------------------------------------------

def load_medical_master():

    df = read_excel("medical_master.xlsx")

    records = []

    if df.empty:
        return records

    for _, row in df.iterrows():

        record = {
            "code": get_column(row, "Code"),

            "category": get_column(row, "Category"),

            "parameter": get_column(row, "Parameter"),

            "synonyms": split_values(
                get_column(row, "Synonyms", "Synonym")
            ),

            "regex_pattern": validate_regex(
                get_column(
                    row,
                    "Regex Pattern",
                    "Regex_Pattern",
                    "Regex Pattern "
                )
            ),

            "unit": get_column(row, "Unit"),

            "gender": get_column(
                row,
                "Gender",
                "Gender Specific"
            ),

            "age_group": get_column(
                row,
                "Age Group",
                "Age_Group"
            ),

            "normal_min": normalize_number(
                get_column(row, "Normal Min", "Normal_Min")
            ),

            "normal_max": normalize_number(
                get_column(row, "Normal Max", "Normal_Max")
            ),

            "critical_min": normalize_number(
                get_column(row, "Critical Min", "Critical_Min")
            ),

            "critical_max": normalize_number(
                get_column(row, "Critical Max", "Critical_Max")
            ),

            "priority": get_column(row, "Priority"),

            "description": get_column(row, "Description")
        }

        if record["parameter"]:
            records.append(record)

    return records


# ---------------------------------------------------------
# MEDICAL TERMS
# ---------------------------------------------------------

def load_medical_terms():

    df = read_excel("medical_terms.xlsx")

    records = []

    if df.empty:
        return records

    for _, row in df.iterrows():

        record = {
            "term_id": get_column(
                row,
                "Term_ID",
                "Term ID"
            ),

            "medical_term": get_column(
                row,
                "Medical_Term",
                "Medical Term"
            ),

            "simple_meaning": get_column(
                row,
                "Simple_Meaning",
                "Simple Meaning"
            ),

            "description": get_column(
                row,
                "Description"
            ),

            "why_important": get_column(
                row,
                "Why_Important",
                "Why Important"
            ),

            "effects_low": get_column(
                row,
                "Possible_Effects_if_Low",
                "Possible Effects if Low"
            ),

            "effects_high": get_column(
                row,
                "Possible_Effects_if_High",
                "Possible Effects if High"
            ),

            "common_symptoms": get_column(
                row,
                "Common_Symptoms",
                "Common Symptoms"
            ),

            "dietary_suggestions": get_column(
                row,
                "General_Dietary_Suggestions",
                "General Dietary Suggestions"
            ),

            "lifestyle_advice": get_column(
                row,
                "General_Lifestyle_Advice",
                "General Lifestyle Advice"
            ),

            "notes": get_column(row, "Notes")
        }

        if record["medical_term"]:
            records.append(record)

    return records


# ---------------------------------------------------------
# HEALTHCARE SERVICES
# ---------------------------------------------------------

def load_healthcare_services():

    df = read_excel("healthcare_services.xlsx")

    records = []

    if df.empty:
        return records

    for _, row in df.iterrows():

        record = {
            "service_id": get_column(
                row,
                "Service_ID",
                "Service ID"
            ),

            "service_name": get_column(
                row,
                "Service_Name",
                "Service Name"
            ),

            "category": get_column(
                row,
                "Category"
            ),

            "subcategory": get_column(
                row,
                "Subcategory"
            ),

            "description": get_column(
                row,
                "Description"
            ),

            "purpose": get_column(
                row,
                "Purpose"
            ),

            "common_uses": get_column(
                row,
                "Common_Uses",
                "Common Uses"
            ),

            "body_part": get_column(
                row,
                "Body_Part",
                "Body Part"
            ),

            "department": get_column(
                row,
                "Department"
            ),

            "preparation": get_column(
                row,
                "Preparation"
            ),

            "duration": get_column(
                row,
                "Duration"
            ),

            "radiation": get_column(
                row,
                "Radiation"
            ),

            "contrast": get_column(
                row,
                "Contrast"
            ),

            "sample_type": get_column(
                row,
                "Sample_Type",
                "Sample Type"
            ),

            "result_timing": get_column(
                row,
                "Result_Timing",
                "Result Timing"
            ),

            "invasive": get_column(
                row,
                "Invasive"
            ),

            "requires_prescription": get_column(
                row,
                "Requires_Prescription",
                "Requires Prescription"
            ),

            "gender": get_column(
                row,
                "Gender",
                "Gender Specific"
            ),

            "age_group": get_column(
                row,
                "Age_Group",
                "Age Group"
            ),

            "synonyms": split_values(
                get_column(
                    row,
                    "Synonyms",
                    "Synonym"
                )
            ),

            "keyword": get_column(
                row,
                "Keyword",
                "Keywords"
            )
        }

        if (
            record["service_name"]
            or record["keyword"]
        ):
            records.append(record)

    return records


# ---------------------------------------------------------
# HOSPITAL / PATIENT KEYWORDS
# ---------------------------------------------------------

def load_hospital_patient_keywords():

    # IMPORTANT:
    # The active hospital/patient keyword workbook.

    df = read_excel(
        "hospital_patient_keywords.xlsx"
    )

    records = []

    if df.empty:
        return records

    for _, row in df.iterrows():

        record = {
            "keyword_id": get_column(
                row,
                "Keyword_ID",
                "Keyword ID"
            ),

            "keyword": get_column(
                row,
                "Keyword"
            ),

            "standard_field": get_column(
                row,
                "Standard_Field",
                "Standard Field"
            ),

            "category": get_column(
                row,
                "Category"
            ),

            "synonyms": split_values(
                get_column(
                    row,
                    "Synonyms",
                    "Synonym"
                )
            ),

            # Label/key regex:
            # finds the label such as Patient Name, DOB,
            # Doctor, Test Name etc.
            "regex_pattern": validate_regex(
                get_column(
                    row,
                    "Regex_Pattern",
                    "Regex Pattern"
                )
            ),

            "data_type": get_column(
                row,
                "Data_Type",
                "Data Type"
            ),

            "example": get_column(
                row,
                "Example"
            ),

            "mandatory": get_column(
                row,
                "Mandatory"
            ),

            "notes": get_column(
                row,
                "Notes"
            ),

            # -------------------------------------------------
            # V2 OPTIONAL COLUMNS
            # -------------------------------------------------

            # Higher value = try this field earlier.
            "extraction_priority": normalize_number(
                get_column(
                    row,
                    "Extraction_Priority",
                    "Extraction Priority"
                ),
                default=50
            ),

            # Regex for the VALUE itself, not the label.
            #
            # Example for age:
            # (?P<value>\d{1,3})\s*(?:yrs?|years?)
            #
            # Example for phone:
            # (?P<value>\+?\d[\d\s().-]{7,}\d)
            "value_regex": validate_regex(
                get_column(
                    row,
                    "Value_Regex",
                    "Value Regex",
                    "Value_Regex_Pattern"
                )
            ),

            # Helps the extractor know where to search.
            # Examples:
            # top_header
            # patient_section
            # report_header
            # report_body
            # footer
            # anywhere
            "location_hint": get_column(
                row,
                "Location_Hint",
                "Location Hint"
            ).lower(),

            # A lightweight semantic hint used by the
            # extractor to reject obvious wrong values.
            "validation_rule": get_column(
                row,
                "Validation_Rule",
                "Validation Rule"
            ),

            # Optional confidence weight.
            "confidence_weight": normalize_number(
                get_column(
                    row,
                    "Confidence_Weight",
                    "Confidence Weight"
                ),
                default=1.0
            ),

            # Optional list of words/labels that should NOT
            # be accepted as the extracted value.
            "exclude_values": split_values(
                get_column(
                    row,
                    "Exclude_Values",
                    "Exclude Values"
                )
            )
        }

        if record["keyword"]:
            records.append(record)

    return records


# ---------------------------------------------------------
# MASTER LIST
# ---------------------------------------------------------

def load_master_list():
    df = read_excel("master_List.xlsx")
    records = []
    if df.empty:
        return records
        
    for _, row in df.iterrows():
        param = get_column(row, "Master List", "Master_List", "Parameter")
        if param:
            records.append(param)
            
    return records


# ---------------------------------------------------------
# COMPLETE KNOWLEDGE BASE
# ---------------------------------------------------------

@lru_cache(maxsize=1)
def load_knowledge_base():

    print("\n========== MEDSAATHI KNOWLEDGE BASE ==========")

    knowledge = {
        "medical_master": load_medical_master(),
        "medical_terms": load_medical_terms(),
        "healthcare_services": load_healthcare_services(),
        "hospital_patient_keywords": load_hospital_patient_keywords(),
        "master_list": load_master_list()
    }

    print("-----------------------------------------------")

    print(
        "Medical Master:",
        len(knowledge["medical_master"])
    )

    print(
        "Medical Terms:",
        len(knowledge["medical_terms"])
    )

    print(
        "Healthcare Services:",
        len(knowledge["healthcare_services"])
    )

    print(
        "Hospital/Patient Keywords:",
        len(knowledge["hospital_patient_keywords"])
    )

    print(
        "Master List:",
        len(knowledge["master_list"])
    )

    print("===============================================\n")

    # -----------------------------------------------------
    # REGEX TEST
    # -----------------------------------------------------
    print("===== REGEX TEST =====")

    test_ids = {
        "HPK001",  # Patient Name
        "HPK007",  # DOB
        "HPK034",  # Doctor
        "HPK035",  # Ref. By
        "HPK068",  # Test Name
        "HPK069"   # Report Type
    }

    for row in knowledge["hospital_patient_keywords"]:

        if row.get("keyword_id") in test_ids:

            print(f"\n{row.get('keyword_id')}")
            print("Keyword :", row.get("keyword"))
            print("Regex   :", repr(row.get("regex_pattern")))
            print("ValueRx :", repr(row.get("value_regex")))
            print("Synonyms:", row.get("synonyms"))
            print("Field   :", row.get("standard_field"))
            print("Priority:", row.get("extraction_priority"))
            print("Location:", row.get("location_hint"))
            print("Rule    :", row.get("validation_rule"))

    print("========================\n")

    return knowledge


# ---------------------------------------------------------
# OPTIONAL: QUICK TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    knowledge = load_knowledge_base()

    print(
        "Knowledge base loaded successfully."
    )