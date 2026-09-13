import os
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Supported Native Indian Languages with Native Script Names
SUPPORTED_LANGUAGES = {
    "english": {"code": "en", "label": "English", "native": "English"},
    "marathi": {"code": "mr", "label": "Marathi", "native": "मराठी"},
    "hindi": {"code": "hi", "label": "Hindi", "native": "हिन्दी"},
    "punjabi": {"code": "pa", "label": "Punjabi", "native": "ਪੰਜਾਬੀ"},
    "gujarati": {"code": "gu", "label": "Gujarati", "native": "ગુજરાતી"},
    "bengali": {"code": "bn", "label": "Bengali", "native": "বাংলা"},
    "telugu": {"code": "te", "label": "Telugu", "native": "తెలుగు"},
    "tamil": {"code": "ta", "label": "Tamil", "native": "தமிழ்"},
    "kannada": {"code": "kn", "label": "Kannada", "native": "ಕನ್ನಡ"},
    "malayalam": {"code": "ml", "label": "Malayalam", "native": "മലയാളം"}
}

# Regional Language UI and Section Templates
NATIVE_TEMPLATES = {
    "mr": {
        "title": "वैद्यकीय आरोग्य विश्लेषण आणि अहवाल सारांश",
        "patient_header": "रुग्णाची माहिती",
        "name": "रुग्णाचे नाव",
        "age_gender": "वय आणि लिंग",
        "doctor": "सल्लागार डॉक्टर",
        "status_normal": "सर्व चाचण्या सामान्य मर्यादेत आहेत. तुमचे आरोग्य चांगले आहे.",
        "status_attention": "काही चाचण्या सामान्य मर्यादेबाहेर आहेत. डॉक्टरांचा सल्ला घेणे आवश्यक आहे.",
        "status_critical": "तातडीचा इशारा: काही वैद्यकीय मापदंड अत्यंत गंभीर पातळीवर आहेत. ताबडतोब डॉक्टरांशी संपर्क साधा!",
        "sec_overview": "१. अहवाल सारांश आणि सद्यस्थिती (Executive Summary)",
        "sec_findings": "२. महत्त्वाचे निष्कर्ष आणि मापदंड सुधारण्याचे उपाय",
        "sec_conditions": "३. आपली आरोग्य स्थिती समजून घ्या (Understanding Your Condition)",
        "sec_diet_lifestyle": "४. आहार आणि जीवनशैली विषयक मार्गदर्शन",
        "sub_diet": "आहारविषयक सूचना (Nutritional Guidance)",
        "sub_lifestyle": "जीवनशैली आणि दैनंदिन काळजी (Lifestyle & Daily Care)",
        "sec_doctor_checklist": "५. डॉक्टरांना विचारण्यासाठी महत्त्वाच्या प्रश्नांची यादी (Doctor Checklist)",
        "disclaimer_title": "वैद्यकीय सूचना (Medical Disclaimer):",
        "disclaimer": "हा सारांश केवळ माहितीसाठी आणि प्राथमिक समज वाढवण्यासाठी तयार केला आहे. अंतिम निदान आणि उपचारांसाठी नेहमी तुमच्या डॉक्टरांचा सल्ला घ्या.",
        "normal": "सामान्य (Normal)",
        "low": "कमी (Low)",
        "high": "जास्त (High)",
        "critical_low": "अत्यंत कमी (Critical Low)",
        "critical_high": "अत्यंत जास्त (Critical High)",
        "ref_range": "सामान्य प्रमाण:",
        "meaning": "साधा अर्थ:",
        "solution": "कसे सुधारावे / उपाय:"
    },
    "hi": {
        "title": "चिकित्सा स्वास्थ्य विश्लेषण और रिपोर्ट सारांश",
        "patient_header": "मरीज की जानकारी",
        "name": "मरीज का नाम",
        "age_gender": "उम्र और लिंग",
        "doctor": "सलाहकार डॉक्टर",
        "status_normal": "सभी टेस्ट सामान्य सीमा के भीतर हैं। आपकी स्वास्थ्य स्थिति संतुलित है।",
        "status_attention": "कुछ टेस्ट सामान्य सीमा से बाहर हैं। डॉक्टर से परामर्श की आवश्यकता है।",
        "status_critical": "तत्काल चेतावनी: कुछ पैरामीटर गंभीर स्थिति में हैं। तुरंत डॉक्टर से संपर्क करें!",
        "sec_overview": "1. रिपोर्ट सारांश और वर्तमान स्थिति (Executive Summary)",
        "sec_findings": "2. प्रमुख निष्कर्ष और पैरामीटर सुधारने के उपाय",
        "sec_conditions": "3. अपनी स्वास्थ्य स्थिति को समझें (Understanding Your Condition)",
        "sec_diet_lifestyle": "4. आहार और जीवनशैली संबंधी मार्गदर्शन",
        "sub_diet": "आहार संबंधी सुझाव (Nutritional Guidance)",
        "sub_lifestyle": "जीवनशैली और दैनिक देखभाल (Lifestyle & Daily Care)",
        "sec_doctor_checklist": "5. डॉक्टर से पूछने योग्य सवालों की चेकलिस्ट (Doctor Checklist)",
        "disclaimer_title": "चिकित्सीय सूचना (Medical Disclaimer):",
        "disclaimer": "यह सारांश केवल स्वास्थ्य जागरूकता और समझ के लिए है। किसी भी दवा या उपचार के लिए हमेशा योग्य डॉक्टर से परामर्श लें।",
        "normal": "सामान्य (Normal)",
        "low": "कम (Low)",
        "high": "अधिक (High)",
        "critical_low": "अत्यधिक कम (Critical Low)",
        "critical_high": "अत्यधिक अधिक (Critical High)",
        "ref_range": "सामान्य सीमा:",
        "meaning": "सरल अर्थ:",
        "solution": "कैसे ठीक करें / उपाय:"
    },
    "pa": {
        "title": "ਮੈਡੀਕਲ ਸਿਹਤ ਵਿਸ਼ਲੇਸ਼ਣ ਅਤੇ ਰਿਪੋਰਟ ਸਾਰਾਂਸ਼",
        "patient_header": "ਮਰੀਜ਼ ਦੀ ਜਾਣਕਾਰੀ",
        "name": "ਮਰੀਜ਼ ਦਾ ਨਾਮ",
        "age_gender": "ਉਮਰ ਅਤੇ ਲਿੰਗ",
        "doctor": "ਡਾਕਟਰ",
        "status_normal": "ਸਾਰੇ ਟੈਸਟ ਆਮ ਸੀਮਾ ਦੇ ਅੰਦਰ ਹਨ।",
        "status_attention": "ਕੁਝ ਟੈਸਟ ਆਮ ਸੀਮਾ ਤੋਂ ਬਾਹਰ ਹਨ। ਡਾਕਟਰ ਦੀ ਸਲਾਹ ਜ਼ਰੂਰੀ ਹੈ।",
        "status_critical": "ਗੰਭੀਰ ਚੇਤਾਵਨੀ: ਕੁਝ ਮਾਪਦੰਡ ਬਹੁਤ ਗੰਭੀਰ ਪੱਧਰ 'ਤੇ ਹਨ। ਤੁਰੰਤ ਡਾਕਟਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ!",
        "sec_overview": "1. ਰਿਪੋਰਟ ਸੰਖੇਪ ਅਤੇ ਸਿਹਤ ਸਥਿਤੀ (Executive Summary)",
        "sec_findings": "2. ਮੁੱਖ ਨਤੀਜੇ ਅਤੇ ਸੁਧਾਰ ਦੇ ਉਪਾਅ",
        "sec_conditions": "3. ਆਪਣੀ ਸਿਹਤ ਸਥਿਤੀ ਨੂੰ ਸਮਝੋ",
        "sec_diet_lifestyle": "4. ਖੁਰਾਕ ਅਤੇ ਜੀਵਨ ਸ਼ੈਲੀ ਬਾਰੇ ਸਲਾਹ",
        "sub_diet": "ਖੁਰਾਕ ਸਬੰਧੀ ਸੁਝਾਅ (Nutritional Guidance)",
        "sub_lifestyle": "ਜੀਵਨ ਸ਼ੈਲੀ ਸਬੰਧੀ ਸੁਝਾਅ (Lifestyle & Daily Care)",
        "sec_doctor_checklist": "5. ਡਾਕਟਰ ਨੂੰ ਪੁੱਛਣ ਵਾਲੇ ਜ਼ਰੂਰੀ ਸਵਾਲ (Doctor Checklist)",
        "disclaimer_title": "ਮੈਡੀਕਲ ਬੇਦਾਅਵਾ (Medical Disclaimer):",
        "disclaimer": "ਇਹ ਸਾਰਾਂਸ਼ ਸਿਰਫ ਜਾਣਕਾਰੀ ਅਤੇ ਮਾਰਗਦਰਸ਼ਨ ਲਈ ਹੈ। ਇਲਾਜ ਲਈ ਆਪਣੇ ਡਾਕਟਰ ਦੀ ਸਲਾਹ ਲਓ।",
        "normal": "ਆਮ (Normal)",
        "low": "ਘੱਟ (Low)",
        "high": "ਵੱਧ (High)",
        "critical_low": "ਬਹੁਤ ਘੱਟ (Critical Low)",
        "critical_high": "ਬਹੁਤ ਵੱਧ (Critical High)",
        "ref_range": "ਆਮ ਰੇਂਜ:",
        "meaning": "ਸਧਾਰਨ ਅਰਥ:",
        "solution": "ਕਿਵੇਂ ਠੀਕ ਕਰੀਏ:"
    },
    "gu": {
        "title": "તબીબી આરોગ્ય વિશ્લેષણ અને રિપોર્ટ સારાંશ",
        "patient_header": "દર્દીની વિગતો",
        "name": "દર્દીનું નામ",
        "age_gender": "ઉંમર અને જાતિ",
        "doctor": "ડોક્ટરનું નામ",
        "status_normal": "બધા ટેસ્ટ સામાન્ય મર્યાદામાં છે.",
        "status_attention": "કેટલાક પરિણામો સામાન્ય મર્યાદા બહાર છે. ડોક્ટરની સલાહ જરૂરી છે.",
        "status_critical": "તાત્કાલિક ચેતવણી: કેટલાક પેરામીટર અત્યંત ગંભીર સ્તરે છે. તાત્કાલિક ડોક્ટરનો સંપર્ક કરો!",
        "sec_overview": "1. રિપોર્ટ સારાંશ અને સ્થિતિ (Executive Summary)",
        "sec_findings": "2. મુખ્ય તારણો અને સુધારણાના ઉપાયો",
        "sec_conditions": "3. તમારી આરોગ્ય સ્થિતિ સમજો",
        "sec_diet_lifestyle": "4. આહાર અને જીવનશૈલી સંબંધિત માર્ગદર્શન",
        "sub_diet": "આહાર સંબંધિત સલાહ (Nutritional Guidance)",
        "sub_lifestyle": "જીવનશૈલી સંબંધિત સલાહ (Lifestyle & Daily Care)",
        "sec_doctor_checklist": "5. ડોક્ટરને પૂછવા માટેના અગત્યના પ્રશ્નો",
        "disclaimer_title": "તબીબી સૂચના (Medical Disclaimer):",
        "disclaimer": "આ સારાંશ માત્ર માહિતી અને સમજણ માટે છે. સારવાર માટે હંમેશા ડોક્ટરની સલાહ લો.",
        "normal": "સામાન્ય (Normal)",
        "low": "ઓછું (Low)",
        "high": "વધુ (High)",
        "critical_low": "અત્યંત ઓછું (Critical Low)",
        "critical_high": "અત્યંત વધુ (Critical High)",
        "ref_range": "સામાન્ય મર્યાદા:",
        "meaning": "સરળ અર્થ:",
        "solution": "કેવી રીતે સુધારવું:"
    },
    "bn": {
        "title": "চিকিৎসা স্বাস্থ্য বিশ্লেষণ এবং রিপোর্ট সারাংশ",
        "patient_header": "রোগীর তথ্য",
        "name": "রোগীর নাম",
        "age_gender": "বয়স ও লিঙ্গ",
        "doctor": "পরামর্শদাতা ডাক্তার",
        "status_normal": "সমস্ত পরীক্ষার ফলাফল স্বাভাবিক সীমার মধ্যে রয়েছে।",
        "status_attention": "কিছু ফলাফল স্বাভাবিক সীমার বাইরে। ডাক্তারের পরামর্শ নিন।",
        "status_critical": "জরুরী সতর্কতা: কিছু মান অত্যন্ত সংকটজনক অবস্থায় রয়েছে। অবিলম্বে ডাক্তারের সাথে যোগাযোগ করুন!",
        "sec_overview": "১. রিপোর্ট সারাংশ ও বর্তমান অবস্থা (Executive Summary)",
        "sec_findings": "২. মূল ফলাফল ও প্রতিকারের উপায়",
        "sec_conditions": "৩. আপনার স্বাস্থ্য পরিস্থিতি বুঝুন",
        "sec_diet_lifestyle": "৪. খাদ্যতালিকা ও জীবনযাত্রার পরামর্শ",
        "sub_diet": "খাদ্য সংক্রান্ত পরামর্শ (Nutritional Guidance)",
        "sub_lifestyle": "জীবনযাত্রা সংক্রান্ত পরামর্শ (Lifestyle & Daily Care)",
        "sec_doctor_checklist": "৫. ডাক্তারকে জিজ্ঞাসা করার জন্য গুরুত্বপূর্ণ প্রশ্ন",
        "disclaimer_title": "চিকিৎসা দাবিত্যাগ (Medical Disclaimer):",
        "disclaimer": "এই সারাংশটি শুধুমাত্র তথ্য ও সাধারণ ব্যাখ্যার জন্য। চিকিৎসার জন্য সর্বদা আপনার ডাক্তারের পরামর্শ নিন।",
        "normal": "স্বাভাবিক (Normal)",
        "low": "কম (Low)",
        "high": "বেশি (High)",
        "critical_low": "অত্যন্ত কম (Critical Low)",
        "critical_high": "অত্যন্ত বেশি (Critical High)",
        "ref_range": "স্বাভাবিক মাত্রা:",
        "meaning": "সহজ অর্থ:",
        "solution": "কীভাবে ঠিক করবেন:"
    },
    "te": {
        "title": "వైద్య ఆరోగ్య విశ్లేషణ మరియు నివేదిక సారాంశం",
        "patient_header": "రోగి వివరాలు",
        "name": "రోగి పేరు",
        "age_gender": "వయస్సు & లింగం",
        "doctor": "డాక్టర్ పేరు",
        "status_normal": "అన్ని పరీక్షా ఫలితాలు సాధారణ పరిమితిలో ఉన్నాయి.",
        "status_attention": "కొన్ని ఫలితాలు సాధారణ పరిమితికి భిన్నంగా ఉన్నాయి. వైద్యుడిని సంప్రదించండి.",
        "status_critical": "అత్యవసర హెచ్చరిక: కొన్ని విలువలు చాలా ప్రమాదకర స్థాయిలో ఉన్నాయి. వెంటనే వైద్యుడిని సంప్రదించండి!",
        "sec_overview": "1. నివేదిక సారాంశం మరియు స్థితి (Executive Summary)",
        "sec_findings": "2. ముఖ్యమైన ఫలితాలు మరియు నివారణ మార్గాలు",
        "sec_conditions": "3. మీ ఆరోగ్య పరిస్థితిని అర్థం చేసుకోండి",
        "sec_diet_lifestyle": "4. ఆహార మరియు జీవనశైలి సూచనలు",
        "sub_diet": "ఆహార సూచనలు (Nutritional Guidance)",
        "sub_lifestyle": "జీవనశైలి సూచనలు (Lifestyle & Daily Care)",
        "sec_doctor_checklist": "5. డాక్టర్‌ను అడగవలసిన ముఖ్యమైన ప్రశ్నలు",
        "disclaimer_title": "వైద్య నిరాకరణ (Medical Disclaimer):",
        "disclaimer": "ఈ సారాంశం సమాచార అవగాహన కొరకు మాత్రమే. చికిత్స కోసం మీ వైద్యుడిని సంప్రదించండి.",
        "normal": "సాధారణం (Normal)",
        "low": "తక్కువ (Low)",
        "high": "ఎక్కువ (High)",
        "critical_low": "చాలా తక్కువ (Critical Low)",
        "critical_high": "చాలా ఎక్కువ (Critical High)",
        "ref_range": "సాధారణ పరిమితి:",
        "meaning": "సరళమైన అర్థం:",
        "solution": "ఎలా మెరుగుపరచాలి:"
    }
}

