from fastapi import FastAPI, UploadFile, File , HTTPException
import shutil
import os
from app.services.ocr_service import extract_text_from_pdf
from app.services.text_cleaner import clean_ocr_text
from app.services.medical_validator import validate_medical_document

app = FastAPI()

@app.get("/")

def home():
    return {"message": "MedSaathi API is running"}
    
@app.post("/uploadfile/")

async def upload_file(file: UploadFile = File(...)):

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
    
    extracted_text = extract_text_from_pdf(file_path)
    cleaned_text = clean_ocr_text(extracted_text)
    validation = validate_medical_document(cleaned_text)

    if not validation["is_medical_document"]:

        return {
        "message": "Invalid document",
        "filename": file.filename,
        "validation": validation,
        "error": "The uploaded file does not appear to be a medical document."
    }
    
    return {
    "message": "Medical document validated successfully",
    "filename": file.filename,
    "validation": validation,
    "extracted_text": cleaned_text
    }

    # return {
    #     "message": "File uploaded successfully",
    #     "filename": file.filename,
    #     # "saved_path": file_path,
    #     "extracted_text": cleaned_text
    #     # "extracted_lines": cleaned_text.splitlines()
    # }
