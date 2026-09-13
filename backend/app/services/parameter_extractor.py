import re
from typing import Optional, Union, List, Dict, Any
from app.services.knowledge_loader import load_knowledge_base


def parse_typed_value(raw_val: str) -> Union[float, int, str]:
    """
    Converts a value string into its exact native Python numeric type.
    - If it contains a decimal point (e.g. '7.5'), returns float (7.5).
    - If it is a whole number (e.g. '1500'), returns int (1500).
    - Never truncates float to int, preserving all medical measurement precision.
    """
    clean_val_str = re.sub(r'[<>,]', '', str(raw_val)).strip()
    if "." in clean_val_str:
        try:
            return float(clean_val_str)
        except ValueError:
            pass

    try:
        return int(clean_val_str)
    except ValueError:
        try:
            return float(clean_val_str)
        except ValueError:
            return raw_val


def normalize_unit(unit: str, canonical_unit: str = "") -> str:
    """
    Normalizes OCR unit text (e.g. 'mgldl' -> 'mg/dL', 'mg\\hg' -> 'mg/hg', 'mg/kl' -> 'mg/kl').
    Specifically handles OCR misreadings where '/' is scanned as 'l', '1', 'I',
    '\\', '.', '|', '-', or spaces.
    """
    if not unit:
        return canonical_unit or ""

    u = unit.strip()

    # If canonical_unit is present and matches when separators are normalized to '/',
    # use canonical casing directly (e.g. 'mg/dL' from medical_master)
    if canonical_unit:
        norm_u = re.sub(r'[\s/\\|.:_-]+|[lI1](?=[A-Za-z])', '/', u.lower())
        norm_c = re.sub(r'[\s/\\|.:_-]+', '/', canonical_unit.lower())
        if norm_u == norm_c:
            return canonical_unit

    # Check for mg prefix specifically as requested by user
    # Handles mgldl -> mg/dL, mg\hg -> mg/hg, mg/kl -> mg/kl, mg.dl -> mg/dL, etc.
    mg_match = re.match(r'^(mg)(?:[\s/\\|.:_-]+|[lI1](?=[A-Za-z]))(?P<rest>[A-Za-z%µ0-9^]+)$', u, re.IGNORECASE)
    if mg_match:
        prefix = "mg"
        rest = mg_match.group("rest")
        combined = f"{prefix}/{rest}"
        if combined.lower() == "mg/dl":
            return "mg/dL"
        if combined.lower() == "mg/l":
            return "mg/L"
        return combined

    # Check for other multi-letter units like mcg, ng, pg, mmol, cells, gms, gm, g
    other_match = re.match(r'^(?P<prefix>mcg|µg|ug|ng|pg|mmol|cells|gms|gm|g)(?:[\s/\\|.:_-]+|[lI1](?=[A-Za-z]))(?P<rest>[A-Za-z%µ0-9^]+)$', u, re.IGNORECASE)
    if other_match:
        prefix = other_match.group("prefix")
        rest = other_match.group("rest")
        combined = f"{prefix}/{rest}"
        if combined.lower() in ["g/dl", "gm/dl", "gms/dl"]:
            return "g/dL"
        if combined.lower() == "ng/ml":
            return "ng/mL"
        if combined.lower() == "pg/ml":
            return "pg/mL"
        if combined.lower() == "mmol/l":
            return "mmol/L"
        return combined

    return u


def select_best_record(matched_records: List[Dict[str, Any]], gender_code: str, lookup_name: str) -> Optional[Dict[str, Any]]:
    """
    Selects the most suitable record from matched records in medical_master.
    Prioritizes:
    1. Records with defined normal and critical reference ranges (prevents empty records from shadowing).
    2. Exact patient gender match over generic/all.
    3. Exact parameter name match over synonym match.
    """
    if not matched_records:
        return None

    best_record = None
    best_score = -1

    for record in matched_records:
        rec_gender = str(record.get("gender", "")).strip().upper()
        # Must be gender compatible
        if rec_gender not in [gender_code, "BOTH", "ALL", "ANY", ""]:
            continue

        score = 0
        # Gender exact match
        if rec_gender == gender_code:
            score += 20
        elif rec_gender in ["BOTH", "ALL", "ANY", ""]:
            score += 10

        # Has defined reference ranges
        if record.get("normal_min") is not None or record.get("normal_max") is not None:
            score += 30
        if record.get("critical_min") is not None or record.get("critical_max") is not None:
            score += 15

        # Exact parameter name match
        if record.get("parameter", "").strip().lower() == lookup_name:
            score += 10

        if score > best_score:
            best_score = score
            best_record = record

    return best_record