# Pre-translated Clinical Knowledge for Offline Analyser Fallback
OFFLINE_PARAM_TRANSLATIONS = {
    "egfr": {
        "hi": {
            "meaning": "यह टेस्ट दर्शाता है कि आपकी किडनियां (गुर्दे) खून को कितनी कुशलता से छान और साफ कर रही हैं।",
            "effect": "इसका कम होना किडनी की कार्यक्षमता में गिरावट या दबाव का संकेत देता है।",
            "solution": "किडनी विशेषज्ञ (नेफ्रोलॉजिस्ट) से तुरंत परामर्श लें, अधिक नमक व बहुत भारी प्रोटीन कम करें, और डॉक्टर से पूछे बिना कोई पेनकिलर न लें।"
        },
        "mr": {
            "meaning": "ही चाचणी दर्शवते की तुमची मूत्रपिंडे (किडनी) रक्त किती चांगल्या प्रकारे गाळत व स्वच्छ करत आहेत.",
            "effect": "हे प्रमाण कमी असणे किडनीच्या कार्यक्षमतेत घट दर्शवते.",
            "solution": "किडनी तज्ज्ञांचा (नेफ्रोलॉजिस्ट) त्वरित सल्ला घ्या, आहारात मीठ कमी करा आणि डॉक्टरांच्या सल्ल्याशिवाय कोणतीही वेदनाशामक औषधे घेऊ नका."
        }
    },
    "creatinine": {
        "hi": {
            "meaning": "यह मांसपेशियों की सामान्य क्रिया से बनने वाला वेस्ट प्रोडक्ट है जिसे स्वस्थ किडनियां पेशाब द्वारा बाहर निकालती हैं।",
            "effect": "इसका बढ़ना दर्शाता है कि किडनी खून से कचरा पूरी तरह बाहर नहीं निकाल पा रही है।",
            "solution": "भरपूर पानी पिएं (यदि डॉक्टर ने सीमित न किया हो), नमक कम करें, और डॉक्टर की निगरानी में नियमित जांच कराएं।"
        },
        "mr": {
            "meaning": "हा स्नायूंच्या हालचालीतून निर्माण होणारा टाकाऊ घटक आहे जो निरोगी किडनीद्वारे लघवीवाटे बाहेर टाकला जातो.",
            "effect": "हे प्रमाण वाढणे किडनीवर ताण असल्याचे दर्शवते.",
            "solution": "पुरेसे पाणी प्या, आहारात मीठ मर्यादित ठेवा आणि डॉक्टरांच्या मार्गदर्शनाखाली नियमित तपासणी करा."
        }
    },
    "potassium": {
        "hi": {
            "meaning": "यह दिल की धड़कन, नसों और मांसपेशियों के सुचारू संचालन के लिए एक अत्यंत आवश्यक इलेक्ट्रोलाइट है।",
            "effect": "पोटेशियम का अधिक या कम होना दिल की धड़कन और मांसपेशियों को प्रभावित कर सकता है।",
            "solution": "पोटेशियम अधिक होने पर केला, संतरा, नारियल पानी व आलू सीमित करें और तुरंत डॉक्टर से मिलें।"
        },
        "mr": {
            "meaning": "हा हृदयाचे ठोके आणि स्नायूंचे कार्य सुरळीत चालण्यासाठी अत्यंत आवश्यक घटक आहे.",
            "effect": "पोटॅशियमचे प्रमाण असंतुलित झाल्यास हृदयाच्या ठोक्यांवर परिणाम होऊ शकतो.",
            "solution": "प्रमाण जास्त असल्यास केळी, संत्री, नारळ पाणी कमी करा आणि त्वरित डॉक्टरांचा सल्ला घ्या."
        }
    },
    "heart rate": {
        "hi": {
            "meaning": "यह मापता है कि आपका दिल प्रति मिनट कितनी बार धड़क रहा है।",
            "effect": "धड़कन बहुत तेज (टैचीकार्डिया) होने से घबराहट, कमजोरी और थकान महसूस हो सकती है।",
            "solution": "गहरे सांस लें, कैफीन व तनाव से बचें, पर्याप्त विश्राम करें और धड़कन तेज रहने पर तुरंत डॉक्टर को दिखाएं।"
        },
        "mr": {
            "meaning": "हे तुमचे हृदय दर मिनिटाला किती वेळा धडकते ते मोजते.",
            "effect": "ठोके खूप जास्त असणे हृदयावर ताण दर्शवते.",
            "solution": "शांत राहा, दीर्घ श्वास घ्या, विश्रांती घ्या आणि ठोके जास्त राहिल्यास तातडीने तपासणी करा."
        }
    },
    "hemoglobin": {
        "hi": {
            "meaning": "यह लाल रक्त कोशिकाओं में मौजूद प्रोटीन है जो पूरे शरीर में ऑक्सीजन पहुंचाने का काम करता है।",
            "effect": "कम हीमोग्लोबिन एनीमिया (खून की कमी), कमजोरी और सांस फूलने का कारण बनता है।",
            "solution": "आयरन युक्त आहार लें (पालक, गुड़, चना, अनार, चुकंदर, खजूर) और डॉक्टर की सलाह से सप्लीमेंट लें।"
        },
        "mr": {
            "meaning": "हा रक्तातील लाल पेशींमधील महत्त्वाचा घटक आहे जो शरीराच्या प्रत्येक अवयवाला ऑक्सिजन पोहोचवतो.",
            "effect": "हे प्रमाण कमी असल्यास अशक्तपणा, थकवा आणि धाप लागणे जाणवू शकते.",
            "solution": "लोहयुक्त आहार घ्या (पालक, गूळ, डाळिंब, बीट, खजूर) आणि डॉक्टरांच्या सल्ल्याने आयर्नच्या गोळ्या घ्या."
        }
    },
    "wbc": {
        "hi": {
            "meaning": "श्वेत रक्त कोशिकाएं शरीर की रोग प्रतिरोधक क्षमता (इम्यूनिटी) हैं जो कीटाणुओं और संक्रमण से लड़ती हैं।",
            "effect": "इनका बढ़ना शरीर में किसी संक्रमण (इन्फेक्शन) या सूजन का संकेत हो सकता है।",
            "solution": "संक्रमण के कारण का पता लगाने हेतु डॉक्टर से परामर्श करें, पर्याप्त आराम करें और ताजा पौष्टिक भोजन लें।"
        },
        "mr": {
            "meaning": "पांढऱ्या रक्तपेशी शरीराची रोगप्रतिकारक शक्ती असून संसर्गाशी (इन्फेक्शन) लढतात.",
            "effect": "हे प्रमाण वाढणे शरीरात जंतूसंसर्ग किंवा सूज असल्याचे दर्शवते.",
            "solution": "संसर्गाचे अचूक कारण शोधण्यासाठी डॉक्टरांचा सल्ला घ्या आणि पुरेशी विश्रांती घ्या."
        }
    },
    "platelets": {
        "hi": {
            "meaning": "ये रक्त कोशिकाएं चोट लगने पर खून का थक्का बनाकर अत्यधिक रक्तस्राव को रोकती हैं।",
            "effect": "प्लेटलेट्स बहुत कम होने से रक्तस्राव का जोखिम बढ़ सकता है।",
            "solution": "पपीते के पत्ते का रस, कीवी, नारियल पानी लें और प्लेटलेट की स्थिति पर डॉक्टर से तत्काल परामर्श करें।"
        },
        "mr": {
            "meaning": "या पेशी जखम झाल्यावर रक्त गोठण्यास आणि रक्तस्त्राव थांबवण्यास मदत करतात.",
            "effect": "प्रमाण कमी झाल्यास रक्तस्त्रावाचा धोका वाढू शकतो.",
            "solution": "किवी, पपईच्या पानांचा रस घ्या आणि प्लेटलेट्स नियंत्रणासाठी त्वरित डॉक्टरांना भेटा."
        }
    },
    "glucose": {
        "hi": {
            "meaning": "यह रक्त में शर्करा (शुगर) की मात्रा को मापता है जो शरीर की ऊर्जा का मुख्य स्रोत है।",
            "effect": "अधिक शुगर प्रीडायबिटीज या डायबिटीज का संकेत देती है।",
            "solution": "मीठा व मैदे से बनी चीजें बंद करें, रोज 30 मिनट टहलें और डॉक्टर के अनुसार दवा या जांच कराएं।"
        },
        "mr": {
            "meaning": "हे रक्तातील साखरेचे (ग्लुकोज) प्रमाण मोजते.",
            "effect": "साखरेचे प्रमाण वाढल्यास मधुमेहाचा (डायबिटीज) धोका असतो.",
            "solution": "गोड पदार्थ टाळा, रोज नियमित व्यायाम करा आणि डॉक्टरांच्या मार्गदर्शनानुसार औषधोपचार घ्या."
        }
    }
}


