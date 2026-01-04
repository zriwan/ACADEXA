# nlp/nlp_processor.py
# Rule-based NLP Processor for ACADEXA

from typing import Dict, Any
import re

from pydantic import BaseModel

from .intents import match_intent


class ParseResult(BaseModel):
  intent: str
  slots: Dict[str, Any]

  # ✅ Allow dict-style access: parsed["intent"], parsed["slots"]
  def __getitem__(self, key: str) -> Any:
      return getattr(self, key)

  # Optional but handy if anything calls parsed.get("intent")
  def get(self, key: str, default=None) -> Any:
      return getattr(self, key, default)


def _normalize(text: str) -> str:
    """
    Simple, robust normalization for voice → text:
    - lowercase
    - strip outer spaces
    - remove punctuation (except hyphens)
    - collapse multiple spaces
    - keep hyphens and digits (for codes like CS-101, roll numbers, etc.)
    """
    # lowercase + basic strip
    text = text.lower().strip()

    # remove punctuation except hyphens (keep course codes like cs-101)
    # keep only lowercase letters, digits, whitespace and hyphen
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)

    # collapse runs of whitespace into a single space
    text = re.sub(r"\s+", " ", text)

    # final cleanup: remove leading/trailing spaces
    text = text.strip()

    return text


def parse_command(text: str) -> ParseResult:
    """
    Convert raw text into a canonical intent + slots dict.

    If no intent matches, returns:
        ParseResult(intent="unknown", slots={})
    """
    norm = _normalize(text)
    matched = match_intent(norm)
    if matched:
        return ParseResult(**matched)

    return ParseResult(intent="unknown", slots={})
