// ==========================================================================
// MEDSAATHI FRONTEND APPLICATION CONTROLLER
// ==========================================================================

const API_BASE_URL = window.location.origin.includes(":8000") 
  ? window.location.origin 
  : "http://127.0.0.1:8000";

// DOM Elements
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const dropContent = document.getElementById("dropContent");
const selectedFileBadge = document.getElementById("selectedFileBadge");
const selectedFileName = document.getElementById("selectedFileName");
const removeFileBtn = document.getElementById("removeFileBtn");

const reportForm = document.getElementById("reportForm");
const submitBtn = document.getElementById("submitBtn");

const uploadSection = document.getElementById("uploadSection");
const loadingCard = document.getElementById("loadingCard");
const resultsWrapper = document.getElementById("resultsWrapper");

// Result Elements
const resPatientName = document.getElementById("resPatientName");
const resAgeGender = document.getElementById("resAgeGender");
const resDoctor = document.getElementById("resDoctor");
const resReportDate = document.getElementById("resReportDate");
const overallRiskBadge = document.getElementById("overallRiskBadge");
const criticalAlertBanner = document.getElementById("criticalAlertBanner");
const criticalAlertText = document.getElementById("criticalAlertText");

const chipTotal = document.getElementById("chipTotal");
const chipNormal = document.getElementById("chipNormal");
const chipLow = document.getElementById("chipLow");
const chipHigh = document.getElementById("chipHigh");
const chipCrit = document.getElementById("chipCrit");
const paramTableBody = document.getElementById("paramTableBody");

const btnLangEnglish = document.getElementById("btnLangEnglish");
const btnLangNative = document.getElementById("btnLangNative");
const nativeBtnLabel = document.getElementById("nativeBtnLabel");
const downloadPdfBtnEnglish = document.getElementById("downloadPdfBtnEnglish");
const downloadPdfBtnNative = document.getElementById("downloadPdfBtnNative");
const downloadNativeBtnText = document.getElementById("downloadNativeBtnText");
const downloadPdfBtn = document.getElementById("downloadPdfBtnEnglish"); // Alias for backwards compatibility
const analyzeAnotherBtn = document.getElementById("analyzeAnotherBtn");

// State
let selectedFile = null;
let currentEnglishSummary = "";
let currentNativeSummary = "";
let currentNativeLabel = "मराठी";

// --------------------------------------------------------------------------
// Drag & Drop File Handling
// --------------------------------------------------------------------------
dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    handleFileSelection(e.dataTransfer.files[0]);
  }
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files[0]) {
    handleFileSelection(e.target.files[0]);
  }
});

function handleFileSelection(file) {
  selectedFile = file;
  selectedFileName.textContent = file.name;
  dropContent.style.display = "none";
  selectedFileBadge.style.display = "inline-flex";
}

removeFileBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  selectedFile = null;
  fileInput.value = "";
  selectedFileBadge.style.display = "none";
  dropContent.style.display = "block";
});

// --------------------------------------------------------------------------
// Form Submission & API Analysis
// --------------------------------------------------------------------------
reportForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!selectedFile) {
    alert("Please select or drop a medical report file (PDF, JPG, PNG).");
    return;
  }

  const formData = new FormData(reportForm);
  // Ensure the file is appended correctly
  formData.set("file", selectedFile);

  // Show Loading State
  uploadSection.style.display = "none";
  loadingCard.style.display = "block";
  resultsWrapper.style.display = "none";

  try {
    const response = await fetch(`${API_BASE_URL}/uploadfile/`, {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.error || "Failed to analyze document.");
    }

    if (!data.validation?.is_medical_document) {
      alert("Validation Error: " + (data.error || "Uploaded document does not appear to be a medical report."));
      resetToUploadForm();
      return;
    }

    // Render Successful Results
    renderResults(data);

  } catch (error) {
    console.error("Error analyzing report:", error);
    alert("Error: " + error.message);
    resetToUploadForm();
  }
});

