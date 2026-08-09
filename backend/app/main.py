from fastapi import FastAPI, UploadFile, File , HTTPException
import shutil
import os
from app.services.ocr_service import extract_text_from_pdf

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
    
    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        # "saved_path": file_path,
        "extracted_text": extracted_text
    }
