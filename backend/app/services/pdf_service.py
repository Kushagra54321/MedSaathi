import os
import re
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Global font registry state
_INDIC_FONTS_REGISTERED = False
_INDIC_REGULAR_FONT = "Helvetica"
_INDIC_BOLD_FONT = "Helvetica-Bold"


def register_indic_fonts():
    """Registers Unicode TrueType fonts supporting Indian scripts (Hindi, Marathi, etc.)."""
    global _INDIC_FONTS_REGISTERED, _INDIC_REGULAR_FONT, _INDIC_BOLD_FONT
    if _INDIC_FONTS_REGISTERED:
        return _INDIC_REGULAR_FONT, _INDIC_BOLD_FONT

    font_paths = [
        ("C:/Windows/Fonts/Nirmala.ttc", 0, 1),
        ("C:/Windows/Fonts/nirmala.ttc", 0, 1),
    ]

    for path, reg_idx, bold_idx in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("IndicFont", path, subfontIndex=reg_idx))
                pdfmetrics.registerFont(TTFont("IndicFont-Bold", path, subfontIndex=bold_idx))
                _INDIC_REGULAR_FONT = "IndicFont"
                _INDIC_BOLD_FONT = "IndicFont-Bold"
                _INDIC_FONTS_REGISTERED = True
                return _INDIC_REGULAR_FONT, _INDIC_BOLD_FONT
            except Exception as e:
                print(f"[WARNING] Failed to register TTC font {path}: {e}")

    # Fallback to standard Helvetica if Nirmala is not available
    _INDIC_REGULAR_FONT = "Helvetica"
    _INDIC_BOLD_FONT = "Helvetica-Bold"
    _INDIC_FONTS_REGISTERED = True
    return _INDIC_REGULAR_FONT, _INDIC_BOLD_FONT