// --------------------------------------------------------------------------
// Render Analysis Dashboard
// --------------------------------------------------------------------------
function renderResults(data) {
  loadingCard.style.display = "none";
  resultsWrapper.style.display = "block";
  window.scrollTo({ top: 0, behavior: "smooth" });

  const patient = data.user_provided_metadata || {};
  const meta = data.metadata || {};
  const params = data.medical_parameters || [];
  const stats = data.parameter_summary || {};
  const bilingual = data.bilingual_summary || {};
  const clinical = data.clinical_insights || {};

  // 1. Patient Banner
  resPatientName.textContent = patient.patient_name || meta.patient?.name || "Patient";
  resAgeGender.textContent = `${patient.age || "N/A"} yrs, ${patient.gender || "N/A"}`;
  resDoctor.textContent = patient.doctor_name || meta.doctor?.name || "Consultant Physician";
  resReportDate.textContent = `Date: ${new Date().toLocaleDateString('en-GB')}`;

  // Overall Risk Badge
  const risk = stats.overall_health_risk || "NORMAL";
  overallRiskBadge.className = "risk-badge";
  if (risk === "CRITICAL") {
    overallRiskBadge.classList.add("critical");
    overallRiskBadge.textContent = "CRITICAL ALERT";
  } else if (risk === "ATTENTION_REQUIRED") {
    overallRiskBadge.classList.add("attention");
    overallRiskBadge.textContent = "ATTENTION REQUIRED";
  } else {
    overallRiskBadge.classList.add("normal");
    overallRiskBadge.textContent = "NORMAL PROFILE";
  }

  // Critical Alert Banner
  if (stats.critical_count > 0 || (clinical.emergency_alerts && clinical.emergency_alerts.length > 0)) {
    criticalAlertBanner.style.display = "flex";
    if (clinical.emergency_alerts && clinical.emergency_alerts.length > 0) {
      criticalAlertText.textContent = clinical.emergency_alerts[0];
    } else {
      criticalAlertText.textContent = "One or more medical values are in dangerous critical zones. Immediate medical evaluation is required.";
    }
  } else {
    criticalAlertBanner.style.display = "none";
  }

  // 2. Chips Counters
  chipTotal.textContent = `Total: ${stats.total_parameters_detected || params.length}`;
  chipNormal.textContent = `Normal: ${stats.normal_count || 0}`;
  chipLow.textContent = `Low: ${stats.low_count || 0}`;
  chipHigh.textContent = `High: ${stats.high_count || 0}`;
  chipCrit.textContent = `Critical: ${stats.critical_count || 0}`;

  // 3. Parameter Table
  paramTableBody.innerHTML = "";
  if (params.length === 0) {
    paramTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No specific diagnostic parameters detected in report text.</td></tr>`;
  } else {
    params.forEach(p => {
      const tr = document.createElement("tr");

      let statusClass = "normal";
      let statusText = p.status || "NORMAL";
      if (statusText === "CRITICAL LOW" || statusText === "CRITICAL HIGH") {
        statusClass = "critical-low";
      } else if (statusText === "LOW") {
        statusClass = "low";
      } else if (statusText === "HIGH") {
        statusClass = "high";
      }

      tr.innerHTML = `
        <td><strong>${escapeHtml(p.parameter)}</strong></td>
        <td><strong>${escapeHtml(String(p.value))}</strong></td>
        <td>${escapeHtml(p.unit || "-")}</td>
        <td>${escapeHtml(p.reference_range || "-")}</td>
        <td><span class="status-tag ${statusClass}">${escapeHtml(statusText)}</span></td>
      `;
      paramTableBody.appendChild(tr);
    });
  }

  // 4. Summaries & Language Switcher
  currentEnglishSummary = bilingual.summary_english || "Summary not available.";
  currentNativeSummary = bilingual.summary_native || currentEnglishSummary;
  currentNativeLabel = bilingual.language_native_label || bilingual.preferred_language || "Native";

  nativeBtnLabel.textContent = `${currentNativeLabel} Summary`;

  // Default view: English summary is displayed first by default.
  // The user can click the native language button anytime to switch to their chosen regional language.
  showSummary("english");

  // 5. Dual PDF Download Buttons (English & Native Language)
  const englishPdfUrl = data.pdf_download_url_english || data.pdf_download_url || "#";
  const nativePdfUrl = data.pdf_download_url_native || englishPdfUrl;

  if (downloadPdfBtnEnglish) {
    downloadPdfBtnEnglish.href = `${API_BASE_URL}${englishPdfUrl}`;
  }

  if (downloadPdfBtnNative) {
    if (bilingual.language_code && bilingual.language_code !== "en") {
      downloadPdfBtnNative.style.display = "inline-flex";
      downloadPdfBtnNative.href = `${API_BASE_URL}${nativePdfUrl}`;
      if (downloadNativeBtnText) {
        downloadNativeBtnText.textContent = `Download ${currentNativeLabel} PDF`;
      }
    } else {
      downloadPdfBtnNative.style.display = "none";
    }
  }
}

// --------------------------------------------------------------------------
// Language Toggle Controller
// --------------------------------------------------------------------------
btnLangEnglish.addEventListener("click", () => showSummary("english"));
btnLangNative.addEventListener("click", () => showSummary("native"));

function showSummary(lang) {
  if (lang === "english") {
    btnLangEnglish.classList.add("active");
    btnLangNative.classList.remove("active");
    summaryRendered.innerHTML = formatMarkdownToHtml(currentEnglishSummary);
  } else {
    btnLangNative.classList.add("active");
    btnLangEnglish.classList.remove("active");
    summaryRendered.innerHTML = formatMarkdownToHtml(currentNativeSummary);
  }
}

// --------------------------------------------------------------------------
// Simple Markdown Formatter to HTML
// --------------------------------------------------------------------------
function formatMarkdownToHtml(markdown) {
  if (!markdown) return "<p>No summary content available.</p>";

  const lines = markdown.split("\n");
  let html = "";
  let inList = false;

  for (let line of lines) {
    let trimmed = line.trim();

    if (!trimmed || trimmed.startsWith("---") || trimmed.startsWith("===")) {
      if (inList) { html += "</ul>"; inList = false; }
      continue;
    }

    if (trimmed.startsWith("# ")) {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<h2>${parseInlineFormatting(trimmed.substring(2))}</h2>`;
    } else if (trimmed.startsWith("## ")) {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<h2>${parseInlineFormatting(trimmed.substring(3))}</h2>`;
    } else if (trimmed.startsWith("### ")) {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<h3>${parseInlineFormatting(trimmed.substring(4))}</h3>`;
    } else if (trimmed.startsWith("#### ")) {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<h4>${parseInlineFormatting(trimmed.substring(5))}</h4>`;
    } else if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
      if (!inList) { html += "<ul>"; inList = true; }
      html += `<li>${parseInlineFormatting(trimmed.substring(2))}</li>`;
    } else if (/^\d+\.\s+/.test(trimmed)) {
      if (!inList) { html += "<ul>"; inList = true; }
      const content = trimmed.replace(/^\d+\.\s+/, "");
      html += `<li><strong>${trimmed.match(/^\d+/)[0]}.</strong> ${parseInlineFormatting(content)}</li>`;
    } else if (trimmed.startsWith("[ ] ")) {
      if (!inList) { html += "<ul>"; inList = true; }
      html += `<li><strong>❓ सवाल:</strong> ${parseInlineFormatting(trimmed.substring(4))}</li>`;
    } else {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<p>${parseInlineFormatting(trimmed)}</p>`;
    }
  }

  if (inList) { html += "</ul>"; }
  return html;
}

function parseInlineFormatting(str) {
  return str
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function resetToUploadForm() {
  uploadSection.style.display = "block";
  loadingCard.style.display = "none";
  resultsWrapper.style.display = "none";
}

analyzeAnotherBtn.addEventListener("click", () => {
  resetToUploadForm();
  window.scrollTo({ top: 0, behavior: "smooth" });
});
