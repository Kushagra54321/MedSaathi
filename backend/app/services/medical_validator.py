import re

from app.services.knowledge_loader import load_knowledge_base


# ---------------------------------------------------------
# BASIC TEXT HELPERS
# ---------------------------------------------------------

def normalize_text(text: str) -> str:
    """Normalize OCR text for matching."""
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def safe_regex_search(pattern: str, text: str) -> bool:
    """Safely test a regex pattern from the knowledge base."""

    if not pattern:
        return False

    try:
        return re.search(
            pattern,
            text,
            re.IGNORECASE
        ) is not None

    except re.error:
        print(
            f"[WARNING] Invalid regex skipped: {pattern}"
        )
        return False


def keyword_exists(keyword: str, text: str) -> bool:
    """
    Match a keyword using word boundaries.

    This prevents short terms such as AST from matching
    inside unrelated words.
    """

    if not keyword:
        return False

    keyword = keyword.strip()

    if len(keyword) <= 2:
        # Very short medical abbreviations should not be
        # treated as standalone evidence unless a value/unit
        # is also found around them.
        return False

    pattern = (
        r"(?<![A-Za-z0-9])"
        + re.escape(keyword)
        + r"(?![A-Za-z0-9])"
    )

    return re.search(
        pattern,
        text,
        re.IGNORECASE
    ) is not None


# ---------------------------------------------------------
# VALUE / UNIT DETECTION
# ---------------------------------------------------------

NUMBER_PATTERN = r"""
    [-+]?
    (?:
        \d+(?:\.\d+)?
        |
        \.\d+
    )
"""


def find_nearby_value(text: str, keyword: str) -> bool:
    """
    Check whether a numeric value appears near a medical
    parameter.

    Examples:
        Hemoglobin 11.2
        WBC: 7200
        Glucose = 96 mg/dL
    """

    if not keyword:
        return False

    escaped = re.escape(keyword)

    pattern = (
        rf"(?<![A-Za-z0-9])"
        rf"{escaped}"
        rf"(?![A-Za-z0-9])"
        rf".{{0,40}}?"
        rf"[:=\-]?\s*"
        rf"{NUMBER_PATTERN}"
    )

    try:
        return re.search(
            pattern,
            text,
            re.IGNORECASE | re.VERBOSE
        ) is not None

    except re.error:
        return False


def find_nearby_unit(
    text: str,
    keyword: str,
    unit: str
) -> bool:
    """
    Check whether the expected unit appears close to
    the parameter.

    Example:
        Hemoglobin 11.2 g/dL
    """

    if not keyword or not unit:
        return False

    escaped_keyword = re.escape(keyword)
    escaped_unit = re.escape(unit)

    pattern = (
        rf"(?<![A-Za-z0-9])"
        rf"{escaped_keyword}"
        rf"(?![A-Za-z0-9])"
        rf".{{0,60}}?"
        rf"{escaped_unit}"
    )

    try:
        return re.search(
            pattern,
            text,
            re.IGNORECASE
        ) is not None

    except re.error:
        return False


def parameter_has_value_or_unit(
    text: str,
    parameter: str,
    synonyms: list,
    unit: str
) -> bool:
    """
    Test the parameter, its synonyms, and its unit.

    We intentionally require stronger evidence for very
    short abbreviations such as AST, ALP, pH, etc.
    """

    candidates = []

    if parameter:
        candidates.append(parameter)

    candidates.extend(synonyms or [])

    for candidate in candidates:

        if not candidate:
            continue

        candidate = candidate.strip()

        # For short abbreviations, require numeric value
        # or expected unit nearby.
        if len(candidate) <= 3:

            if find_nearby_value(
                text,
                candidate
            ):
                return True

            if find_nearby_unit(
                text,
                candidate,
                unit
            ):
                return True

        else:

            if find_nearby_value(
                text,
                candidate
            ):
                return True

            if find_nearby_unit(
                text,
                candidate,
                unit
            ):
                return True

    return False


# ---------------------------------------------------------
# MEDICAL PARAMETER MATCHING
# ---------------------------------------------------------

