# MedSaathi - AI Medical Assistant 🩺

An intelligent medical assistant designed to streamline clinical workflows by extracting, analyzing, and summarizing information from medical documents. Powered by advanced OCR and Large Language Models (LLMs), MedSaathi helps medical professionals process clinical data with speed and accuracy.

---

## 🌟 Key Features

- **Medical Document OCR**: Accurately extracts text from medical reports, prescriptions, and lab results using advanced PDF parsing (PyMuPDF, pdfplumber) and image processing.
- **Clinical Intelligence**: Leverages generative AI (Google Gemini, Groq) to analyze extracted text, summarize patient conditions, and provide clinical insights.
- **Metadata Extraction**: Intelligently identifies and structures key patient and document metadata.
- **Multi-lingual Support**: Built-in translation capabilities to handle medical documents in different languages (via deep-translator).
- **Fast & Responsive UI**: Clean and intuitive frontend built with Vanilla HTML/JS/CSS for seamless user experience.

---

## 🛠️ Tech Stack

**Frontend:**
- HTML5, CSS3, Vanilla JavaScript

**Backend:**
- **Framework**: FastAPI (Python)
- **AI/LLM**: Google Generative AI (`google-generativeai`), Groq API
- **Document Processing**: `PyMuPDF`, `pdfplumber`, `pypdf`, `Pillow`, `reportlab`
- **Data Manipulation**: `pandas`, `openpyxl`
- **Server**: `uvicorn`

---

## 📂 Project Structure

```
Ai_medical_assitant/
│
├── backend/                  # FastAPI backend source code
│   ├── app/
│   │   ├── services/         # OCR, Metadata extraction, Clinical Intelligence
│   │   └── __init__.py
│   ├── uploads/              # Temporary storage for uploaded medical documents
│   └── .env                  # Backend environment variables
│
├── frontend/                 # Frontend application files
│   ├── index.html            # Main UI
│   ├── style.css             # UI Styling
│   ├── app.js                # Frontend logic and API integration
│   └── assets/               # Images and icons
│
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- API Keys for Google Gemini and/or Groq

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd Ai_medical_assitant
```

### 2. Backend Setup
Create a virtual environment and install dependencies:
```bash
python -m venv venv
venv\Scripts\activate      # On Windows
# source venv/bin/activate # On macOS/Linux

pip install -r requirements.txt
```

Set up your environment variables by copying the example file:
```bash
cp .env.example .env
```
*(Make sure to add your actual API keys inside `.env`)*

Start the FastAPI server:
```bash
uvicorn backend.app.main:app --reload
# or navigate into backend folder and run accordingly
```
The backend API will be available at `http://localhost:8000`.

### 3. Frontend Setup
The frontend is built with vanilla web technologies, so no complex build steps are required. 
Simply open `frontend/index.html` in your web browser, or use a tool like VS Code Live Server to run it locally.

---

## 📄 License
This project is licensed under the MIT License.
