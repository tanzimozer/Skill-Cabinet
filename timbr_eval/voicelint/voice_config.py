
# voice_config.py — Lexical fingerprints for TIMBR voice registers

SECTION_VOICE_MAP = {
    "Training": "athletic",
    "Nutrition": "people",
    "Supplements": "fitt",
    "Recovery": "fitt",
    "Culture": "athletic",
    "Social": "people",
    "Nightlife": "fitt",
}

ATHLETIC_POSITIVE = [
    r'\b(?:says|said|explains|notes|adds|argues|told|according to)\b',
    r'\bAt (?:the )?[A-Z][a-zA-Z]+\b',
    r'\bIn (?:the )?[A-Z][a-zA-Z]+\b',
    r'\d+\s*(?:%|percent|miles|minutes|pounds|lbs|kg|hours|days|weeks)',
    r'[A-Z][a-z]+,\s*\d{2},',
    r'[A-Z][a-z]+\s[A-Z][a-z]+,\s*[a-z]+\s+at\s+[A-Z]',
]
ATHLETIC_NEGATIVE = [
    r'!',
    r'\b(?:you should|you can|you need|get ready|are you ready|it is time)\b',
    r'\b(?:amazing|incredible|awesome|fantastic|wonderful)\b',
]

PEOPLE_POSITIVE = [
    r'^[A-Z][a-z]+\s[A-Z][a-z]+',
    r'\b(?:who|whose|her|his|she|he)\s+[a-z]+',
    r'\d{2}(?:,|\s)\s*(?:a|the|an|is|was|works|lives|trains)',
    r'["\""][^"\"]{5,50}["\""]\s*(?:says|said|adds|explains)',
    r'\b(?:every|each)\s+(?:morning|Tuesday|week|Thursday|Sunday)',
]
PEOPLE_NEGATIVE = [
    r'^(?:Studies|Research|Data|According to studies)',
    r'\b(?:was found|has been shown|it is known|it has been)\',
    r'(?:\d+\.\s){3,}',
]

FITT_POSITIVE_PARA_MAX = 40   # words
FITT_POSITIVE_KICKER_MAX = 12  # words
FITT_STRONG_OPINION = [r'\b(?:best|worst|only|never|always|exactly|period|full stop|done)\b']
FITT_DECLARATIVE = r'^[A-Z][^,;]{0,30}(?:\.|:)\s'
FITT_DATA_LEAD = r'^\d'
FITT_NEGATIVE = [
    r'\b(?:might|could|perhaps|possibly|seems|appear|suggest|may)\b',
    r'^(?:Although|While|Despite|However|Nevertheless|Nonetheless)',
    r'\b(?:you should|your body|try this|you need)\b',
]

PASS_THRESHOLD = 65
CROSS_CONTAMINATION_THRESHOLD = 5
CROSS_CONTAMINATION_PENALTY = 10
