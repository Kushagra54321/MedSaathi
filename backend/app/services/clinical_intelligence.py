import re
from typing import List, Dict, Any, Optional
from functools import lru_cache
from app.services.knowledge_loader import read_excel, load_knowledge_base


@lru_cache(maxsize=1)
def load_disease_mapping() -> List[Dict[str, Any]]:
    """Loads and caches disease_mapping.xlsx records."""
    df = read_excel("disease_mapping.xlsx")
    records = []
    if df.empty:
        return records

    for _, row in df.iterrows():
        param = str(row.get("Parameter", "")).strip()
        status = str(row.get("Status", "")).strip()
        condition = str(row.get("Possible_Condition", "")).strip()
        if param and condition:
            records.append({
                "disease_id": str(row.get("Disease_ID", "")).strip(),
                "parameter": param,
                "status": status,
                "possible_condition": condition,
                "severity": str(row.get("Severity", "Medium")).strip(),
                "recommendation": str(row.get("Recommendation", "")).strip(),
                "emergency": str(row.get("Emergency", "No")).strip().lower() in ["yes", "y", "true", "1"],
                "notes": str(row.get("Notes", "")).strip()
            })
    return records


def _match_term(param_name: str, target: str) -> bool:
    """Checks if param_name matches target phrase or abbreviation."""
    p = param_name.lower().replace("haemo", "hemo").strip()
    t = target.lower().replace("haemo", "hemo").strip()
    if p == t or p in t or t in p:
        return True
    
    # Check words inside parentheses e.g. "Hemoglobin (Hb)" matching "Hb" or "Hemoglobin"
    parens = re.findall(r'\((.*?)\)', t)
    for part in parens:
        if p == part.strip().lower():
            return True
            
    base_t = re.sub(r'\(.*?\)', '', t).strip()
    if p == base_t or p in base_t or base_t in p:
        return True
        
    return False


def _status_matches(param_status: str, record_status: str) -> bool:
    """Matches parameter status against disease mapping status."""
    ps = param_status.upper().strip()
    rs = record_status.upper().strip()

    if ps == rs:
        return True
    if "CRITICAL LOW" in ps and ("LOW" in rs or "CRITICAL" in rs):
        return True
    if "CRITICAL HIGH" in ps and ("HIGH" in rs or "CRITICAL" in rs):
        return True
    if "LOW" in ps and "LOW" in rs:
        return True
    if "HIGH" in ps and "HIGH" in rs:
        return True
    return False