def _get_offline_param_info(param_name: str, lang_code: str) -> Dict[str, str]:
    """Retrieves localized plain-language meanings, clinical effects, and fixes for offline use."""
    name_clean = param_name.lower()
    for key, data in OFFLINE_PARAM_TRANSLATIONS.items():
        if key in name_clean or name_clean in key:
            lang_data = data.get(lang_code, data.get("hi", {}))
            if lang_data:
                return lang_data

    # Generic native translation fallback
    if lang_code == "mr":
        return {
            "meaning": f"हा {param_name} चाचणीचा परिणाम शरीराची कार्यप्रणाली दर्शवतो.",
            "effect": "प्रमाण सामान्य मर्यादेबाहेर असणे वैद्यकीय सल्ल्याची गरज दर्शवते.",
            "solution": "योग्य तपासणी आणि उपचारांसाठी तुमच्या डॉक्टरांचा सल्ला घ्या."
        }
    return {
        "meaning": f"यह {param_name} टेस्ट आपके शरीर की स्वास्थ्य स्थिति और अंगों की कार्यप्रणाली को दर्शाता है।",
        "effect": "मान सामान्य सीमा से बाहर होना किसी अंतर्निहित स्वास्थ्य असंतुलन का संकेत हो सकता है।",
        "solution": "उचित निदान, आहार सुधार और आवश्यक उपचार के लिए अपने डॉक्टर से परामर्श करें।"
    }


