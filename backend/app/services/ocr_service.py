import numpy as np
import easyocr
from pdf2image import convert_from_path

reader = easyocr.Reader(["en"])

def extract_text_from_pdf(pdf_path: str) -> str:

#     images = convert_from_path(
#     pdf_path,
#     poppler_path=r"C:\poppler\poppler-26.02.0\Library\bin"
# )
    POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"

    images = convert_from_path(
        pdf_path,
        poppler_path=POPPLER_PATH,
    )

    full_text = ""

    for image in images:
        result = reader.readtext(np.array(image))
        for detection in result:
            full_text += detection[1] + "\n"

    return full_text