import ollama
import os
import re
import time
import importlib
from app.config import settings
from app.llm_lock import ollama_lock

def _load_optional_nltk_tokenizers():
    try:
        tokenize_module = importlib.import_module("nltk.tokenize")
        punkt_module = importlib.import_module("nltk.tokenize.punkt")
        toktok_cls = getattr(tokenize_module, "ToktokTokenizer", None)
        punkt_cls = getattr(punkt_module, "PunktSentenceTokenizer", None)
        if toktok_cls is None or punkt_cls is None:
            return None, None
        return toktok_cls(), punkt_cls()
    except Exception:
        return None, None

# deep-translator language codes for Indian languages
# GoogleTranslator uses BCP-47 / ISO 639-1 codes matching what we already store.
_GOOGLE_LANG_MAP = {
    "hi": "hi",  # Hindi
    "mr": "mr",  # Marathi
    "ta": "ta",  # Tamil
    "te": "te",  # Telugu
    "kn": "kn",  # Kannada
    "bn": "bn",  # Bengali
    "gu": "gu",  # Gujarati
}

_LANGUAGE_NAME_MAP = {
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali",
    "gu": "Gujarati",
}

_LANGUAGE_SCRIPT_GROUP = {
    "hi": "devanagari",
    "mr": "devanagari",
    "bn": "bengali",
    "gu": "gujarati",
    "ta": "tamil",
    "te": "telugu",
    "kn": "kannada",
}

_SCRIPT_GROUP_PATTERNS = {
    "devanagari": re.compile(r"[\u0900-\u097f]"),
    "bengali": re.compile(r"[\u0980-\u09ff]"),
    "gujarati": re.compile(r"[\u0a80-\u0aff]"),
    "tamil": re.compile(r"[\u0b80-\u0bff]"),
    "telugu": re.compile(r"[\u0c00-\u0c7f]"),
    "kannada": re.compile(r"[\u0c80-\u0cff]"),
}

_TOKEN_CONTENT_PATTERN = re.compile(r"[A-Za-z0-9\u0900-\u0D7F]")
_NLTK_WORD_TOKENIZER, _NLTK_SENTENCE_TOKENIZER = _load_optional_nltk_tokenizers()