def build_english_summary(
    patient_meta: Dict[str, Any],
    parameters: List[Dict[str, Any]],
    clinical_insights: Dict[str, Any],
    summary_stats: Dict[str, Any]
) -> str:
    """Generates a structured, empathetic, non-jargon English medical report summary (offline fallback)."""
    name = patient_meta.get("name", "Patient")
    age = patient_meta.get("age", "N/A")
    gender = patient_meta.get("gender", "N/A")
    doctor = patient_meta.get("doctor", "Consultant Physician")

    risk = summary_stats.get("overall_health_risk", "NORMAL")
    abnormal_cnt = clinical_insights.get("abnormal_parameter_count", 0)

    lines = []
    lines.append(f"# Medical Health Analysis & Report Summary")
    lines.append(f"**Patient:** {name} | **Age/Gender:** {age} yrs, {gender} | **Doctor:** {doctor}")
    lines.append("-" * 60)

    # 1. Overview
    lines.append("\n### 1. Executive Summary")
    if risk == "CRITICAL":
        lines.append(
            f"⚠️ **CRITICAL MEDICAL ALERT:** The laboratory analysis detected **{abnormal_cnt} abnormal parameter(s)**, "
            f"with critical values that require immediate medical attention and urgent doctor consultation."
        )
    elif risk == "ATTENTION_REQUIRED":
        lines.append(
            f"ℹ️ **ATTENTION REQUIRED:** The laboratory analysis detected **{abnormal_cnt} parameter(s) outside standard reference ranges**. "
            f"While not immediately critical, these findings warrant medical review with your doctor for proper diagnosis and care."
        )
    else:
        lines.append(
            f"✅ **NORMAL HEALTH PROFILE:** All detected medical parameters are within standard healthy physiological reference ranges. "
            f"Continue routine wellness checkups and healthy lifestyle practices."
        )

    # 2. Key Findings & Solutions
    lines.append("\n### 2. Key Findings & How to Improve Your Parameters")
    parameter_insights = clinical_insights.get("parameter_insights", [])
    if parameter_insights:
        for item in parameter_insights:
            p_name = item.get("parameter")
            val = item.get("value")
            unit = item.get("unit")
            status = item.get("status")
            ref = item.get("reference_range")
            meaning = item.get("simple_meaning", "")
            effects = item.get("possible_effects", "")

            badge = "🔴" if "CRITICAL" in status else ("🟡" if status in ["LOW", "HIGH"] else "🟢")
            lines.append(f"\n* **{badge} {p_name}: {val} {unit}** (Status: **{status}** | Healthy Range: {ref})")
            if meaning:
                lines.append(f"  * *What it measures:* {meaning}")
            if effects:
                lines.append(f"  * *Why it matters:* {effects}")
            lines.append(f"  * *How to improve:* Consult your physician for medical review, maintain proper hydration, and adhere to recommended dietary adjustments.")
    else:
        lines.append("All analyzed blood indices and metabolic parameters are within normal biological limits.")

    # 3. Possible Conditions
    possible_conditions = clinical_insights.get("possible_conditions", [])
    if possible_conditions:
        lines.append("\n### 3. Understanding Your Health Condition")
        lines.append("Based on the pattern of abnormal laboratory findings, your doctor may consider evaluating:")
        for cond in possible_conditions:
            lines.append(f"- **{cond}**")
        lines.append("\n*Understanding:* These conditions are manageable with timely medical intervention, lifestyle adaptations, and consistent follow-up checkups.")

    # 4. Dietary & Lifestyle Guidance
    dietary = clinical_insights.get("dietary_guidelines", [])
    lifestyle = clinical_insights.get("lifestyle_guidelines", [])
    lines.append("\n### 4. Dietary & Lifestyle Recommendations")
    if dietary:
        lines.append("**Nutritional Guidance:**")
        for tip in dietary:
            lines.append(f"- {tip}")
    if lifestyle:
        lines.append("\n**Lifestyle & Daily Care:**")
        for tip in lifestyle:
            lines.append(f"- {tip}")

    # 5. Doctor Checklist
    questions = clinical_insights.get("doctor_questions", [])
    if questions:
        lines.append("\n### 5. Questions to Ask Your Doctor Checklist")
        for q in questions:
            lines.append(f"[ ] {q}")

    # Disclaimer
    lines.append("\n" + "=" * 60)
    lines.append(
        "**Medical Disclaimer:** This report summary is generated by MedSaathi AI to assist in understanding laboratory metrics. "
        "It does not constitute a formal diagnosis or medical prescription. Always consult your healthcare provider for professional medical evaluation."
    )

    return "\n".join(lines)


