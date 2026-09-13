import numpy as np
import easyocr
from pdf2image import convert_from_path

reader = easyocr.Reader(["en"])

POPPLER_PATH = r"C:\poppler\poppler-26.02.0\Library\bin"


def extract_text_from_pdf(pdf_path: str) -> str:
    lower_path = pdf_path.lower()
    if lower_path.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
        from PIL import Image
        images = [Image.open(pdf_path).convert("RGB")]
    else:
        images = convert_from_path(
            pdf_path,
            dpi=200,
            poppler_path=POPPLER_PATH
        )

    full_text = []

    for image in images:
        result = reader.readtext(np.array(image))
        
        # result format: [ ( [[x,y], [x,y], [x,y], [x,y]], text, conf ), ... ]
        # We need to sort by Y first (with a tolerance to group same lines), then X.
        
        boxes = []
        for det in result:
            bbox, text, conf = det
            if not text.strip():
                continue
                
            # Calculate center Y and min X
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
            
        # Sort by Y, but group into lines if Y difference is less than 50% of text height
        boxes.sort(key=lambda b: b["center_y"])
        
        lines = []
        current_line = []
        
        for box in boxes:
            if not current_line:
                current_line.append(box)
                continue
                
            # If the box is vertically close to the current line, add it to the same line
            avg_height = sum(b["height"] for b in current_line) / len(current_line)
            y_diff = abs(box["center_y"] - current_line[-1]["center_y"])
            
            if y_diff < avg_height * 0.6:  # Tolerance threshold
                current_line.append(box)
            else:
                lines.append(current_line)
                current_line = [box]
                
        if current_line:
            lines.append(current_line)
            
        # Sort each line by X and join with spaces
        for line in lines:
            line.sort(key=lambda b: b["min_x"])
            full_text.append(" ".join(b["text"] for b in line))

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