_LOCALIZED_COMPLAINT_TEMPLATES = {
    "hi": {
        "subject": "विषय: तत्काल नागरिक शिकायत - {subject_issue} के संबंध में तत्काल कार्रवाई आवश्यक",
        "dear": "प्रिय {department},",
        "intro": "मैं सार्वजनिक हित से जुड़ी एक तात्कालिक समस्या आपकी जानकारी में लाने के लिए लिख रहा/रही हूँ।",
        "evidence": "संलग्न फोटोग्राफ में यह समस्या दिखाई दे रही है: {issue_phrase}।",
        "location_known": "ध्यान देने योग्य स्थान: {location}।",
        "location_unknown": "मेटाडेटा से सटीक स्थान की पुष्टि नहीं हो सकी, लेकिन संलग्न साक्ष्य से स्पष्ट है कि यह मामला आपके अधिकार क्षेत्र में आता है।",
        "risk": "यदि इस पर तुरंत कार्रवाई नहीं हुई, तो {risk_hint} का जोखिम बढ़ सकता है।",
        "action": "{action_hint}।",
        "close": "जनहित और सार्वजनिक सुरक्षा के लिए कृपया शीघ्र हस्तक्षेप करें।",
        "sincerely": "सादर,",
        "citizen": "चिंतित नागरिक",
    },
    "mr": {
        "subject": "विषय: तातडीची नागरी तक्रार - {subject_issue} बाबत तात्काळ कारवाई आवश्यक",
        "dear": "प्रिय {department},",
        "intro": "सार्वजनिक हिताशी संबंधित तातडीचा मुद्दा आपल्या निदर्शनास आणण्यासाठी मी लिहित आहे.",
        "evidence": "जोडलेल्या छायाचित्रात ही समस्या स्पष्ट दिसत आहे: {issue_phrase}.",
        "location_known": "लक्ष देण्याची जागा: {location}.",
        "location_unknown": "मेटाडेटामधून अचूक स्थान निश्चित झाले नाही, परंतु जोडलेल्या पुराव्यांवरून हा मुद्दा आपल्या कार्यक्षेत्रात येतो हे स्पष्ट होते.",
        "risk": "यावर तात्काळ कारवाई न झाल्यास {risk_hint} चा धोका वाढू शकतो.",
        "action": "{action_hint}.",
        "close": "जनहित आणि सार्वजनिक सुरक्षिततेच्या दृष्टीने कृपया त्वरीत हस्तक्षेप करावा.",
        "sincerely": "आपला नम्र,",
        "citizen": "चिंताग्रस्त नागरिक",
    },
    "ta": {
        "subject": "பொருள்: அவசர குடிமக்கள் புகார் - {subject_issue} குறித்து உடனடி நடவடிக்கை தேவை",
        "dear": "அன்புள்ள {department},",
        "intro": "பொது நலனுடன் தொடர்புடைய அவசர பிரச்சினையை உங்கள் கவனத்திற்கு கொண்டு வர நான் எழுதுகிறேன்.",
        "evidence": "இணைக்கப்பட்ட புகைப்படத்தில் இந்த பிரச்சினை தெளிவாக தெரிகிறது: {issue_phrase}.",
        "location_known": "கவனம் தேவைப்படும் இடம்: {location}.",
        "location_unknown": "மெட்டாடேட்டாவில் துல்லியமான இடம் உறுதியாகவில்லை, ஆனால் இணைக்கப்பட்ட சான்று இந்த பிரச்சினை உங்கள் அதிகார வரம்பில் உள்ளதை காட்டுகிறது.",
        "risk": "உடனடி நடவடிக்கை எடுக்கப்படாவிட்டால் {risk_hint} என்ற ஆபத்து அதிகரிக்கலாம்.",
        "action": "{action_hint}.",
        "close": "பொது பாதுகாப்பும் பொதுநலனும் கருதி தயவுசெய்து விரைந்து தலையீடு செய்யவும்.",
        "sincerely": "மரியாதையுடன்,",
        "citizen": "கவலைப்படும் குடிமகன்",
    },
    "te": {
        "subject": "విషయం: అత్యవసర పౌర ఫిర్యాదు - {subject_issue} గురించి తక్షణ చర్య అవసరం",
        "dear": "ప్రియమైన {department},",
        "intro": "ప్రజా ప్రయోజనానికి సంబంధించిన అత్యవసర సమస్యను మీ దృష్టికి తీసుకురావడానికి నేను ఈ లేఖ రాస్తున్నాను.",
        "evidence": "జతచేసిన ఫోటోలో ఈ సమస్య స్పష్టంగా కనిపిస్తోంది: {issue_phrase}.",
        "location_known": "శ్రద్ధ అవసరమైన స్థలం: {location}.",
        "location_unknown": "మెటాడేటా ద్వారా ఖచ్చితమైన స్థానం నిర్ధారించలేకపోయినా, జతచేసిన ఆధారాల ప్రకారం ఈ విషయం మీ అధికార పరిధిలోకి వస్తుంది.",
        "risk": "తక్షణ చర్య తీసుకోకపోతే {risk_hint} అనే ప్రమాదం పెరగవచ్చు.",
        "action": "{action_hint}.",
        "close": "ప్రజల భద్రత మరియు ప్రజాహితాన్ని దృష్టిలో ఉంచుకుని దయచేసి వెంటనే జోక్యం చేసుకోండి.",
        "sincerely": "వినయపూర్వకం,",
        "citizen": "ఆందోళన చెందిన పౌరుడు",
    },
    "kn": {
        "subject": "ವಿಷಯ: ತುರ್ತು ನಾಗರಿಕ ದೂರು - {subject_issue} ಕುರಿತು ತಕ್ಷಣ ಕ್ರಮ ಅಗತ್ಯ",
        "dear": "ಮಾನ್ಯ {department},",
        "intro": "ಸಾರ್ವಜನಿಕ ಹಿತಾಸಕ್ತಿಗೆ ಸಂಬಂಧಿಸಿದ ತುರ್ತು ವಿಷಯವನ್ನು ನಿಮ್ಮ ಗಮನಕ್ಕೆ ತರಲು ನಾನು ಬರೆಯುತ್ತಿದ್ದೇನೆ.",
        "evidence": "ಲಗತ್ತಿಸಲಾದ ಫೋಟೋದಲ್ಲಿ ಈ ಸಮಸ್ಯೆ ಸ್ಪಷ್ಟವಾಗಿ ಕಾಣುತ್ತಿದೆ: {issue_phrase}.",
        "location_known": "ಗಮನಿಸಬೇಕಾದ ಸ್ಥಳ: {location}.",
        "location_unknown": "ಮೆಟಾಡೇಟಾದಿಂದ ನಿಖರ ಸ್ಥಳ ದೃಢಪಡಿಸಲಾಗಲಿಲ್ಲ, ಆದರೆ ಲಗತ್ತಿಸಲಾದ ಸಾಕ್ಷ್ಯದಿಂದ ಇದು ನಿಮ್ಮ ವ್ಯಾಪ್ತಿಯ ವಿಷಯವೆಂದು ತಿಳಿಯುತ್ತದೆ.",
        "risk": "ಇದನ್ನು ತಕ್ಷಣ ಸರಿಪಡಿಸದಿದ್ದರೆ {risk_hint} ಎಂಬ ಅಪಾಯ ಹೆಚ್ಚಾಗಬಹುದು.",
        "action": "{action_hint}.",
        "close": "ಸಾರ್ವಜನಿಕ ಸುರಕ್ಷತೆ ಮತ್ತು ಜನಹಿತದ ದೃಷ್ಟಿಯಿಂದ ದಯವಿಟ್ಟು ಶೀಘ್ರ ಕ್ರಮ ಕೈಗೊಳ್ಳಿ.",
        "sincerely": "ವಂದನೆಗಳೊಂದಿಗೆ,",
        "citizen": "ಚಿಂತೆಗೊಂಡ ನಾಗರಿಕ",
    },
    "bn": {
        "subject": "বিষয়: জরুরি নাগরিক অভিযোগ - {subject_issue} সম্পর্কে অবিলম্বে ব্যবস্থা প্রয়োজন",
        "dear": "প্রিয় {department},",
        "intro": "জনস্বার্থের সঙ্গে যুক্ত একটি জরুরি বিষয় আপনার নজরে আনার জন্য আমি লিখছি।",
        "evidence": "সংযুক্ত ছবিতে এই সমস্যাটি স্পষ্টভাবে দেখা যাচ্ছে: {issue_phrase}।",
        "location_known": "যে স্থানে দ্রুত নজর প্রয়োজন: {location}।",
        "location_unknown": "মেটাডেটা থেকে সুনির্দিষ্ট অবস্থান নিশ্চিত করা যায়নি, তবে সংযুক্ত প্রমাণ থেকে বোঝা যায় বিষয়টি আপনার এখতিয়ারের মধ্যে পড়ে।",
        "risk": "দ্রুত ব্যবস্থা না নিলে {risk_hint} এর ঝুঁকি বাড়তে পারে।",
        "action": "{action_hint}।",
        "close": "জননিরাপত্তা ও জনস্বার্থে দয়া করে দ্রুত হস্তক্ষেপ করুন।",
        "sincerely": "শ্রদ্ধাসহ,",
        "citizen": "উদ্বিগ্ন নাগরিক",
    },
    "gu": {
        "subject": "વિષય: તાત્કાલિક નાગરિક ફરિયાદ - {subject_issue} અંગે તાત્કાલિક કાર્યવાહી જરૂરી",
        "dear": "પ્રિય {department},",
        "intro": "હું જાહેર હિત સાથે જોડાયેલી તાત્કાલિક સમસ્યાની જાણ કરવા માટે લખી રહ્યો/રહી છું.",
        "evidence": "જોડાયેલ ફોટોગ્રાફમાં નીચેની સમસ્યા સ્પષ્ટ દેખાય છે: {issue_phrase}.",
        "location_known": "ધ્યાન આપવાની જગ્યા: {location}.",
        "location_unknown": "મેટાડેટાથી ચોક્કસ સ્થાનની પુષ્ટિ થઈ શકી નથી, પરંતુ જોડાયેલ પુરાવાથી સ્પષ્ટ છે કે આ મુદ્દો તમારા અધિકાર ક્ષેત્રમાં આવે છે.",
        "risk": "જો તાત્કાલિક કાર્યવાહી નહીં થાય, તો {risk_hint} નો જોખમ વધી શકે છે.",
        "action": "{action_hint}.",
        "close": "જાહેર સુરક્ષા અને જનહિત માટે કૃપા કરીને તરત જ હસ્તક્ષેપ કરો.",
        "sincerely": "આપનો વિશ્વાસુ,",
        "citizen": "ચિંતિત નાગરિક",
    },
}