def build_native_summary(
    lang_code: str,
    patient_meta: Dict[str, Any],
    parameters: List[Dict[str, Any]],
    clinical_insights: Dict[str, Any],
    summary_stats: Dict[str, Any]
) -> str:
    """
    Generates an authentic, 100% native language summary (Marathi, Hindi, Punjabi, etc.)
    with ZERO English sentences, used when running offline or as fallback.
    """
    t = NATIVE_TEMPLATES.get(lang_code, NATIVE_TEMPLATES["hi"])

    name = patient_meta.get("name", "रुग्ण / मरीज")
    age = patient_meta.get("age", "N/A")
    gender = patient_meta.get("gender", "N/A")
    doctor = patient_meta.get("doctor", "सल्लागार डॉक्टर / सलाहकार चिकित्सक")
    risk = summary_stats.get("overall_health_risk", "NORMAL")

    lines = []
    lines.append(f"# {t['title']}")
    lines.append(f"**{t['name']}:** {name} | **{t['age_gender']}:** {age} वर्ष, {gender} | **{t['doctor']}:** {doctor}")
    lines.append("-" * 60)

    # 1. Overview
    lines.append(f"\n### {t['sec_overview']}")
    if risk == "CRITICAL":
        lines.append(f"⚠️ **{t['status_critical']}**")
    elif risk == "ATTENTION_REQUIRED":
        lines.append(f"ℹ️ **{t['status_attention']}**")
    else:
        lines.append(f"✅ **{t['status_normal']}**")

    # 2. Key Findings & Solutions (100% Native Language!)
    lines.append(f"\n### {t['sec_findings']}")
    parameter_insights = clinical_insights.get("parameter_insights", [])
    if parameter_insights:
        for item in parameter_insights:
            p_name = item.get("parameter")
            val = item.get("value")
            unit = item.get("unit")
            status_raw = item.get("status", "")
            ref = item.get("reference_range", "")

            # Native status & badge
            status_native = t["normal"]
            badge = "🟢"
            if "CRITICAL LOW" in status_raw:
                status_native = t["critical_low"]
                badge = "🔴"
            elif "CRITICAL HIGH" in status_raw:
                status_native = t["critical_high"]
                badge = "🔴"
            elif "LOW" in status_raw:
                status_native = t["low"]
                badge = "🟡"
            elif "HIGH" in status_raw:
                status_native = t["high"]
                badge = "🟡"

            # Fetch 100% native translations for meaning, effect, and fix
            native_info = _get_offline_param_info(p_name, lang_code)

            lines.append(f"\n* **{badge} {p_name}: {val} {unit}** ({status_native} | {t['ref_range']} {ref})")
            lines.append(f"  * *{t['meaning']}* {native_info['meaning']}")
            lines.append(f"  * *प्रभाव:* {native_info['effect']}")
            lines.append(f"  * *{t['solution']}* {native_info['solution']}")
    else:
        lines.append(f"{t['status_normal']}")

    # 3. Possible Conditions
    possible_conditions = clinical_insights.get("possible_conditions", [])
    if possible_conditions:
        lines.append(f"\n### {t['sec_conditions']}")
        intro = "या चाचणी परिणामांच्या आधारे खालील संभाव्य आरोग्य स्थितींवर डॉक्टरांशी चर्चा करावी:" if lang_code == "mr" else "इन जांच परिणामों के आधार पर निम्नलिखित संभावित स्थितियों पर डॉक्टर से परामर्श करना चाहिए:"
        lines.append(intro)
        for cond in possible_conditions:
            lines.append(f"- **{cond}**")
        note = "मार्गदर्शन: नियमित वैद्यकीय तपासणी, वेळेवर औषधोपचार आणि संतुलित आहाराने या स्थिती नियंत्रणात ठेवता येतात." if lang_code == "mr" else "मार्गदर्शन: नियमित चिकित्सीय परामर्श, समय पर दवाइयों और अनुशासित जीवनशैली से इन स्थितियों को पूरी तरह नियंत्रित किया जा सकता है।"
        lines.append(f"\n*{note}*")

    # 4. Dietary & Lifestyle Guidance
    dietary = clinical_insights.get("dietary_guidelines", [])
    lifestyle = clinical_insights.get("lifestyle_guidelines", [])
    lines.append(f"\n### {t['sec_diet_lifestyle']}")
    if dietary:
        lines.append(f"**{t['sub_diet']}:**")
        for tip in dietary:
            lines.append(f"- {tip}")
    if lifestyle:
        lines.append(f"\n**{t['sub_lifestyle']}:**")
        for tip in lifestyle:
            lines.append(f"- {tip}")

    # 5. Doctor Checklist
    questions = clinical_insights.get("doctor_questions", [])
    if questions:
        lines.append(f"\n### {t['sec_doctor_checklist']}")
        for q in questions:
            lines.append(f"[ ] {q}")

    # Disclaimer
    lines.append("\n" + "=" * 60)
    lines.append(f"**{t['disclaimer_title']}** {t['disclaimer']}")

    return "\n".join(lines)


