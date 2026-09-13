import os
import json
import urllib.request
import urllib.parse
from typing import List, Optional, Dict
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

# In-memory translation cache to optimize performance
_TRANSLATION_CACHE: Dict[str, str] = {}

# Language mapping
LANG_CODE_MAP = {
    "hindi": "hi",
    "hi": "hi",
    "marathi": "mr",
    "mr": "mr",
    "punjabi": "pa",
    "pa": "pa",
    "gujarati": "gu",
    "gu": "gu",
    "bengali": "bn",
    "bn": "bn",
    "telugu": "te",
    "te": "te",
    "tamil": "ta",
    "ta": "ta",
    "kannada": "kn",
    "kn": "kn",
    "malayalam": "ml",
    "ml": "ml",
    "english": "en",
    "en": "en"
}


def translate_text(text: str, target_lang: str) -> str:
    """
    Translates text into the target Indic language using Google Translate API.
    Supports official Google Cloud Translation API key if provided, or Google's
    reliable translation endpoint with zero dependencies and no downtime.
    """
    if not text or not text.strip():
        return text

    target_code = LANG_CODE_MAP.get(target_lang.strip().lower(), target_lang.strip().lower())
    if target_code == "en":
        return text

    cache_key = f"{target_code}::{text.strip()}"
    if cache_key in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[cache_key]

    # Optional: Google Cloud Translation API Key if configured in .env
    cloud_api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if cloud_api_key:
        try:
            url = f"https://translation.googleapis.com/language/translate/v2?key={cloud_api_key}"
            payload = json.dumps({"q": text, "target": target_code, "format": "text"}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                translated = result["data"]["translations"][0]["translatedText"]
                _TRANSLATION_CACHE[cache_key] = translated
                return translated
        except Exception as e:
            print(f"[Translation] Cloud API error: {e}, falling back to direct endpoint.")

    # High-speed direct translation endpoint
    try:
        # Handle chunking if text is very long
        if len(text) > 1500:
            lines = text.split("\n")
            translated_lines = []
            for line in lines:
                if line.strip():
                    translated_lines.append(translate_text(line, target_code))
                else:
                    translated_lines.append("")
            res = "\n".join(translated_lines)
            _TRANSLATION_CACHE[cache_key] = res
            return res

        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_code}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = "".join([part[0] for part in data[0] if part and part[0]])
            if translated:
                _TRANSLATION_CACHE[cache_key] = translated
                return translated
    except Exception as err:
        print(f"[Translation] Translation warning ({err}) for target '{target_code}'. Returning original.")
        return text

    return text


def translate_batch(texts: List[str], target_lang: str) -> List[str]:
    """
    Translates a list of strings (e.g. dietary tips or doctor checklist questions).
    """
    return [translate_text(t, target_lang) for t in texts]