_TARGET_COMPLAINT_WORDS = 67
_TARGET_MIN_WORDS = 62
_TARGET_MAX_WORDS = 72
_BAD_TRAILING_WORDS = {
    "a", "an", "the", "and", "or", "of", "to", "from", "with",
    "in", "on", "for", "by", "as", "at", "is", "are", "was", "were",
}
_UNKNOWN_LOCATION_MARKERS = (
    "not specified",
    "not available",
    "unknown",
    "unavailable",
    "cannot be determined",
    "metadata",
)

_LOW_INFO_HINTS = (
    "possibly",
    "maybe",
    "appears to be",
    "seems to be",
    "looks like",
    "object",
    "circular shape",
    "machinery",
    "equipment",
)

_CONCRETE_CIVIC_HINTS = (
    "fire", "flame", "smoke", "spark", "wire", "transformer", "panel",
    "tree", "branch", "pothole", "drain", "garbage", "street light",
    "waterlogging", "encroachment", "traffic", "sewage", "leak",
)

_COMPLAINT_OUTPUT_MODES = {"paragraph", "email"}
_TRANSLATION_CHUNK_MAX_CHARS = 420


def _normalize_text(text: str) -> str:
    out = " ".join(text.split())
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    out = re.sub(r"\.{2,}", ".", out)
    return out


def _tokenize_words(text: str) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []

    if _NLTK_WORD_TOKENIZER is not None:
        try:
            tokens = [
                token for token in _NLTK_WORD_TOKENIZER.tokenize(normalized)
                if _TOKEN_CONTENT_PATTERN.search(token)
            ]
            if tokens:
                return tokens
        except Exception:
            pass

    return re.findall(r"\S+", normalized)


def _split_sentences(text: str) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []

    if _NLTK_SENTENCE_TOKENIZER is not None:
        try:
            sentences = [part.strip() for part in _NLTK_SENTENCE_TOKENIZER.tokenize(normalized) if part.strip()]
            if sentences:
                return sentences
        except Exception:
            pass

    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def _is_unknown_location(address: str) -> bool:
    raw = (address or "").strip().lower()
    if not raw:
        return True
    return any(marker in raw for marker in _UNKNOWN_LOCATION_MARKERS)