def _call_gemini_summary(
    patient_meta: Dict[str, Any],
    parameters: List[Dict[str, Any]],
    clinical_insights: Dict[str, Any],
    summary_stats: Dict[str, Any],
    target_language: str
) -> Optional[str]:
    """
    Calls Google Gemini (gemini-3.6-flash) to craft an empathetic, highly structured,
    plain-language medical report summary with 100% native language immersion.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.6-flash")

        name = patient_meta.get("name", "Patient")
        age = patient_meta.get("age", "N/A")
        gender = patient_meta.get("gender", "N/A")
        doctor = patient_meta.get("doctor", "Consultant Physician")
        symptoms = patient_meta.get("disease_symptoms", "")
        risk = summary_stats.get("overall_health_risk", "NORMAL")

        # Format parameter details
        abnormal_params = []
        normal_params = []
        for p in parameters:
            line = f"- {p.get('parameter')}: {p.get('value')} {p.get('unit')} (Status: {p.get('status')}, Reference Range: {p.get('reference_range', 'N/A')})"
            if p.get("status") in ["LOW", "HIGH", "CRITICAL LOW", "CRITICAL HIGH"]:
                abnormal_params.append(line)
            else:
                normal_params.append(line)

        abnormal_block = "\n".join(abnormal_params) if abnormal_params else "None (All parameters within normal ranges)."
        normal_block = "\n".join(normal_params) if normal_params else "None."

        conditions = ", ".join(clinical_insights.get("possible_conditions", [])) or "None specifically identified."
        diet_tips = "\n".join([f"- {d}" for d in clinical_insights.get("dietary_guidelines", [])])
        lifestyle_tips = "\n".join([f"- {l}" for l in clinical_insights.get("lifestyle_guidelines", [])])
        doctor_questions = "\n".join([f"- {q}" for q in clinical_insights.get("doctor_questions", [])])

        lang_key = target_language.strip().lower()
        lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES["marathi"])
        is_native = lang_info["code"] != "en"
        target_lang_label = lang_info["label"]
        target_native_label = lang_info["native"]

        # Specific section titles for the requested language
        t = NATIVE_TEMPLATES.get(lang_info["code"], NATIVE_TEMPLATES["hi"])
        
        if is_native:
            sec1_title = t["sec_overview"]
            sec2_title = t["sec_findings"]
            sec3_title = t["sec_conditions"]
            sec4_title = t["sec_diet_lifestyle"]
            sub_diet = t["sub_diet"]
            sub_lifestyle = t["sub_lifestyle"]
            sec5_title = t["sec_doctor_checklist"]
            sec6_title = t["disclaimer_title"]

            language_directive = f"""