def match_medical_parameters(
    text: str,
    knowledge: dict
):
    """
    Match medical_master records.

    A parameter becomes strong evidence when:
      1. Parameter/synonym is present AND
      2. A value or expected unit is nearby.

    A regex match alone is not enough for validation.
    """

    matches = []

    for record in knowledge["medical_master"]:

        parameter = record.get(
            "parameter",
            ""
        )

        synonyms = record.get(
            "synonyms",
            []
        )

        regex_pattern = record.get(
            "regex_pattern",
            ""
        )

        unit = record.get(
            "unit",
            ""
        )

        parameter_found = False

        # ---------------------------------------------
        # Parameter / synonym matching
        # ---------------------------------------------

        if keyword_exists(
            parameter,
            text
        ):
            parameter_found = True

        if not parameter_found:

            for synonym in synonyms:

                if keyword_exists(
                    synonym,
                    text
                ):
                    parameter_found = True
                    break

        # ---------------------------------------------
        # Regex matching
        # ---------------------------------------------

        regex_found = safe_regex_search(
            regex_pattern,
            text
        )

        # ---------------------------------------------
        # Strong evidence:
        # parameter + value/unit
        # ---------------------------------------------

        strong_match = False

        if parameter_found:

            strong_match = parameter_has_value_or_unit(
                text,
                parameter,
                synonyms,
                unit
            )

        # Regex is supporting evidence only.
        # Do NOT accept regex alone.
        if strong_match:

            matches.append({
                "code": record.get("code", ""),
                "parameter": parameter,
                "category": record.get(
                    "category",
                    ""
                ),
                "unit": unit,
                "priority": record.get(
                    "priority",
                    ""
                ),
                "evidence": "parameter + value/unit"
            })

        elif (
            parameter_found
            and regex_found
            and unit
            and find_nearby_unit(
                text,
                parameter,
                unit
            )
        ):

            matches.append({
                "code": record.get("code", ""),
                "parameter": parameter,
                "category": record.get(
                    "category",
                    ""
                ),
                "unit": unit,
                "priority": record.get(
                    "priority",
                    ""
                ),
                "evidence": "parameter + regex + unit"
            })

    return matches


# ---------------------------------------------------------
# HEALTHCARE SERVICE MATCHING
# ---------------------------------------------------------

def match_healthcare_services(
    text: str,
    knowledge: dict
):
    """
    Detect services such as:
        MRI
        CT Scan
        X-Ray
        Ultrasound
        ECG

    Service matches are strong evidence because these
    are medical/diagnostic concepts.
    """

    matches = []

    for record in knowledge[
        "healthcare_services"
    ]:

        service_name = record.get(
            "service_name",
            ""
        )

        keyword = record.get(
            "keyword",
            ""
        )

        synonyms = record.get(
            "synonyms",
            []
        )

        found = False
        matched_by = ""

        candidates = []

        if service_name:
            candidates.append(
                (
                    service_name,
                    "service name"
                )
            )

        if keyword:
            candidates.append(
                (
                    keyword,
                    "keyword"
                )
            )

        for synonym in synonyms:
            candidates.append(
                (
                    synonym,
                    "synonym"
                )
            )

        for candidate, source in candidates:

            if keyword_exists(
                candidate,
                text
            ):
                found = True
                matched_by = source
                break

            # Short service names such as MRI/CT/ECG
            # require a safer standalone regex.
            if len(candidate.strip()) <= 3:

                pattern = (
                    r"(?<![A-Za-z0-9])"
                    + re.escape(candidate.strip())
                    + r"(?![A-Za-z0-9])"
                )

                if re.search(
                    pattern,
                    text,
                    re.IGNORECASE
                ):
                    found = True
                    matched_by = source
                    break

        if found:

            matches.append({
                "service_id": record.get(
                    "service_id",
                    ""
                ),
                "service_name": service_name,
                "category": record.get(
                    "category",
                    ""
                ),
                "matched_by": matched_by
            })

    return matches


# ---------------------------------------------------------
# MEDICAL TERM MATCHING
# ---------------------------------------------------------

def match_medical_terms(
    text: str,
    knowledge: dict
):
    """
    Medical terms provide supporting evidence.
    They are not enough by themselves to validate a
    document.
    """

    matches = []

    for record in knowledge[
        "medical_terms"
    ]:

        term = record.get(
            "medical_term",
            ""
        )

        if keyword_exists(
            term,
            text
        ):

            matches.append({
                "term_id": record.get(
                    "term_id",
                    ""
                ),
                "medical_term": term
            })

    return matches