def _issue_phrase_from_text(text: str) -> str:
    out = _normalize_text(text)
    out = re.sub(r"^(?:the|this)?\s*image\s+(?:shows|depicts|contains|captures)\s+", "", out, flags=re.IGNORECASE)
    out = re.sub(r"^a\s+close-?up\s+of\s+", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\b(?:this situation|this condition)\s+poses\b.*$", "", out, flags=re.IGNORECASE)
    out = re.sub(
        r"\b(?:appears?|is\s+visible|is\s+seen|can\s+be\s+seen)\s+in\s+the\s+"
        r"(?:foreground|background|attached\s+image)\b.*$",
        "",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(r"\b(?:in|of)\s+the\s+attached\s+image\b.*$", "", out, flags=re.IGNORECASE)

    sentences = _split_sentences(out)
    phrase = sentences[0] if sentences else out
    words = _tokenize_words(phrase)
    if len(words) > 26:
        phrase = " ".join(words[:26]).rstrip(",;:-")

    phrase = phrase.strip().rstrip(".")
    if not phrase:
        return "a potentially hazardous civic condition"
    return phrase


def _is_low_information_issue(text: str) -> bool:
    t = _normalize_text(text).lower()
    if not t:
        return True
    has_low_info_hint = any(h in t for h in _LOW_INFO_HINTS)
    has_concrete_hint = any(h in t for h in _CONCRETE_CIVIC_HINTS)
    return has_low_info_hint and not has_concrete_hint


def _department_issue_fallback(category: str) -> str:
    c = (category or "").lower()
    if any(k in c for k in ["fire", "rescue"]):
        return "a visible fire-related hazard in a public area"
    if any(k in c for k in ["electrical", "power", "discom"]):
        return "an unsafe electrical condition involving exposed or damaged components"
    if any(k in c for k in ["street lighting", "lighting"]):
        return "a non-functional or unsafe street-lighting condition"
    if any(k in c for k in ["road", "pwd", "civil", "pothole"]):
        return "a damaged road or public infrastructure condition"
    if any(k in c for k in ["horticulture", "park", "garden", "tree"]):
        return "an unsafe horticulture-related condition in a public green area"
    if any(k in c for k in ["enforcement", "traffic", "police"]):
        return "an obstruction or enforcement-related safety issue in public space"
    if any(k in c for k in ["health", "sanitation", "waste"]):
        return "an unhygienic sanitation condition affecting public health"
    return "an unsafe civic condition requiring immediate attention"


def _refine_issue_phrase(issue_text: str, category: str) -> str:
    phrase = _issue_phrase_from_text(issue_text)
    phrase = re.sub(r"\b(?:possibly|maybe|likely|appears to be|seems to be|looks like)\b", "", phrase, flags=re.IGNORECASE)
    phrase = _normalize_text(phrase).strip().rstrip(".,;:-")

    if _is_low_information_issue(phrase):
        return _department_issue_fallback(category)
    return phrase


def _department_risk_hint(category: str) -> str:
    c = (category or "").lower()
    if any(k in c for k in ["fire", "flame", "rescue"]):
        return "fire spread, injury, and property damage"
    if any(k in c for k in ["electrical", "power", "discom"]):
        return "electrocution, fire, and power disruption"
    if any(k in c for k in ["street lighting", "lighting"]):
        return "low visibility, safety threats, and avoidable accidents"
    if any(k in c for k in ["road", "pwd", "pothole"]):
        return "road accidents, vehicle damage, and commuter risk"
    if any(k in c for k in ["horticulture", "park", "garden", "tree"]):
        return "falling branches, obstruction of movement, and injury to pedestrians"
    if any(k in c for k in ["enforcement", "traffic", "police"]):
        return "traffic obstruction, unsafe movement, and collision risk"
    if any(k in c for k in ["water", "drain", "sewer"]):
        return "water contamination, sanitation concerns, and health risk"
    return "injury to citizens, disruption of civic services, and avoidable local damage"


def _department_action_hint(category: str) -> str:
    c = (category or "").lower()
    if any(k in c for k in ["fire", "flame", "rescue"]):
        return "Kindly deploy emergency response, secure the affected area, and neutralize the hazard"
    if any(k in c for k in ["electrical", "power", "discom"]):
        return "Kindly de-energize unsafe lines where required, rectify the electrical fault, and make the site safe"
    if any(k in c for k in ["street lighting", "lighting"]):
        return "Kindly restore lighting functionality and complete necessary repairs to ensure safe night-time movement"
    if any(k in c for k in ["road", "pwd", "civil", "pothole"]):
        return "Kindly inspect the site, carry out durable repairs, and restore safe public movement"
    if any(k in c for k in ["horticulture", "park", "garden", "tree"]):
        return "Kindly inspect the area, remove the immediate hazard, and complete horticulture maintenance without delay"
    if any(k in c for k in ["enforcement", "traffic", "police"]):
        return "Kindly conduct immediate on-ground enforcement, clear the obstruction, and restore orderly movement"
    if any(k in c for k in ["health", "sanitation", "waste"]):
        return "Kindly arrange immediate sanitation action, remove the source of nuisance, and disinfect the affected area"
    return "Kindly arrange immediate inspection and corrective action"


def _compact_location(address: str, max_words: int = 12) -> str:
    words = _tokenize_words(_normalize_text(address or ""))
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",;:-")


def _salutation_department(category: str) -> str:
    dep = (category or "").strip()
    if not dep:
        return "Concerned Department"
    dep_lower = dep.lower()
    if dep_lower.endswith("department") or dep_lower.endswith("authority") or dep_lower.endswith("cell"):
        return dep
    return f"{dep} Department"


def _compose_official_mail_text(issue_text: str, category: str, address: str) -> str:
    issue_phrase = _refine_issue_phrase(issue_text, category)
    department = (category or "").strip() or "concerned department"
    salutation_department = _salutation_department(department)
    risk_hint = _department_risk_hint(f"{department} {issue_phrase}")
    action_hint = _department_action_hint(department)

    if _is_unknown_location(address):
        location_line = ""
    else:
        location_line = f"The reported location is {_compact_location(address)}."

    location_part = f"{location_line} " if location_line else ""

    return (
        f"Dear {salutation_department}, the attached image indicates {issue_phrase}. "
        f"{location_part}"
        f"This issue may lead to {risk_hint} if not addressed promptly. "
        f"{action_hint}. "
        "Immediate attention is requested in public interest."
    )


def _compose_structured_email_text(issue_text: str, category: str, address: str) -> str:
    issue_phrase = _refine_issue_phrase(issue_text, category)
    department = (category or "").strip() or "Concerned Department"
    salutation_department = _salutation_department(department)
    risk_hint = _department_risk_hint(f"{department} {issue_phrase}")
    action_hint = _department_action_hint(department).strip().rstrip(". ")

    if _is_unknown_location(address):
        location_sentence = (
            "The exact location could not be confirmed from metadata, "
            "but the attached evidence indicates this issue is within your jurisdiction."
        )
    else:
        location_sentence = f"The specific location requiring attention is {_compact_location(address)}."

    subject_issue = issue_phrase[:1].upper() + issue_phrase[1:] if issue_phrase else "Civic Hazard"

    return (
        f"Subject: Urgent Civic Grievance - Immediate Action Required regarding **{subject_issue}**\n\n"
        f"Dear **{salutation_department}**,\n\n"
        "I am writing to formally bring to your attention a matter of public concern that requires urgent resolution. "
        f"The attached photographic evidence indicates **{issue_phrase}**. **{location_sentence}**\n\n"
        f"If left unaddressed, this issue poses a significant risk of **{risk_hint}**. "
        f"**{action_hint}**.\n\n"
        "Your prompt intervention in this matter is requested in the interest of public safety.\n\n"
        "Sincerely,\n"
        "Concerned Citizen"
    )


def _align_with_observed_issue(text: str, observed_issue: str) -> str:
    """
    Remove contradiction-style absence claims when the observed issue itself
    already indicates fire/smoke/sparks.
    """
    out = _normalize_text(text)
    issue = (observed_issue or "").lower()
    issue_has_fire_signal = any(k in issue for k in ["fire", "flame", "flames", "smoke", "burning", "spark", "sparks"])

    if issue_has_fire_signal:
        out = re.sub(
            r"\b(?:with\s+)?(?:there is|there's)?\s*no\s+(?:visible|clear\s+(?:indication|evidence)\s+of)\s+"
            r"(?:fire|smoke)(?:\s+or\s+(?:fire|smoke))?\.?\s*",
            "",
            out,
            flags=re.IGNORECASE,
        )

    # Repair common truncated phrase artifacts from small-model outputs.
    out = re.sub(r"\bcannot be determined from the\.?\b", "cannot be determined from metadata.", out, flags=re.IGNORECASE)

    # Remove common dangling connector left behind after phrase stripping.
    out = re.sub(r"\bin an area with\s+(?=The location\b)", "in the affected area. ", out, flags=re.IGNORECASE)
    out = re.sub(r"\bin an area\s+(?=The location\b)", "in the affected area. ", out, flags=re.IGNORECASE)

    # If phrase removal collapsed words (e.g., "withThe"), restore spacing.
    out = re.sub(r"([a-z])([A-Z])", r"\1 \2", out)

    return _normalize_text(out)


def _fit_to_target_words(text: str, target_words: int = _TARGET_COMPLAINT_WORDS) -> str:
    """
    Normalize a generated paragraph to a tight target range.

    This keeps UI output consistent and aligned with the requested style length.
    """
    sentences = _split_sentences(text)
    words: list[str] = []

    min_words = max(40, target_words - 5)
    max_words = target_words + 5

    # Prefer complete sentences so outputs never end mid-thought.
    used_sentence_count = 0
    if sentences:
        selected: list[str] = []
        used = 0
        for sentence in sentences:
            sentence_words = _tokenize_words(sentence)
            if not sentence_words:
                continue
            if used + len(sentence_words) <= max_words:
                selected.append(sentence)
                used += len(sentence_words)
                used_sentence_count += 1
            else:
                break

        if selected:
            words = _tokenize_words(" ".join(selected))

    if not words:
        words = _tokenize_words(_normalize_text(text))

    if len(words) > max_words:
        words = words[:max_words]
        # Avoid clipped sentence fragments at the boundary.
        while words and words[-1][-1] not in ".!?":
            words.pop()

    # If we're still short and there is an unselected sentence, consume part of it
    # before using generic filler so output stays content-rich.
    if len(words) < min_words and used_sentence_count < len(sentences):
        remaining = min_words - len(words)
        next_sentence_words = _tokenize_words(sentences[used_sentence_count])
        if next_sentence_words:
            take = min(len(next_sentence_words), remaining)
            words.extend(next_sentence_words[:take])
            # Remove awkward trailing stop words after partial sentence copy.
            while words and words[-1].strip(".,;:-").lower() in _BAD_TRAILING_WORDS:
                words.pop()

    if len(words) < min_words:
        filler_chunks: list[list[str]] = [
            ["Immediate", "attention", "is", "requested", "in", "public", "interest."],
            ["Necessary", "corrective", "measures", "may", "kindly", "be", "expedited."],
            ["This", "matter", "may", "please", "be", "treated", "as", "priority."],
            ["An", "early", "compliance", "update", "is", "requested."],
            ["Urgent", "intervention", "is", "solicited."],
            ["Without", "delay."],
            ["Today."],
        ]

        remaining = min_words - len(words)
        filler_idx = 0
        while remaining > 0:
            options = [c for c in filler_chunks if len(c) <= remaining]
            if not options:
                break
            current_text = " ".join(words).lower()
            non_repeating = [
                c for c in options
                if " ".join(c).lower().rstrip(".") not in current_text
            ]
            choose_from = non_repeating if non_repeating else options
            chunk = choose_from[filler_idx % len(choose_from)]
            filler_idx += 1
            words.extend(chunk)
            remaining -= len(chunk)

    # Keep outputs within upper bound if filler pushed us over.
    if len(words) > max_words:
        words = words[:max_words]
        while words and words[-1][-1] not in ".!?":
            words.pop()

    out = _normalize_text(" ".join(words).strip())
    out = out.rstrip(",;:-")
    if out and out[-1] not in ".!?":
        out += "."
    return out


def _split_for_translation(text: str, max_chars: int = _TRANSLATION_CHUNK_MAX_CHARS) -> list[str]:
    """
    Split long text into sentence/word-safe chunks suitable for translation APIs.
    """
    normalized = _normalize_text(text)
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]

    sentences = _split_sentences(normalized)
    if not sentences:
        sentences = [normalized]

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(sentence) <= max_chars:
            current = sentence
            continue

        words = _tokenize_words(sentence)
        segment = ""
        for word in words:
            candidate_segment = word if not segment else f"{segment} {word}"
            if len(candidate_segment) <= max_chars:
                segment = candidate_segment
            else:
                if segment:
                    chunks.append(segment)
                segment = word
        if segment:
            chunks.append(segment)

    if current:
        chunks.append(current)

    return chunks