CRITICAL TRANSLATION & LANGUAGE RULES:
1. You MUST write the entire response 100% in pure, natural, conversational, and empathetic {target_lang_label} ({target_native_label}).
2. Do NOT leave ANY English sentences, English explanations, or English advice anywhere in the response!
3. All section titles, bullet points, explanations, dietary guidance, lifestyle tips, and doctor checklist questions MUST be in {target_lang_label}.
4. Use everyday, easily understood language (सरल और आम बोलचाल की भाषा) so that any common person or family member can understand every single point without fear or confusion.
5. Medical parameters may retain their standard medical acronym in brackets alongside the native name (e.g., 'ईजीएफआर (eGFR)', 'हीमोग्लोबिन (Hb)', 'पोटेशियम (Potassium)'), but their meanings and solutions must be 100% in {target_lang_label}.
6. Use these EXACT section headings:
   ### {sec1_title}
   ### {sec2_title}
   ### {sec3_title}
   ### {sec4_title}
     **{sub_diet}:**
     **{sub_lifestyle}:**
   ### {sec5_title}
   ### {sec6_title}
"""
        else:
            sec1_title = "1. Executive Summary"
            sec2_title = "2. Key Findings & How to Improve Your Parameters"
            sec3_title = "3. Understanding Your Health Condition"
            sec4_title = "4. Dietary & Lifestyle Recommendations"
            sub_diet = "Nutritional Guidance"
            sub_lifestyle = "Lifestyle & Daily Care"
            sec5_title = "5. Questions to Ask Your Doctor Checklist"
            sec6_title = "Medical Disclaimer"

            language_directive = """
