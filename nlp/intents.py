import re
from typing import Tuple, Dict, Any

INTENT_PATTERNS = {
    "get_results": re.compile(r"results?.*roll\s*no\.?\s*(\d+)", re.I),
    "add_student": re.compile(r"add student\s+([A-Za-z ]+).*roll\s*no\.?\s*(\d+).*in\s+([A-Za-z0-9]+)", re.I),
    "assign_course": re.compile(r"assign course\s+([A-Za-z0-9]+).*roll\s*no\.?\s*(\d+)", re.I),
}

def parse_intent(text: str) -> Tuple[str, Dict[str, Any]]:
    text = text.strip()
    for intent, pat in INTENT_PATTERNS.items():
        m = pat.search(text)
        if m:
            return intent, {"groups": m.groups()}
    return "unknown", {}