def evaluate_parameter_condition(
    typed_val: Union[float, int],
    unit: str,
    norm_min: Optional[float],
    norm_max: Optional[float],
    crit_min: Optional[float],
    crit_max: Optional[float],
    ref_range: str
) -> Dict[str, Any]:
    """
    Evaluates the condition and risk of a medical parameter against reference ranges:
    - CRITICAL LOW: value < critical_min -> Urgent doctor checkup alert
    - CRITICAL HIGH: value > critical_max -> Urgent doctor checkup alert
    - LOW: value < normal_min
    - HIGH: value > normal_max
    - NORMAL: normal_min <= value <= normal_max
    """
    has_normal_range = (norm_min is not None or norm_max is not None)
    has_critical_range = (crit_min is not None or crit_max is not None)

    if not has_normal_range and not has_critical_range:
        return {
            "status": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "is_critical": False,
            "warning": None,
            "interpretation": f"Extracted value is {typed_val} {unit}. No reference range available in Medical Master."
        }

    numeric_val = float(typed_val)
    unit_str = f" {unit}" if unit else ""

    # 1. Critical Low Check
    if crit_min is not None and numeric_val < crit_min:
        return {
            "status": "CRITICAL LOW",
            "risk_level": "CRITICAL",
            "is_critical": True,
            "warning": "CRITICAL ALERT: Condition is very critical! Urgent checkup or consult doctor immediately.",
            "interpretation": (
                f"Value ({typed_val}{unit_str}) is critically below the critical threshold ({crit_min}{unit_str}). "
                f"Normal range is {ref_range}. Immediate medical checkup/doctor consultation is strongly advised!"
            )
        }

    # 2. Critical High Check
    if crit_max is not None and numeric_val > crit_max:
        return {
            "status": "CRITICAL HIGH",
            "risk_level": "CRITICAL",
            "is_critical": True,
            "warning": "CRITICAL ALERT: Condition is very critical! Urgent checkup or consult doctor immediately.",
            "interpretation": (
                f"Value ({typed_val}{unit_str}) is critically above the critical threshold ({crit_max}{unit_str}). "
                f"Normal range is {ref_range}. Immediate medical checkup/doctor consultation is strongly advised!"
            )
        }

    # 3. Normal Low Check
    if norm_min is not None and numeric_val < norm_min:
        return {
            "status": "LOW",
            "risk_level": "LOW",
            "is_critical": False,
            "warning": None,
            "interpretation": (
                f"Value ({typed_val}{unit_str}) is below the normal range ({ref_range}). "
                f"Routine follow-up medical consultation recommended."
            )
        }

    # 4. Normal High Check
    if norm_max is not None and numeric_val > norm_max:
        return {
            "status": "HIGH",
            "risk_level": "HIGH",
            "is_critical": False,
            "warning": None,
            "interpretation": (
                f"Value ({typed_val}{unit_str}) is above the normal range ({ref_range}). "
                f"Routine follow-up medical consultation recommended."
            )
        }

    # 5. Normal In-Range
    return {
        "status": "NORMAL",
        "risk_level": "NORMAL",
        "is_critical": False,
        "warning": None,
        "interpretation": f"Value ({typed_val}{unit_str}) is within normal physiological limits ({ref_range})."
    }