def _translate_chunk(text: str, google_code: str) -> str | None:
    # Primary: Google Translate
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="en", target=google_code).translate(text)
        if isinstance(translated, str) and translated.strip():
            return translated.strip()
    except Exception:
        pass

    # Fallback: MyMemory
    try:
        from deep_translator import MyMemoryTranslator
        translated = MyMemoryTranslator(source="en", target=google_code).translate(text)
        if isinstance(translated, str) and translated.strip():
            return translated.strip()
    except Exception:
        pass

    return None


def _translation_model_name() -> str:
    preferred = getattr(settings, "translation_model", "")
    model_name = (preferred or settings.reasoning_model).strip()
    return model_name or settings.reasoning_model


def _ollama_translation_fallback_enabled() -> bool:
    return bool(getattr(settings, "enable_ollama_translation_fallback", False))


def _clean_translation_output(text: str) -> str:
    out = (text or "").strip()
    if out.startswith("```"):
        out = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", out)
        out = re.sub(r"\s*```$", "", out)
    if (out.startswith('"') and out.endswith('"')) or (out.startswith("'") and out.endswith("'")):
        out = out[1:-1].strip()
    return out


def _looks_like_translated_text(source_text: str, translated_text: str, target_lang: str) -> bool:
    translated = _normalize_text(translated_text or "")
    if not translated:
        return False

    source = _normalize_text(source_text or "")
    if source and translated.lower() == source.lower():
        return False

    normalized_lang = (target_lang or "").strip().lower()
    target_group = _LANGUAGE_SCRIPT_GROUP.get(normalized_lang)
    if not target_group:
        return False

    target_pattern = _SCRIPT_GROUP_PATTERNS.get(target_group)
    if not target_pattern:
        return False

    target_count = len(target_pattern.findall(translated))
    if target_count < 6:
        return False

    group_counts = {
        group: len(pattern.findall(translated))
        for group, pattern in _SCRIPT_GROUP_PATTERNS.items()
    }
    total_indic = sum(group_counts.values())
    if total_indic and (target_count / total_indic) < 0.78:
        return False

    for group, count in group_counts.items():
        if group == target_group or count == 0:
            continue
        if total_indic and (count / total_indic) > 0.22:
            return False

    return True


