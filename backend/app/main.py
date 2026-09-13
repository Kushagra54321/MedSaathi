from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
from typing import Optional
from dotenv import load_dotenv

# Load environment variables (from .env and backend/.env)
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from app.services.ocr_service import extract_text_from_pdf
from app.services.text_cleaner import clean_ocr_text
from app.services.medical_validator import validate_medical_document
from app.services.metadata_extractor import extract_metadata
from app.services.parameter_extractor import extract_parameters, generate_parameter_summary
from app.services.clinical_intelligence import analyze_clinical_insights
from app.services.summary_service import generate_bilingual_medical_summary
from app.services.pdf_service import generate_medical_pdf_report

app = FastAPI(title="MedSaathi API", description="AI Medical Assistant & Multilingual Report Engine")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend directory for easy serving
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

if os.path.exists(FRONTEND_DIR):
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.get("/")
def home():
    return {
        "message": "MedSaathi API is running",
        "frontend_ui": "/ui/",
        "version": "2.0 (Phase 2 Multilingual AI Engine)"
    }


@app.post("/uploadfile/")
async def upload_file(
    file: UploadFile = File(...),
    patient_name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    doctor_name: Optional[str] = Form(None),
    disease_symptoms: Optional[str] = Form(None),
    preferred_language: Optional[str] = Form("English")
):
    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/png"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG and PNG files are allowed."
        )
    
    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 1. OCR and Text Cleaning
    extracted_text = extract_text_from_pdf(file_path)
    cleaned_text = clean_ocr_text(extracted_text)
    
    # 2. Medical Document Validation
    validation = validate_medical_document(cleaned_text)

    user_provided_metadata = {
        "patient_name": patient_name,
        "age": age,
        "gender": gender,
        "doctor_name": doctor_name if doctor_name else "",
        "disease_symptoms": disease_symptoms if disease_symptoms else "",
        "preferred_language": preferred_language
    }

    if not validation["is_medical_document"]:
        return {
            "message": "Invalid document",
            "filename": file.filename,
            "validation": validation,
            "user_provided_metadata": user_provided_metadata,
            "error": "The uploaded file does not appear to be a medical document."
        }
    
    # 3. Metadata Extraction
    metadata = extract_metadata(cleaned_text)
    if "patient" not in metadata:
        metadata["patient"] = {}
    metadata["patient"]["name"] = patient_name
    metadata["patient"]["age"] = age
    metadata["patient"]["gender"] = gender
    
    if "doctor" not in metadata:
        metadata["doctor"] = {}
    metadata["doctor"]["name"] = doctor_name if doctor_name else ""
    
    # 4. Phase 1: Parameter Extraction & Evaluation
    parameters = extract_parameters(cleaned_text, metadata)
    summary_stats = generate_parameter_summary(parameters)

    # 5. Phase 2: Clinical Intelligence (Disease Mapping & Medical Terms)
    clinical_insights = analyze_clinical_insights(
        parameters=parameters,
        user_symptoms=disease_symptoms if disease_symptoms else ""
    )

    # 6. Phase 2: Bilingual Plain Language Medical Summary
    patient_meta_for_summary = {
        "name": patient_name,
        "age": age,
        "gender": gender,
        "doctor": doctor_name if doctor_name else "Consultant Physician",
        "disease_symptoms": disease_symptoms if disease_symptoms else ""
    }

    bilingual_summary = generate_bilingual_medical_summary(
        patient_meta=patient_meta_for_summary,
        parameters=parameters,
        clinical_insights=clinical_insights,
        summary_stats=summary_stats,
        preferred_language=preferred_language
    )

    # 7. Phase 2: PDF Report Generation (Both English & Native Language!)
    report_id = uuid.uuid4().hex[:12]
    
    # 7a. Generate English PDF
    pdf_path_en = generate_medical_pdf_report(
        report_id=report_id,
        patient_meta=patient_meta_for_summary,
        parameters=parameters,
        summary_text=bilingual_summary["summary_english"],
        risk_level=summary_stats.get("overall_health_risk", "NORMAL"),
        language_label="English",
        lang_code="en"
    )

    # 7b. Generate Native Language PDF (if preferred language is not English)
    has_native_pdf = False
    if bilingual_summary.get("language_code") != "en":
        try:
            generate_medical_pdf_report(
                report_id=report_id,
                patient_meta=patient_meta_for_summary,
                parameters=parameters,
                summary_text=bilingual_summary["summary_native"],
                risk_level=summary_stats.get("overall_health_risk", "NORMAL"),
                language_label=bilingual_summary["preferred_language"],
                lang_code="native"
            )
            has_native_pdf = True
        except Exception as e:
            print(f"[WARNING] Failed to generate native PDF ({e})")

    return {
        "message": "Medical document validated and analyzed successfully",
        "filename": file.filename,
        "report_id": report_id,
        "pdf_download_url": f"/download-pdf/{report_id}?lang=en",
        "pdf_download_url_english": f"/download-pdf/{report_id}?lang=en",
        "pdf_download_url_native": f"/download-pdf/{report_id}?lang=native" if has_native_pdf else f"/download-pdf/{report_id}?lang=en",
        "validation": validation,
        "user_provided_metadata": user_provided_metadata,
        "metadata": metadata,
        "medical_parameters": parameters,
        "parameter_summary": summary_stats,
        "clinical_insights": clinical_insights,
        "bilingual_summary": bilingual_summary,
        "extracted_text": cleaned_text
    }


@app.get("/download-pdf/{report_id}")
async def download_pdf(report_id: str, lang: Optional[str] = "en"):
    """Allows patient or doctor to download either English or Native Language PDF report."""
    lang_lower = (lang or "en").lower().strip()
    
    # Check if native language PDF requested
    if lang_lower in ["native", "hi", "mr", "pa", "gu", "bn", "te", "ta", "kn", "ml"]:
        pdf_filename = f"MedSaathi_Report_{report_id}_native.pdf"
        pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
        if os.path.exists(pdf_path):
            return FileResponse(
                pdf_path,
                media_type="application/pdf",
                filename=f"MedSaathi_Medical_Report_{report_id}_Native.pdf"
            )

    # English / Standard PDF
    pdf_filename_en = f"MedSaathi_Report_{report_id}_en.pdf"
    pdf_path_en = os.path.join(REPORTS_DIR, pdf_filename_en)
    if os.path.exists(pdf_path_en):
        return FileResponse(
            pdf_path_en,
            media_type="application/pdf",
            filename=f"MedSaathi_Medical_Report_{report_id}_English.pdf"
        )

    # Legacy fallback
    legacy_path = os.path.join(REPORTS_DIR, f"MedSaathi_Report_{report_id}.pdf")
    if os.path.exists(legacy_path):
        return FileResponse(
            legacy_path,
            media_type="application/pdf",
            filename=f"MedSaathi_Medical_Report_{report_id}.pdf"
        )

    raise HTTPException(status_code=404, detail="Report PDF not found")