def analyze_clinical_insights(parameters: List[Dict[str, Any]], user_symptoms: str = "") -> Dict[str, Any]:
    """
    Analyzes extracted medical parameters against disease_mapping.xlsx (2,812 rows)
    and medical_terms.xlsx (590 rows) to produce clinical findings, dietary suggestions,
    lifestyle advice, and doctor consultation checklists.
    """
    disease_records = load_disease_mapping()
    kb = load_knowledge_base()
    term_records = kb.get("medical_terms", [])

    abnormal_parameters = [
        p for p in parameters if p.get("status") in ["LOW", "HIGH", "CRITICAL LOW", "CRITICAL HIGH"]
    ]

    parameter_insights = []
    dietary_tips = set()
    lifestyle_tips = set()
    recommended_tests = set()
    possible_conditions_all = []
    emergency_alerts = []

    user_symptom_tokens = set(re.findall(r'\b[A-Za-z]{3,}\b', user_symptoms.lower())) if user_symptoms else set()

    for p in abnormal_parameters:
        param_name = p.get("parameter", "")
        param_status = p.get("status", "")
        param_val = p.get("value")
        param_unit = p.get("unit", "")
        is_crit = p.get("is_critical", False)

        # 1. Match in disease_mapping.xlsx
        matched_diseases = []
        for d in disease_records:
            if _match_term(param_name, d["parameter"]) and _status_matches(param_status, d["status"]):
                matched_diseases.append(d)

        # 2. Match in medical_terms.xlsx
        matched_term = None
        for t in term_records:
            t_name = t.get("medical_term", "")
            if _match_term(param_name, t_name):
                matched_term = t
                break

        # Extract explanations
        simple_meaning = matched_term.get("simple_meaning", "") if matched_term else ""
        why_important = matched_term.get("why_important", "") if matched_term else ""
        common_symptoms = matched_term.get("common_symptoms", "") if matched_term else ""
        
        effects = ""
        if matched_term:
            if "LOW" in param_status:
                effects = matched_term.get("effects_low", "")
            elif "HIGH" in param_status:
                effects = matched_term.get("effects_high", "")

        # Dietary and lifestyle suggestions from medical_terms
        if matched_term:
            if matched_term.get("dietary_suggestions"):
                dietary_tips.add(matched_term["dietary_suggestions"])
            if matched_term.get("lifestyle_advice"):
                lifestyle_tips.add(matched_term["lifestyle_advice"])

        # Check for symptom correlation
        symptom_correlated = False
        if user_symptom_tokens and common_symptoms:
            common_tokens = set(re.findall(r'\b[A-Za-z]{3,}\b', common_symptoms.lower()))
            if user_symptom_tokens.intersection(common_tokens):
                symptom_correlated = True

        # Process disease conditions
        conditions_list = []
        for d in matched_diseases[:4]:  # Top 4 relevant conditions
            cond_name = d["possible_condition"]
            severity = d["severity"]
            rec = d["recommendation"]
            is_emerg = d["emergency"]

            conditions_list.append({
                "condition": cond_name,
                "severity": severity,
                "recommendation": rec,
                "is_emergency": is_emerg
            })
            possible_conditions_all.append(cond_name)

            if rec:
                recommended_tests.add(rec)
            if is_emerg or is_crit:
                emergency_alerts.append(f"{param_name} ({param_val} {param_unit}): Risk of {cond_name} - Requires urgent evaluation!")

        parameter_insights.append({
            "parameter": param_name,
            "status": param_status,
            "value": param_val,
            "unit": param_unit,
            "reference_range": p.get("reference_range", ""),
            "is_critical": is_crit,
            "simple_meaning": simple_meaning,
            "why_important": why_important,
            "possible_effects": effects,
            "common_symptoms": common_symptoms,
            "symptom_correlated": symptom_correlated,
            "possible_conditions": conditions_list
        })

    # Prepare targeted questions for doctor consultation
    doctor_questions = []
    if abnormal_parameters:
        for p in abnormal_parameters[:3]:
            doctor_questions.append(
                f"My {p.get('parameter')} is {p.get('status').lower()} ({p.get('value')} {p.get('unit')}). What underlying cause should we investigate?"
            )
        if recommended_tests:
            first_test = list(recommended_tests)[0]
            doctor_questions.append(f"Should I undergo follow-up tests such as {first_test}?")
        doctor_questions.append("Are there any specific dietary or medication changes I should start immediately?")

    # Default general wellness tips if empty
    if not dietary_tips:
        dietary_tips.add("Maintain a balanced diet rich in leafy vegetables, fresh fruits, adequate hydration, and whole grains.")
    if not lifestyle_tips:
        lifestyle_tips.add("Ensure 7-8 hours of sound sleep, moderate physical activity, and stress management.")

    return {
        "abnormal_parameter_count": len(abnormal_parameters),
        "parameter_insights": parameter_insights,
        "possible_conditions": list(dict.fromkeys(possible_conditions_all))[:8],
        "emergency_alerts": list(dict.fromkeys(emergency_alerts)),
        "dietary_guidelines": list(dietary_tips)[:4],
        "lifestyle_guidelines": list(lifestyle_tips)[:4],
        "recommended_next_tests": list(recommended_tests)[:5],
        "doctor_questions": doctor_questions
    }
