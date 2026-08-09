import re
import pandas as pd
from pathlib import Path
from functools import lru_cache


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

# backend/
#   app/
#     services/
#       knowledge_loader.py
#
# DATA files are expected here:
# backend/data/

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def clean_value(value):
    """Convert a CSV/Excel cell into a clean string."""
    if value is None or pd.isna(value):
        return ""

    return str(value).strip()


def split_values(value):
    """
    Split synonyms/keywords written with:
        |
        ,
        ;

    Example:
        Hb|HGB
    becomes:
        ["Hb", "HGB"]
    """

    if value is None or pd.isna(value):
        return []

    parts = re.split(r"[|,;]", str(value))

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def read_excel(filename):
    """
    Read an Excel knowledge-base file safely.
    """

    path = DATA_DIR / filename

    if not path.exists():
        print(f"[WARNING] File not found: {path}")
        return pd.DataFrame()

    try:
        df = pd.read_excel(path)

        # Remove completely empty rows
        df = df.dropna(how="all")

        # Normalize column names
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


def get_column(row, *names):
    """
    Safely get a value from a row using multiple
    possible column-name variations.

    This makes the loader more tolerant of small
    Excel header naming differences.
    """

    for name in names:

        if name in row.index:
            return clean_value(row[name])

    return ""


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
            "code": get_column(
                row,
                "Code"
            ),

            "category": get_column(
                row,
                "Category"
            ),

            "parameter": get_column(
                row,
                "Parameter"
            ),

            "synonyms": split_values(
                get_column(
                    row,
                    "Synonyms",
                    "Synonym"
                )
            ),

            "regex_pattern": get_column(
                row,
                "Regex Pattern",
                "Regex_Pattern",
                "Regex Pattern "
            ),

            "unit": get_column(
                row,
                "Unit"
            ),

            "gender": get_column(
                row,
                "Gender"
            ),

            "age_group": get_column(
                row,
                "Age Group",
                "Age_Group"
            ),

            "normal_min": get_column(
                row,
                "Normal Min",
                "Normal_Min"
            ),

            "normal_max": get_column(
                row,
                "Normal Max",
                "Normal_Max"
            ),

            "critical_min": get_column(
                row,
                "Critical Min",
                "Critical_Min"
            ),

            "critical_max": get_column(
                row,
                "Critical Max",
                "Critical_Max"
            ),

            "priority": get_column(
                row,
                "Priority"
            ),

            "description": get_column(
                row,
                "Description"
            )
        }

        # Ignore completely empty records
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

            "notes": get_column(
                row,
                "Notes"
            )
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

            "regex_pattern": get_column(
                row,
                "Regex_Pattern",
                "Regex Pattern"
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
            )
        }

        if record["keyword"]:
            records.append(record)

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
        "hospital_patient_keywords":
            load_hospital_patient_keywords()
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
        len(
            knowledge[
                "hospital_patient_keywords"
            ]
        )
    )
    print("===============================================\n")

    return knowledge


# ---------------------------------------------------------
# OPTIONAL: QUICK TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    knowledge = load_knowledge_base()

    print(
        "Knowledge base loaded successfully."
    )