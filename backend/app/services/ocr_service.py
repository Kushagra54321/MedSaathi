import os
import sys
import logging

logger = logging.getLogger(__name__)

# POPPLER path configuration for local Windows
DEFAULT_WINDOWS_POPPLER = r"C:\poppler\poppler-26.02.0\Library\bin"
POPPLER_PATH = DEFAULT_WINDOWS_POPPLER if (os.name == "nt" and os.path.exists(DEFAULT_WINDOWS_POPPLER)) else None

# Lazy EasyOCR reader instance
_easyocr_reader = None


def get_easyocr_reader():
    """Lazily load easyocr reader only when requested, saving memory and avoiding startup crashes."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(["en"], gpu=False)
        except Exception as e:
            logger.warning(f"EasyOCR could not be initialized or is not installed: {e}")
            _easyocr_reader = False
    return _easyocr_reader if _easyocr_reader is not False else None


def extract_with_gemini_vision(file_path: str) -> str:
    """Fallback OCR using Gemini Vision if local OCR is unavailable (e.g. on cloud platforms)."""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return ""
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        lower = file_path.lower()
        if lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
            from PIL import Image
            img = Image.open(file_path)
            prompt = "Extract all text, medical test names, numerical values, units, and reference ranges from this medical document exactly as presented. Keep the format clean and readable."
            response = model.generate_content([prompt, img])
            return response.text if response and response.text else ""
        elif lower.endswith(".pdf"):
            uploaded = genai.upload_file(path=file_path)
            prompt = "Extract all text, patient details, lab test results, numerical values, and reference ranges from this medical report exactly as presented."
            response = model.generate_content([uploaded, prompt])
            return response.text if response and response.text else ""
    except Exception as e:
        logger.error(f"Gemini Vision extraction failed: {e}")
    return ""


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from medical documents (PDF or images).
    Strategy:
    1. For PDFs: Use PyMuPDF (fitz) or pdfplumber for fast, 100% accurate native text extraction.
    2. If PDF has no text layer (scanned) or file is an image:
       - Use EasyOCR if available.
       - If EasyOCR is unavailable or fails, fallback to Gemini Vision.
    """
    lower_path = pdf_path.lower()
    is_image = lower_path.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp"))

    # 1. If it's a PDF, first attempt fast native extraction via PyMuPDF / pdfplumber
    if not is_image:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            pages_text = [page.get_text() for page in doc]
            full_pdf_text = "\n".join(pages_text).strip()
            if len(full_pdf_text) > 40:
                return full_pdf_text
        except Exception as e:
            logger.warning(f"PyMuPDF native extraction failed: {e}")

        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = [page.extract_text() or "" for page in pdf.pages]
                full_pdf_text = "\n".join(pages_text).strip()
                if len(full_pdf_text) > 40:
                    return full_pdf_text
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")

    # 2. If it's an image or a scanned PDF, try EasyOCR
    reader = get_easyocr_reader()
    if reader is not None:
        try:
            import numpy as np
            images = []
            if is_image:
                from PIL import Image
                images = [Image.open(pdf_path).convert("RGB")]
            else:
                from pdf2image import convert_from_path
                kwargs = {"dpi": 200}
                if POPPLER_PATH and os.path.exists(POPPLER_PATH):
                    kwargs["poppler_path"] = POPPLER_PATH
                images = convert_from_path(pdf_path, **kwargs)

            full_text = []
            for image in images:
                result = reader.readtext(np.array(image))
                boxes = []
                for det in result:
                    bbox, text, conf = det
                    if not text.strip():
                        continue
                    min_y = min([pt[1] for pt in bbox])
                    max_y = max([pt[1] for pt in bbox])
                    center_y = (min_y + max_y) / 2
                    min_x = min([pt[0] for pt in bbox])
                    height = max_y - min_y
                    boxes.append({
                        "text": text.strip(),
                        "center_y": center_y,
                        "min_x": min_x,
                        "height": height
                    })

                boxes.sort(key=lambda b: b["center_y"])
                lines = []
                current_line = []
                for box in boxes:
                    if not current_line:
                        current_line.append(box)
                        continue
                    avg_height = sum(b["height"] for b in current_line) / len(current_line)
                    y_diff = abs(box["center_y"] - current_line[-1]["center_y"])
                    if y_diff < avg_height * 0.6:
                        current_line.append(box)
                    else:
                        lines.append(current_line)
                        current_line = [box]
                if current_line:
                    lines.append(current_line)

                for line in lines:
                    line.sort(key=lambda b: b["min_x"])
                    full_text.append(" ".join(b["text"] for b in line))

            ocr_res = "\n".join(full_text).strip()
            if len(ocr_res) > 20:
                return ocr_res
        except Exception as e:
            logger.warning(f"EasyOCR extraction failed: {e}")

    # 3. Fallback: Gemini Vision OCR (cloud and scanned document resilient)
    gemini_text = extract_with_gemini_vision(pdf_path)
    if gemini_text:
        return gemini_text

    return ""