def generate_parameter_summary(parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates an aggregated summary of the extracted parameters, counts of
    normal/low/high/critical values, and a list of actionable critical alerts.
    """
    total = len(parameters)
    normal_cnt = sum(1 for p in parameters if p.get("status") == "NORMAL")
    low_cnt = sum(1 for p in parameters if p.get("status") == "LOW")
    high_cnt = sum(1 for p in parameters if p.get("status") == "HIGH")
    crit_low_cnt = sum(1 for p in parameters if p.get("status") == "CRITICAL LOW")
    crit_high_cnt = sum(1 for p in parameters if p.get("status") == "CRITICAL HIGH")
    critical_cnt = crit_low_cnt + crit_high_cnt
    unknown_cnt = sum(1 for p in parameters if p.get("status") == "UNKNOWN")

    critical_alerts = []
    for p in parameters:
        if p.get("is_critical"):
            critical_threshold = p.get("critical_min") if "LOW" in p.get("status", "") else p.get("critical_max")
            critical_alerts.append({
                "parameter": p.get("parameter"),
                "code": p.get("code"),
                "category": p.get("category"),
                "value": p.get("value"),
                "unit": p.get("unit"),
                "status": p.get("status"),
                "critical_threshold": critical_threshold,
                "warning": p.get("warning"),
                "message": (
                    f"{p.get('parameter')} is {p.get('status')} ({p.get('value')} {p.get('unit')})! "
                    f"Threshold breached: {critical_threshold} {p.get('unit')}. "
                    "Urgent doctor checkup recommended."
                )
            })

    if critical_cnt > 0:
        overall_risk = "CRITICAL"
        recommendation = (
            "URGENT: One or more medical parameters are in critical danger zones. "
            "Please consult a doctor or seek medical attention immediately."
        )
    elif (low_cnt + high_cnt) > 0:
        overall_risk = "ATTENTION_REQUIRED"
        recommendation = (
            "Some medical parameters are outside the normal reference range. "
            "A routine follow-up with your doctor is recommended."
        )
    elif normal_cnt > 0:
        overall_risk = "NORMAL"
        recommendation = "All detected medical parameters are within normal reference ranges."
    else:
        overall_risk = "UNKNOWN"
        recommendation = "No reference ranges could be matched for the detected parameters."

    return {
        "total_parameters_detected": total,
        "normal_count": normal_cnt,
        "low_count": low_cnt,
        "high_count": high_cnt,
        "critical_count": critical_cnt,
        "critical_low_count": crit_low_cnt,
        "critical_high_count": crit_high_cnt,
        "unknown_count": unknown_cnt,
        "critical_alerts": critical_alerts,
        "overall_health_risk": overall_risk,
        "recommendation": recommendation
    }


def extract_parameters(text: str, metadata: dict = None) -> list[dict]:
    """
    Extracts medical parameters from OCR text using a dictionary-based approach.
    It searches for the 665 parameters from master_list, extracts their values, 
    and uses medical_master to determine unit, reference range, exact data types,
    and condition status (Normal, Low, High, Critical Low, Critical High) based on gender.
    """
    results = []
    if not text:
        return results

    # Ensure metadata exists
    if metadata is None:
        metadata = {}

    # Get Gender from metadata (default to Male if unknown to prevent failing)
    gender = metadata.get("patient", {}).get("gender", "Male")
    if gender and str(gender).strip().lower() in ["f", "female", "women", "w"]:
        gender_code = "FEMALE"
    else:
        gender_code = "MALE"

    joined_text = re.sub(r'\s+', ' ', text)

    knowledge = load_knowledge_base()
    master_list = knowledge.get("master_list", [])
    medical_master = knowledge.get("medical_master", [])
    
    # Pre-build lookup for medical master by parameter name and synonym (lowercased)
    master_lookup: Dict[str, List[Dict[str, Any]]] = {}
    for record in medical_master:
        param_name = str(record["parameter"]).strip().lower()
        if param_name not in master_lookup:
            master_lookup[param_name] = []
        master_lookup[param_name].append(record)
        
        for syn in record.get("synonyms", []):
            syn_lower = str(syn).strip().lower()
            if syn_lower not in master_lookup:
                master_lookup[syn_lower] = []
            master_lookup[syn_lower].append(record)

    # Convert the 665 master_list parameters to a set for fast lookup and regex building
    # Also include their synonyms from medical_master for robust matching
    valid_params_set = set()
    
    def add_param(p):
        p = str(p).strip()
        if 0 < len(p.split()) <= 4:
            valid_params_set.add(re.escape(p))
            # Handle US/UK spelling for Hemo/Haemo
            if "hemo" in p.lower():
                valid_params_set.add(re.escape(p.lower().replace("hemo", "haemo")))

    for param in master_list:
        add_param(param)
        
        # Add synonyms if this parameter exists in our medical master
        for record in master_lookup.get(str(param).strip().lower(), []):
            for syn in record.get("synonyms", []):
                add_param(syn)
            
    if not valid_params_set:
        return results

    # Build a regex to search for any of the valid parameters
    valid_params = list(valid_params_set)
    # Sort by length descending to match longest phrase first (e.g. "Glucose Fasting" before "Glucose")
    valid_params.sort(key=len, reverse=True)
    
    # Followed by a separator (:, -, =, ->, etc) and then a number
    params_regex = r"\b(" + "|".join(valid_params) + r")\b"
    separator_regex = r"\s*[:,\-=>\s]*\s*(?:->|:->)?\s*"
    # A number (int or float) possibly prefixed by < or >
    value_regex = r"(?P<value>[<>]?\s*\d{1,6}(?:,\d{3})*(?:\.\d+)?)"
    # Followed by optional unit (supports slashes, dots, hyphens, backslashes common in OCR)
    unit_regex = r"(?:\s+(?P<unit>[A-Za-zµ%/\.\\|\-^]{1,15}))?"

    full_pattern = re.compile(
        params_regex + separator_regex + value_regex + unit_regex,
        re.IGNORECASE
    )

    extracted_names = set()

    for match in full_pattern.finditer(joined_text):
        param_name = match.group(1).strip()
        result_val = match.group("value").strip()
        unit = match.group("unit").strip() if match.group("unit") else ""
        
        # Deduplicate - if we already found this parameter, skip
        if param_name.lower() in extracted_names:
            continue
            
        extracted_names.add(param_name.lower())

        # Parse native data type (float for 7.5, int for 1500)
        typed_val = parse_typed_value(result_val)
        if not isinstance(typed_val, (int, float)):
            continue

        # Lookup in medical_master for ranges, units, and status
        # Normalize UK spelling back to US spelling for lookup
        lookup_name = param_name.lower()
        if "haemo" in lookup_name:
            lookup_name = lookup_name.replace("haemo", "hemo")

        matched_records = master_lookup.get(lookup_name, [])
        best_record = select_best_record(matched_records, gender_code, lookup_name)

        ref_range = ""
        norm_min = None
        norm_max = None
        crit_min = None
        crit_max = None
        code = ""
        category = ""
        description = ""
        
        if best_record:
            code = best_record.get("code", "")
            category = best_record.get("category", "")
            description = best_record.get("description", "")
                
            norm_min = best_record.get("normal_min")
            norm_max = best_record.get("normal_max")
            crit_min = best_record.get("critical_min")
            crit_max = best_record.get("critical_max")
            
            # Format reference range string
            if norm_min is not None and norm_max is not None:
                ref_range = f"{norm_min} - {norm_max}"
            elif norm_min is not None:
                ref_range = f"> {norm_min}"
            elif norm_max is not None:
                ref_range = f"< {norm_max}"

        canonical_unit = ""
        if best_record and best_record.get("unit"):
            canonical_unit = str(best_record["unit"]).strip()

        # Normalize unit (handles mgldl -> mg/dL, mg\hg -> mg/hg, mg/kl -> mg/kl, etc.)
        unit = normalize_unit(unit, canonical_unit)

        # Evaluate condition, risk level, critical alerts
        evaluation = evaluate_parameter_condition(
            typed_val=typed_val,
            unit=unit,
            norm_min=norm_min,
            norm_max=norm_max,
            crit_min=crit_min,
            crit_max=crit_max,
            ref_range=ref_range
        )

        results.append({
            "parameter": param_name,
            "code": code,
            "category": category,
            "value": typed_val,
            "raw_value": result_val,
            "data_type": type(typed_val).__name__,
            "unit": unit,
            "normal_min": norm_min,
            "normal_max": norm_max,
            "critical_min": crit_min,
            "critical_max": crit_max,
            "reference_range": ref_range,
            "status": evaluation["status"],
            "risk_level": evaluation["risk_level"],
            "is_critical": evaluation["is_critical"],
            "warning": evaluation["warning"],
            "interpretation": evaluation["interpretation"],
            "description": description
        })

    return results


if __name__ == "__main__":
    demo_text = "Haemoglobin : 7.5 g/dL, WBC: 1500 cells/uL, Platelets: 150000, Blood Sugar: 450 mg/dL"
    params = extract_parameters(demo_text, {"patient": {"gender": "Male"}})
    summary = generate_parameter_summary(params)
    import json
    print("PARAMETERS:")
    print(json.dumps(params, indent=2))
    print("\nSUMMARY:")
    print(json.dumps(summary, indent=2))

