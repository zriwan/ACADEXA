# nlp/nlp_processor.py
# Day 12: Rule-based NLP Processor for ACADEXA
from typing import Dict, Any
import re

from pydantic import BaseModel
from .intents import match_intent

class ParseResult(BaseModel):
    intent: str
    slots: Dict[str, Any]

def _normalize(text: str) -> str:
    """
    Simple, robust normalization for voice → text:
    - lowercase
    - strip outer spaces
    - collapse multiple spaces
    - keep hyphens and digits (for codes like CS-101, roll numbers, etc.)
    """
    text = text.lower().strip()
    # remove punctuation except hyphens (keep course codes like cs-101)
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text

def parse_command(text: str) -> ParseResult:
    """
    Convert raw text into a canonical intent + slots dict.
    If no intent matches, returns intent='unknown' with empty slots.
    """
    norm = _normalize(text)
    matched = match_intent(norm)
    if matched:
        return ParseResult(**matched)
    return ParseResult(intent="unknown", slots={})

# Optional: tiny demo
if __name__ == "__main__":
    samples = [
        "Add student Ali roll 125",
        "Show result of student 125",
        "Delete student 7",
        "List all students in course cs101",
        "Assign teacher Ahmed to course AI-101",
        "How many teachers",
        "Update student 33 name to Hamza Khan",
        "Create course Data Mining",
        "Remove course CS-999",
        "what is this command",  # unknown
    ]
    for s in samples:
        print(s, "->", parse_command(s).model_dump())