# ---------------------------------------------------------
# PATIENT / HOSPITAL METADATA
# ---------------------------------------------------------

def match_metadata(
    text: str,
    knowledge: dict
):
    """
    Metadata is supporting information only.

    Email, phone, technology, etc. are NOT counted as
    medical evidence by themselves.
    """

    matches = []

    # These fields can appear in resumes/CVs, so they
    # should never validate a document.
    ignored_validation_fields = {
        "patient.phone",
        "patient.email",
        "hospital.phone",
        "hospital.email",
        "test.technology"
    }

    for record in knowledge[
        "hospital_patient_keywords"
    ]:

        keyword = record.get(
            "keyword",
            ""
        )

        standard_field = record.get(
            "standard_field",
            ""
        )

        synonyms = record.get(
            "synonyms",
            []
        )

        regex_pattern = record.get(
            "regex_pattern",
            ""
        )

        found = False

        # Regex can identify metadata, but it is only
        # supporting information.
        if safe_regex_search(
            regex_pattern,
            text
        ):
            found = True

        if not found and keyword_exists(
            keyword,
            text
        ):
            found = True

        if not found:

            for synonym in synonyms:

                if keyword_exists(
                    synonym,
                    text
                ):
                    found = True
                    break

        if found:

            matches.append({
                "keyword_id": record.get(
                    "keyword_id",
                    ""
                ),
                "keyword": keyword,
                "standard_field": standard_field,
                "data_type": record.get(
                    "data_type",
                    ""
                ),
                "validation_weight": (
                    0
                    if standard_field
                    in ignored_validation_fields
                    else 0.5
                )
            })

    return matches


# ---------------------------------------------------------
# DOCUMENT VALIDATION
# ---------------------------------------------------------

def validate_medical_document(
    text: str
) -> dict:

    if not text:

        return {
            "is_medical_document": False,
            "score": 0,
            "matched_parameters": [],
            "matched_terms": [],
            "matched_services": [],
            "matched_metadata": [],
            "message": (
                "No text could be extracted "
                "from the document."
            )
        }

    text = normalize_text(text)

    knowledge = load_knowledge_base()

    # -----------------------------------------------------
    # MATCH DIFFERENT EVIDENCE TYPES
    # -----------------------------------------------------

    matched_parameters = match_medical_parameters(
        text,
        knowledge
    )

    matched_services = match_healthcare_services(
        text,
        knowledge
    )

    matched_terms = match_medical_terms(
        text,
        knowledge
    )

    matched_metadata = match_metadata(
        text,
        knowledge
    )

    # -----------------------------------------------------
    # SCORING
    # -----------------------------------------------------

    parameter_score = (
        len(matched_parameters) * 3
    )

    service_score = (
        len(matched_services) * 3
    )

    # Medical terms are supporting evidence.
    term_score = min(
        len(matched_terms) * 1,
        4
    )

    metadata_score = sum(
        item.get(
            "validation_weight",
            0
        )
        for item in matched_metadata
    )

    score = (
        parameter_score
        + service_score
        + term_score
        + metadata_score
    )

    # -----------------------------------------------------
    # VALIDATION RULE
    # -----------------------------------------------------
    #
    # Strong medical evidence:
    #
    # 1+ medical parameter with value/unit
    # OR
    # 1+ healthcare diagnostic service
    #
    # Metadata alone cannot validate a document.
    # -----------------------------------------------------

    has_strong_parameter = (
        len(matched_parameters) >= 1
    )

    has_strong_service = (
        len(matched_services) >= 1
    )

    is_medical = (
        has_strong_parameter
        or has_strong_service
    )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    if is_medical:

        message = (
            "Medical document validated successfully."
        )

    else:

        message = (
            "The uploaded file does not appear "
            "to be a medical report, prescription, "
            "diagnostic report, or healthcare document."
        )

    return {

        "is_medical_document": is_medical,

        "score": round(score, 2),

        "matched_parameters":
            matched_parameters,

        "matched_terms":
            matched_terms,

        "matched_services":
            matched_services,

        "matched_metadata":
            matched_metadata,

        "message": message
    } 