CRITICAL LANGUAGE RULES:
Write the entire summary in clear, warm, compassionate, and patient-friendly English without intimidating medical jargon.
Use these EXACT section headings:
   ### 1. Executive Summary
   ### 2. Key Findings & How to Improve Your Parameters
   ### 3. Understanding Your Health Condition
   ### 4. Dietary & Lifestyle Recommendations
     **Nutritional Guidance:**
     **Lifestyle & Daily Care:**
   ### 5. Questions to Ask Your Doctor Checklist
   ### Medical Disclaimer
"""

        prompt = f"""You are MedSaathi AI, a compassionate, expert AI medical assistant dedicated to helping everyday patients clearly understand their laboratory diagnostic reports.
Your goal is to explain this medical report to the patient in simple, non-intimidating, and easy-to-understand language.

PATIENT & LAB METADATA:
- Patient Name: {name}
- Age: {age} years
- Gender: {gender}
- Consulting Doctor / Lab: {doctor}
- Patient-Reported Disease / Symptoms: {symptoms if symptoms else "None reported by patient"}
- Overall Health Risk Level: {risk}

LABORATORY PARAMETERS EXTRACTED:
Abnormal / Attention Parameters:
{abnormal_block}

Normal Parameters:
{normal_block}

CLINICAL KNOWLEDGE BASE CORRELATIONS:
- Connected Potential Conditions: {conditions}
- Condition-Specific Dietary Guidelines:
{diet_tips}
- Condition-Specific Lifestyle Guidelines:
{lifestyle_tips}
- Suggested Questions for Doctor:
{doctor_questions}

{language_directive}

REQUIRED CONTENT FOR EACH SECTION:
1. Executive Summary:
   - Provide a 2-3 sentence reassuring overview of the entire report: what is normal, what needs attention or if there is a critical alert, and a comforting message to not panic.

2. Key Findings & Parameter Improvement Measures:
   - For every abnormal test (High, Low, or Critical):
     a) Explain what this parameter measures in simple, plain language.
     b) Explain why it is out of range and what happened in the body.
     c) SPECIFIC MEASURES TO IMPROVE / FIX IT: Clearly explain how the patient can bring this parameter back to normal (e.g. hydration, specific foods, doctor consultation for medicine, regular monitoring).

3. Understanding Your Health Condition:
   - Connect the abnormal parameters together!
   - If a disease/condition is indicated (e.g., Kidney disease, Anemia, Infection, Heart strain, Diabetes) or if the patient reported a disease:
     a) Educate the patient in simple terms: What is this disease/condition?
     b) Why did it occur based on the combination of lab tests that increased or decreased?
     c) Provide reassuring, empowering steps on how to recover, emphasizing doctor consultation and regular checkups.

4. Dietary & Lifestyle Recommendations:
   - This section MUST be strictly tailored to the specific diagnosed/suspected condition (e.g. if kidney disease, renal-friendly advice like low-sodium, controlled potassium/phosphorus, adequate hydration; if anemia, iron & vitamin C rich foods; if diabetes, blood sugar control).
   - **{sub_diet}:** Specific foods to eat and foods to strictly avoid for this condition.
   - **{sub_lifestyle}:** Daily habits, safe physical activity, hydration rules, rest, and follow-up habits tailored to this condition.

5. Questions to Ask Your Doctor Checklist:
   - Provide 4-5 practical, targeted questions the patient should ask their doctor during their next visit (e.g., questions about root cause, medication adjustments, lifestyle restrictions, and follow-up tests) so they feel confident and informed.

6. Medical Disclaimer:
   - Include a respectful reminder that this AI summary assists with health literacy and does not replace a professional doctor's clinical diagnosis.

Remember: Be compassionate, practical, and clear. Empower the patient with understanding and hope!"""

        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"[WARNING] Gemini LLM summary generation failed ({e}). Falling back to local clinical engine.")
        return None

    return None


def generate_bilingual_medical_summary(
    patient_meta: Dict[str, Any],
    parameters: List[Dict[str, Any]],
    clinical_insights: Dict[str, Any],
    summary_stats: Dict[str, Any],
    preferred_language: str = "English"
) -> Dict[str, Any]:
    """
    Main orchestrator that produces both English and Native Language summaries.
    Uses Google Gemini 3.6 Flash when GEMINI_API_KEY is active, with seamless
    automatic fallback to the local clinical intelligence engine if offline.
    """
    lang_key = preferred_language.strip().lower()
    lang_info = SUPPORTED_LANGUAGES.get(lang_key, SUPPORTED_LANGUAGES["marathi"])
    lang_code = lang_info["code"]
    lang_label = lang_info["label"]
    lang_native_label = lang_info["native"]

    # 1. Generate English Summary via Gemini LLM (with fallback)
    english_summary = _call_gemini_summary(
        patient_meta, parameters, clinical_insights, summary_stats, "English"
    )
    if not english_summary:
        english_summary = build_english_summary(
            patient_meta, parameters, clinical_insights, summary_stats
        )

    # 2. Generate Native Language Summary via Gemini LLM (with fallback)
    if lang_code == "en":
        native_summary = english_summary
    else:
        native_summary = _call_gemini_summary(
            patient_meta, parameters, clinical_insights, summary_stats, lang_label
        )
        if not native_summary:
            native_summary = build_native_summary(
                lang_code, patient_meta, parameters, clinical_insights, summary_stats
            )

    return {
        "preferred_language": lang_info["label"],
        "language_code": lang_code,
        "language_native_label": lang_native_label,
        "summary_english": english_summary,
        "summary_native": native_summary
    }