def _translation_is_effective(source_text: str, translated_text: str) -> bool:
    src = _normalize_text(source_text or "")
    dst = _normalize_text(translated_text or "")
    if not dst:
        return False
    if not src:
        return True
    return src.lower() != dst.lower()


def _has_excessive_repetition(text: str) -> bool:
    normalized = _normalize_text(text)
    if not normalized:
        return True

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) >= 4 and len(set(lines)) <= max(1, len(lines) // 2):
        return True

    words = [w.strip(".,;:!?()[]{}\"'").lower() for w in normalized.split()]
    words = [w for w in words if w]
    if len(words) < 16:
        return False

    n = 4
    counts: dict[tuple[str, ...], int] = {}
    for idx in range(0, len(words) - n + 1):
        key = tuple(words[idx: idx + n])
        counts[key] = counts.get(key, 0) + 1
        if counts[key] >= 3:
            return True

    return False


def _contains_translation_meta(text: str) -> bool:
    lowered = (text or "").lower()
    markers = (
        "target language",
        "text to translate",
        "translated text",
        "rules:",
        "translation:",
    )
    return any(marker in lowered for marker in markers)


def _translation_quality_ok(source_text: str, translated_text: str, target_lang: str) -> bool:
    if not _translation_is_effective(source_text, translated_text):
        return False
    if not _looks_like_translated_text(source_text, translated_text, target_lang):
        return False
    if _contains_translation_meta(translated_text):
        return False
    if _has_excessive_repetition(translated_text):
        return False
    return True


def _compose_localized_template_fallback(
    issue_text: str,
    category: str,
    address: str,
    target_lang: str,
    output_mode: str,
) -> str | None:
    normalized_lang = (target_lang or "").strip().lower()
    template = _LOCALIZED_COMPLAINT_TEMPLATES.get(normalized_lang)
    if not template:
        return None

    issue_phrase = _refine_issue_phrase(issue_text, category)
    department = (category or "").strip() or "Concerned Department"
    salutation_department = _salutation_department(department)
    risk_hint = _department_risk_hint(f"{department} {issue_phrase}")
    action_hint = _department_action_hint(department).strip().rstrip(". ")
    subject_issue = issue_phrase[:1].upper() + issue_phrase[1:] if issue_phrase else "Civic Hazard"

    location_sentence = (
        template["location_unknown"]
        if _is_unknown_location(address)
        else template["location_known"].format(location=_compact_location(address))
    )

    if output_mode == "email":
        return (
            f"{template['subject'].format(subject_issue=subject_issue)}\n\n"
            f"{template['dear'].format(department=salutation_department)}\n\n"
            f"{template['intro']}\n"
            f"{template['evidence'].format(issue_phrase=issue_phrase)} {location_sentence}\n\n"
            f"{template['risk'].format(risk_hint=risk_hint)} {template['action'].format(action_hint=action_hint)}\n\n"
            f"{template['close']}\n\n"
            f"{template['sincerely']}\n"
            f"{template['citizen']}"
        )

    localized_paragraph = (
        f"{template['dear'].format(department=salutation_department)} "
        f"{template['evidence'].format(issue_phrase=issue_phrase)} "
        f"{location_sentence} "
        f"{template['risk'].format(risk_hint=risk_hint)} "
        f"{template['action'].format(action_hint=action_hint)} "
        f"{template['close']}"
    )
    return _normalize_text(localized_paragraph)


def _translate_chunk_offline(
    text: str,
    target_lang: str,
    client: ollama.Client | None = None,
) -> str | None:
    normalized_lang = (target_lang or "").strip().lower()
    language_name = _LANGUAGE_NAME_MAP.get(normalized_lang)
    if not language_name:
        return None

    llm_client = client or ollama.Client(host=settings.ollama_base_url)

    system_prompt = (
        "You are an expert translator for Indian civic grievances. "
        "Translate accurately from English into the requested target language."
    )
    prompt = (
        f"Target language: {language_name} ({normalized_lang})\n"
        "Rules:\n"
        "1. Return only translated text.\n"
        "2. Preserve original meaning and tone exactly.\n"
        "3. Preserve punctuation, numbers, and proper nouns where appropriate.\n"
        "4. Use the native script of the target language (no Latin transliteration).\n\n"
        "Text to translate:\n"
        f"{text}"
    )

    try:
        response = llm_client.generate(
            model=_translation_model_name(),
            prompt=prompt,
            system=system_prompt,
            options={"temperature": 0.1},
        )
    except Exception:
        return None

    raw = ""
    if isinstance(response, dict):
        raw = str(response.get("response", ""))
    elif hasattr(response, "response"):
        raw = str(getattr(response, "response"))
    translated = _clean_translation_output(raw)

    if _looks_like_translated_text(text, translated, normalized_lang):
        return translated

    return None


def _translate(text: str, target_lang: str) -> str:
    """
    Translate `text` from English to `target_lang` using deep-translator.
    Falls back to the original English text if translation fails so the
    complaint is never lost.

    Primary:  GoogleTranslator (free, no API key, via unofficial API)
    Fallback: MyMemoryTranslator (free, 10K chars/day, no key)
    Optional fallback: local Ollama reasoning model (disabled by default)
    """
    normalized_lang = (target_lang or "").strip().lower()
    google_code = _GOOGLE_LANG_MAP.get(normalized_lang)
    if not google_code:
        return text  # unsupported language — return as-is

    if not isinstance(text, str) or not text.strip():
        return text

    # Fast path for short single-line text.
    if "\n" not in text and len(text) <= _TRANSLATION_CHUNK_MAX_CHARS:
        translated = _translate_chunk(text, google_code)
        if translated:
            print(f"[generator] Translated to {normalized_lang} via direct translation")
            return translated

        if _ollama_translation_fallback_enabled():
            offline_translated = _translate_chunk_offline(text, normalized_lang)
            if offline_translated:
                print(f"[generator] Translated to {normalized_lang} via offline Ollama fallback")
                return offline_translated

        print(f"[generator] Direct translation failed for {normalized_lang}, returning English text")
        return text

    translated_any = False
    used_offline_fallback = False
    translated_lines: list[str] = []
    offline_client: ollama.Client | None = None
    offline_client_unavailable = False
    offline_fallback_enabled = _ollama_translation_fallback_enabled()

    # Translate line-by-line to preserve email-style structure and avoid API size caps.
    for line in text.splitlines():
        if not line.strip():
            translated_lines.append("")
            continue

        chunks = _split_for_translation(line)
        if not chunks:
            translated_lines.append(line)
            continue

        translated_chunks: list[str] = []
        for chunk in chunks:
            translated_chunk = _translate_chunk(chunk, google_code)
            if not translated_chunk and offline_fallback_enabled:
                if offline_client is None and not offline_client_unavailable:
                    try:
                        offline_client = ollama.Client(host=settings.ollama_base_url)
                    except Exception:
                        offline_client_unavailable = True

                if offline_client is not None:
                    translated_chunk = _translate_chunk_offline(chunk, normalized_lang, client=offline_client)
                    if translated_chunk:
                        used_offline_fallback = True

            if translated_chunk:
                translated_chunks.append(translated_chunk)
                translated_any = True
            else:
                translated_chunks.append(chunk)

        translated_lines.append(" ".join(translated_chunks).strip())

    if translated_any:
        if used_offline_fallback and offline_fallback_enabled:
            print(f"[generator] Translated to {normalized_lang} using chunked translation with offline fallback")
        else:
            print(f"[generator] Translated to {normalized_lang} using chunked translation")
        return "\n".join(translated_lines)

    print(f"[generator] Translation failed for {normalized_lang}, returning English text")
    return text


def _get_loaded_model_names(client: ollama.Client, quiet: bool = False) -> tuple[list[str], bool]:
    """
    Return currently loaded Ollama model names.

    Returns:
        (names, status_known)
    """
    try:
        running = client.ps()
        running_models = running.models if hasattr(running, "models") else running.get("models", [])
        names: list[str] = []
        for m in running_models:
            if hasattr(m, "model"):
                raw_name = m.model
            elif isinstance(m, dict):
                raw_name = m.get("model", "")
            else:
                raw_name = ""
            names.append(raw_name if isinstance(raw_name, str) else str(raw_name or ""))
        return names, True
    except Exception as e:
        if not quiet:
            print(f"[generator] unable to query loaded models ({e}); using blind unload fallback")
        return [], False


def _wait_for_model_unload(client: ollama.Client, model_name: str, timeout: float | None = None) -> None:
    """
    Poll Ollama's running-models list until `model_name` is no longer present
    or `timeout` seconds have elapsed. The keep_alive=0 call is async on the
    Ollama side — without this wait llama3.2:1b starts loading while the vision
    model is still resident, causing OOM or slow generation.
    """
    effective_timeout = timeout if timeout is not None else settings.model_unload_timeout_seconds
    poll_interval = max(settings.model_unload_poll_interval_seconds, 0.05)

    deadline = time.monotonic() + effective_timeout
    while time.monotonic() < deadline:
        names, status_known = _get_loaded_model_names(client, quiet=True)
        if status_known and not any(model_name in n for n in names):
            return
        time.sleep(poll_interval)

    print(
        f"[generator] unload wait timed out for {model_name} after "
        f"{effective_timeout:.1f}s; continuing"
    )


def _effective_output_mode() -> str:
    mode = (settings.complaint_output_mode or "paragraph").strip().lower()
    if mode in _COMPLAINT_OUTPUT_MODES:
        return mode
    return "paragraph"


def generate_complaint(image_path, classification_result, user_details, location_details, language: str = "en"):
    """
    Generates a civic grievance description using the reasoning model (llama3.2:1b).

    Always uses text-only generation — the vision model has already run during
    classification and produced a structured description. Re-running the vision model
    here was the original bottleneck (60–250 s extra per request).
    """

    category = classification_result.get("department") or classification_result.get("label", "Civic Issue")
    reported_issue_text = _normalize_text(str((user_details or {}).get("reported_issue_text", ""))).strip()
    description = (
        reported_issue_text
        or classification_result.get("vision_description")
        or classification_result.get("label", "")
        or "A civic issue requiring attention"
    )
    address = location_details.get("address", "Location not specified")
    output_mode = _effective_output_mode()

    # ── Step 1: Always generate in English ───────────────────────────────────
    # Small models (1B) cannot reliably generate in Indian scripts.
    # We generate a quality English complaint, then post-translate it.
    if output_mode == "email":
        system_prompt = (
            "You are a formal civic grievance drafter for Indian government portals. "
            "Write highly professional, structured email complaints in plain English."
        )
        prompt = (
            f"Issue observed: {description}\n"
            f"Department: {category}\n"
            f"Location: {address}\n\n"
            "Draft a formal email complaint that includes:\n"
            "1. A clear Subject line.\n"
            "2. A formal salutation ('Dear <Department>,').\n"
            "3. A structured body with issue details, location, and risk.\n"
            "4. A clear action request.\n"
            "5. A formal sign-off ('Sincerely, Concerned Citizen').\n"
            "Rules: no markdown, no bullet points in final draft, "
            "never contradict the observed issue, and do not add absence statements "
            "like 'no visible fire/smoke' unless explicitly stated.\n\n"
            "Draft Email:"
        )
    else:
        system_prompt = (
            "You are a civic complaint drafting assistant for Indian government portals. "
            "Write formal, concise complaint descriptions in plain English."
        )
        prompt = (
            f"Issue observed: {description}\n"
            f"Department: {category}\n"
            f"Location: {address}\n\n"
            f"Write approximately {_TARGET_MIN_WORDS}-{_TARGET_MAX_WORDS} words in a professional official-mail tone as a single paragraph.\n"
            f"Rules: begin with 'Dear <Department>,', no sign-offs, no 'Subject:' line, no bullet points, "
            f"no meta-commentary, no markdown. "
            f"Never contradict the observed issue. "
            f"Do not add absence statements like 'no visible fire/smoke' unless explicitly stated in the observed issue. "
            f"Include: (1) issue observed, (2) risk/impact, (3) location availability status, "
            f"(4) clear action request to the concerned department.\n\n"
            f"Complaint description:"
        )

    with ollama_lock:
        try:
            client = ollama.Client(host=settings.ollama_base_url)

            # Check what is currently loaded before issuing unload requests.
            loaded_models, status_known = _get_loaded_model_names(client)
            vision_models_to_check = list(dict.fromkeys(
                m for m in [settings.vision_model, settings.mid_vision_model] if m
            ))

            for vision_model in vision_models_to_check:
                should_unload = (not status_known) or any(vision_model in lm for lm in loaded_models)
                if not should_unload:
                    print(f"[generator] {vision_model} not loaded; skipping unload")
                    continue
                try:
                    client.generate(model=vision_model, prompt="", keep_alive=0)
                    _wait_for_model_unload(client, vision_model)
                    print(f"[generator] {vision_model} unloaded, ready for {settings.reasoning_model}")
                    loaded_models, status_known = _get_loaded_model_names(client, quiet=True)
                except Exception:
                    pass

            response = client.generate(
                model=settings.reasoning_model,
                prompt=prompt,
                system=system_prompt,
                options={"temperature": 0.3},
            )
            if response is None:
                raise RuntimeError("Reasoning model returned no response.")
            raw = response["response"].strip()

            # Strip meta-commentary the small model sometimes prepends
            skip_prefixes = ("i'd", "i 'd", "here ", "note:", "sure", "certainly", "of course", "as requested")
            lines = [
                line for line in raw.splitlines()
                if not line.strip().lower().startswith(skip_prefixes)
            ]
            clean = "\n".join(lines).strip()

            # Unload reasoning model after use unless warm mode is enabled.
            if not settings.keep_reasoning_model_warm:
                try:
                    client.generate(model=settings.reasoning_model, prompt="", keep_alive=0)
                except Exception:
                    pass
            else:
                print(f"[generator] keeping {settings.reasoning_model} warm for faster follow-up requests")

            english_text = clean if clean else raw
            english_text = _align_with_observed_issue(english_text, description)
            preferred_issue_text = reported_issue_text or description
            source_issue = preferred_issue_text if len(_tokenize_words(preferred_issue_text)) >= 2 else english_text
            if output_mode == "email":
                english_text = _compose_structured_email_text(source_issue, category, address)
            else:
                english_text = _compose_official_mail_text(source_issue, category, address)
                english_text = _fit_to_target_words(english_text)

            # ── Step 2: Post-translate if a non-English language was requested ──
            if language and language != "en":
                translated_text = _translate(english_text, target_lang=language)
                if not _translation_quality_ok(english_text, translated_text, language):
                    localized_fallback = _compose_localized_template_fallback(
                        source_issue,
                        category,
                        address,
                        language,
                        output_mode,
                    )
                    if localized_fallback:
                        print(f"[generator] Translation fallback used deterministic template for {language}")
                        translated_text = localized_fallback
                english_text = translated_text

            return english_text

        except Exception as e:
            print(f"[generator] Draft generation failed ({e}); using deterministic complaint template")
            preferred_issue_text = reported_issue_text or description
            fallback_source = preferred_issue_text if len(_tokenize_words(preferred_issue_text)) >= 2 else "A civic issue requiring attention"
            if output_mode == "email":
                fallback = _compose_structured_email_text(fallback_source, category, address)
            else:
                fallback = _compose_official_mail_text(fallback_source, category, address)
                fallback = _fit_to_target_words(fallback)
            if language and language != "en":
                translated_fallback = _translate(fallback, target_lang=language)
                if not _translation_quality_ok(fallback, translated_fallback, language):
                    localized_fallback = _compose_localized_template_fallback(
                        fallback_source,
                        category,
                        address,
                        language,
                        output_mode,
                    )
                    if localized_fallback:
                        print(f"[generator] Exception-path translation fallback used deterministic template for {language}")
                        translated_fallback = localized_fallback
                fallback = translated_fallback
            return fallback