def generate_medical_pdf_report(
    report_id: str,
    patient_meta: Dict[str, Any],
    parameters: List[Dict[str, Any]],
    summary_text: str,
    risk_level: str = "NORMAL",
    language_label: str = "English",
    lang_code: str = "en"
) -> str:
    """
    Generates a professional, print-ready PDF report for either English or Native Language.
    Saves the file as MedSaathi_Report_{report_id}_{lang_code}.pdf and returns the absolute path.
    """
    is_native = lang_code.lower() not in ["en", "english"]
    
    if is_native:
        reg_font, bold_font = register_indic_fonts()
        pdf_filename = f"MedSaathi_Report_{report_id}_native.pdf"
    else:
        reg_font, bold_font = "Helvetica", "Helvetica-Bold"
        pdf_filename = f"MedSaathi_Report_{report_id}_en.pdf"

    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=17,
        leading=21,
        textColor=colors.HexColor('#0F766E')  # Deep Teal
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#475569')  # Slate
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=9,
        spaceAfter=3
    )

    h3_style = ParagraphStyle(
        'SectionH3',
        parent=styles['Normal'],
        fontName=bold_font,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0D9488'),
        spaceBefore=6,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1E293B')
    )

    bold_body = ParagraphStyle(
        'BoldBodyDark',
        parent=body_style,
        fontName=bold_font
    )

    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName=reg_font,
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#64748B')
    )

    story = []

    # 1. Header Banner
    if is_native:
        title_text = "MEDSAATHI - स्मार्ट हेल्थकेयर सहायक"
        sub_text = f"एआई-आधारित क्लिनिकल विश्लेषण और स्वास्थ्य रिपोर्ट | भाषा: {language_label} | दिनांक: {datetime.now().strftime('%d-%b-%Y %H:%M')}"
    else:
        title_text = "MEDSAATHI - SMART HEALTHCARE ASSISTANT"
        sub_text = f"AI-Powered Clinical Analysis & Patient Summary Report | Language: {language_label} | Date: {datetime.now().strftime('%d-%b-%Y %H:%M')}"

    story.append(Paragraph(title_text, title_style))
    story.append(Paragraph(sub_text, subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F766E'), spaceBefore=5, spaceAfter=8))

    # 2. Patient & Doctor Info Grid
    name = patient_meta.get("name", "N/A")
    age = patient_meta.get("age", "N/A")
    gender = patient_meta.get("gender", "N/A")
    doctor = patient_meta.get("doctor", "Consultant Physician")

    if is_native:
        lbl_patient = "मरीज का नाम:"
        lbl_age_gender = "उम्र / लिंग:"
        lbl_doctor = "डॉक्टर / लैब:"
        lbl_report_id = "रिपोर्ट आईडी:"
        val_age_gender = f"{age} वर्ष / {gender}"
    else:
        lbl_patient = "Patient Name:"
        lbl_age_gender = "Age / Gender:"
        lbl_doctor = "Consulting Doctor:"
        lbl_report_id = "Report ID:"
        val_age_gender = f"{age} yrs / {gender}"

    patient_data = [
        [
            Paragraph(f"<b>{lbl_patient}</b>", bold_body), Paragraph(str(name), bold_body),
            Paragraph(f"<b>{lbl_age_gender}</b>", bold_body), Paragraph(val_age_gender, body_style)
        ],
        [
            Paragraph(f"<b>{lbl_doctor}</b>", bold_body), Paragraph(str(doctor), body_style),
            Paragraph(f"<b>{lbl_report_id}</b>", bold_body), Paragraph(str(report_id)[:16], body_style)
        ]
    ]

    patient_table = Table(patient_data, colWidths=[90, 180, 85, 185])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 8))

    # 3. Overall Risk Status Badge
    risk_upper = str(risk_level).upper()
    if "CRITICAL" in risk_upper:
        bg_color = colors.HexColor('#FEE2E2')
        border_color = colors.HexColor('#EF4444')
        text_color = colors.HexColor('#991B1B')
        if is_native:
            msg = "<b>तातडीचा इशारा / तत्काल चेतावनी:</b> कुछ पैरामीटर गंभीर स्थिति में हैं। तुरंत डॉक्टर से परामर्श लें!"
        else:
            msg = "<b>CRITICAL ALERT:</b> One or more laboratory values are in critical danger zones. Immediate medical consultation is required."
    elif "ATTENTION" in risk_upper:
        bg_color = colors.HexColor('#FEF3C7')
        border_color = colors.HexColor('#F59E0B')
        text_color = colors.HexColor('#92400E')
        if is_native:
            msg = "<b>वैद्यकीय सल्ला आवश्यक / ध्यान दें:</b> कुछ पैरामीटर सामान्य सीमा से बाहर हैं। डॉक्टर से परामर्श की सलाह दी जाती है।"
        else:
            msg = "<b>ATTENTION REQUIRED:</b> Some laboratory values are outside normal reference limits. Follow-up consultation is advised."
    else:
        bg_color = colors.HexColor('#DCFCE7')
        border_color = colors.HexColor('#22C55E')
        text_color = colors.HexColor('#166534')
        if is_native:
            msg = "<b>सामान्य स्वास्थ्य प्रोफाइल:</b> सभी टेस्ट सामान्य सीमा के भीतर हैं।"
        else:
            msg = "<b>NORMAL HEALTH PROFILE:</b> All detected laboratory parameters are within standard physiological ranges."

    alert_para = Paragraph(f"<font color='{text_color.hexval()}'>{msg}</font>", body_style)
    alert_table = Table([[alert_para]], colWidths=[540])
    alert_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOX', (0, 0), (-1, -1), 1, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(alert_table)
    story.append(Spacer(1, 10))

    # 4. Laboratory Parameters Table
    if parameters:
        sec_param_title = "प्रयोगशाला परीक्षण विश्लेषण (Laboratory Parameters)" if is_native else "Laboratory Parameters Analysis"
        story.append(Paragraph(sec_param_title, h2_style))
        
        if is_native:
            th_param = "पैरामीटर"
            th_val = "परिणाम"
            th_unit = "इकाई"
            th_range = "सामान्य सीमा"
            th_status = "स्थिति"
        else:
            th_param = "Parameter"
            th_val = "Result"
            th_unit = "Unit"
            th_range = "Reference Range"
            th_status = "Status"

        table_rows = [
            [
                Paragraph(f"<b>{th_param}</b>", bold_body),
                Paragraph(f"<b>{th_val}</b>", bold_body),
                Paragraph(f"<b>{th_unit}</b>", bold_body),
                Paragraph(f"<b>{th_range}</b>", bold_body),
                Paragraph(f"<b>{th_status}</b>", bold_body)
            ]
        ]

        for p in parameters:
            p_name = str(p.get("parameter", ""))
            val = str(p.get("value", ""))
            unit = str(p.get("unit", ""))
            ref = str(p.get("reference_range", "") or "-")
            status = str(p.get("status", "NORMAL")).upper()

            if is_native:
                if "CRITICAL LOW" in status:
                    status_display = "अत्यधिक कम (CRITICAL)"
                    status_html = f"<font color='#B91C1C'><b>{status_display}</b></font>"
                elif "CRITICAL HIGH" in status:
                    status_display = "अत्यधिक अधिक (CRITICAL)"
                    status_html = f"<font color='#B91C1C'><b>{status_display}</b></font>"
                elif "LOW" in status:
                    status_display = "कम (LOW)"
                    status_html = f"<font color='#D97706'><b>{status_display}</b></font>"
                elif "HIGH" in status:
                    status_display = "अधिक (HIGH)"
                    status_html = f"<font color='#D97706'><b>{status_display}</b></font>"
                else:
                    status_display = "सामान्य (NORMAL)"
                    status_html = f"<font color='#15803D'><b>{status_display}</b></font>"
            else:
                if "CRITICAL" in status:
                    status_html = f"<font color='#B91C1C'><b>{status}</b></font>"
                elif status in ["LOW", "HIGH"]:
                    status_html = f"<font color='#D97706'><b>{status}</b></font>"
                elif status == "NORMAL":
                    status_html = f"<font color='#15803D'><b>NORMAL</b></font>"
                else:
                    status_html = f"<font color='#64748B'>{status}</font>"

            table_rows.append([
                Paragraph(p_name, body_style),
                Paragraph(f"<b>{val}</b>", body_style),
                Paragraph(unit, body_style),
                Paragraph(ref, body_style),
                Paragraph(status_html, body_style)
            ])

        param_table = Table(table_rows, colWidths=[160, 65, 65, 130, 120])
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(param_table)
        story.append(Spacer(1, 10))

    # 5. Formatted Summary Content
    sec_summary_title = "चिकित्सीय विश्लेषण और स्वास्थ्य सारांश (Medical Summary)" if is_native else "Clinical Insights & Medical Summary"
    story.append(Paragraph(sec_summary_title, h2_style))

    # Parse and clean markdown lines for ReportLab
    lines = summary_text.split("\n")
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("---") or line.startswith("==="):
            continue
        if line.startswith("# "):
            continue  # Already represented in document header
        
        # Clean inline markdown bold formatting into ReportLab HTML tags
        formatted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
        formatted_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted_line)

        if formatted_line.startswith("### "):
            clean_head = formatted_line.replace("### ", "").strip()
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>{clean_head}</b>", h2_style))
            story.append(Spacer(1, 2))
        elif formatted_line.startswith("#### "):
            clean_subhead = formatted_line.replace("#### ", "").strip()
            story.append(Paragraph(f"<b>{clean_subhead}</b>", h3_style))
            story.append(Spacer(1, 2))
        elif formatted_line.startswith("* ") or formatted_line.startswith("- "):
            clean_bullet = formatted_line[2:].strip()
            story.append(Paragraph(f"• {clean_bullet}", bullet_style))
        elif re.match(r'^\d+\.\s+', formatted_line):
            num = re.match(r'^\d+', formatted_line).group()
            content = re.sub(r'^\d+\.\s+', '', formatted_line).strip()
            story.append(Paragraph(f"<b>{num}.</b> {content}", bullet_style))
        elif formatted_line.startswith("[ ] "):
            clean_q = formatted_line[4:].strip()
            story.append(Paragraph(f"<b>?</b> {clean_q}", bullet_style))
        else:
            if "Medical Disclaimer:" in formatted_line or "चिकित्सीय सूचना" in formatted_line:
                continue  # Dedicated footer disclaimer handles this
            story.append(Paragraph(formatted_line, body_style))
            story.append(Spacer(1, 2))

    # 6. Medical Disclaimer Footer
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#CBD5E1'), spaceBefore=4, spaceAfter=5))
    if is_native:
        disclaimer_text = (
            "<b>चिकित्सीय सूचना (Medical Disclaimer):</b> यह दस्तावेज़ MedSaathi द्वारा तैयार किया गया एआई-सहायक लैब विश्लेषण है। "
            "यह केवल मरीज की समझ और स्वास्थ्य साक्षरता के लिए है। यह कोई डॉक्टरी निदान या दवा का पर्चा नहीं है। "
            "इलाज और चिकित्सकीय निर्णय के लिए हमेशा अपने योग्य डॉक्टर से परामर्श लें।"
        )
    else:
        disclaimer_text = (
            "<b>Medical Disclaimer:</b> This document is an AI-assisted laboratory interpretation generated by MedSaathi. "
            "It is designed solely to facilitate patient understanding and health literacy. It is NOT a clinical diagnosis, "
            "medical prescription, or substitute for professional doctor evaluation. Please consult your physician for medical advice."
        )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(story)

    # For default compatibility, also copy to standard MedSaathi_Report_{report_id}.pdf
    default_pdf_path = os.path.join(REPORTS_DIR, f"MedSaathi_Report_{report_id}.pdf")
    try:
        shutil.copyfile(pdf_path, default_pdf_path)
    except Exception:
        pass

    return pdf_path
