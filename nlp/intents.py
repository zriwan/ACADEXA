# nlp/intents.py
# Canonical, rule-based intent patterns for ACADEXA
import re
from typing import Dict, Any, Optional

# Precompiled regex patterns for speed and clarity
# NOTE: All matching is done on LOWERCASED, normalized text.
INTENT_PATTERNS = [
    {
        "name": "create_student",
        "regex": re.compile(
            r"^(?:add|create|register)\s+student\s+(?P<name>[a-z][a-z\s]+?)(?:\s+roll\s*(?P<roll>\d+))?$"
        ),
        "post": lambda m: {
            "name": m.group("name").strip(),
            "roll": int(m.group("roll")) if m.group("roll") else None,
        },
    },
    {
        "name": "delete_student",
        "regex": re.compile(
            r"^(?:delete|remove)\s+student\s*(?P<student_id>\d+)$"
        ),
        "post": lambda m: {"student_id": int(m.group("student_id"))},
    },
    {
        "name": "update_student_name",
        "regex": re.compile(
            r"^(?:update|edit)\s+student\s*(?P<student_id>\d+)\s+name\s+to\s+(?P<name>[a-z][a-z\s]+)$"
        ),
        "post": lambda m: {
            "student_id": int(m.group("student_id")),
            "name": m.group("name").strip(),
        },
    },
    {
        "name": "list_students",
        "regex": re.compile(
            r"^(?:list|show|display)\s+(?:all\s+)?students(?:\s+in\s+course\s+(?P<course>[a-z0-9\-]+))?$"
        ),
        "post": lambda m: {"course": m.group("course")},
    },
    {
        "name": "show_student_result",
        "regex": re.compile(
            r"^(?:show|get|display).*(?:result|marks).*(?:student|roll)\s*(?P<student_id>\d+)$"
        ),
        "post": lambda m: {"student_id": int(m.group("student_id"))},
    },
    {
        "name": "create_course",
        "regex": re.compile(
            r"^(?:add|create)\s+course\s+(?P<title>[a-z][a-z0-9\s\-]+)$"
        ),
        "post": lambda m: {"title": m.group("title").strip()},
    },
    {
        "name": "delete_course",
        "regex": re.compile(
            r"^(?:delete|remove)\s+course\s+(?P<course_code>[a-z0-9\-]+)$"
        ),
        "post": lambda m: {"course_code": m.group("course_code")},
    },
    {
        "name": "count_teachers",
        "regex": re.compile(
            r"^(?:how\s+many|count)\s+teachers$"
        ),
        "post": lambda m: {},
    },
    {
        "name": "assign_teacher_to_course",
        "regex": re.compile(
            r"^(?:assign|set)\s+teacher\s+(?P<teacher>[a-z][a-z\s]+)\s+to\s+course\s+(?P<course>[a-z0-9\-\s]+)$"
        ),
        "post": lambda m: {
            "teacher": m.group("teacher").strip(),
            "course": m.group("course").strip(),
        },
    },
]

def match_intent(text: str) -> Optional[Dict[str, Any]]:
    """Try each INTENT_PATTERNS entry and return the first match."""
    for spec in INTENT_PATTERNS:
        m = spec["regex"].match(text)
        if m:
            slots = spec["post"](m) if spec.get("post") else {}
            return {"intent": spec["name"], "slots": slots}
    return None
