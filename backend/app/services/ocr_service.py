import numpy as np
import easyocr
from pdf2image import convert_from_path

reader = easyocr.Reader(["en"])

POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"


def extract_text_from_pdf(pdf_path: str) -> str:

    images = convert_from_path(
        pdf_path,
        dpi=200,
        poppler_path=POPPLER_PATH
    )

    full_text = []

    for image in images:

        result = reader.readtext(np.array(image))

        for detection in result:

            text = detection[1].strip()

            if text:
                full_text.append(text)

    return "\n".join(full_text)



# import numpy as np
# import easyocr
# from pdf2image import convert_from_path

# reader = easyocr.Reader(["en"])

# def extract_text_from_pdf(pdf_path: str) -> str:

# #     images = convert_from_path(
# #     pdf_path,
# #     poppler_path=r"C:\poppler\poppler-26.02.0\Library\bin"
# # )
#     POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"

#     images = convert_from_path(
#         pdf_path,
#         poppler_path=POPPLER_PATH,
#     )

#     full_text = ""

#     for image in images:
#         result = reader.readtext(np.array(image))
#         for detection in result:
#             full_text += detection[1] + "\n"

#     return full_text