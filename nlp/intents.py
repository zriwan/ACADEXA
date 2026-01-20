# nlp/intents.py
# Canonical, rule-based intent patterns for ACADEXA

import re
from typing import Dict, Any, Optional, List

# NOTE: All matching is done on LOWERCASED, normalized text
# via _normalize() in nlp_processor.

INTENT_PATTERNS: List[Dict[str, Any]] = [
    # ---------- Student CRUD & queries ----------

    # create_student: optional roll
    {
        "name": "create_student",
        "regex": re.compile(
            r"^(?:add|create|register)\s+student\s+"
            r"(?P<name>[a-z][a-z\s]+?)"
            r"(?:\s+roll\s*(?P<roll>\d+))?$"
        ),
        "post": lambda m: {
            "name": m.group("name").strip(),
            "roll": int(m.group("roll")) if m.group("roll") else None,
        },
    },

    # delete_student
    {
        "name": "delete_student",
        "regex": re.compile(r"^(?:delete|remove)\s+student\s+(?P<student_id>\d+)$"),
        "post": lambda m: {"student_id": int(m.group("student_id"))},
    },

    # update_student_name
    {
        "name": "update_student_name",
        "regex": re.compile(
            r"^update\s+student\s+(?P<student_id>\d+)\s+name\s+to\s+"
            r"(?P<name>[a-z][a-z\s]+)$"
        ),
        "post": lambda m: {
            "student_id": int(m.group("student_id")),
            "name": m.group("name").strip(),
        },
    },

    # list_students — with optional course
    {
        "name": "list_students",
        "regex": re.compile(
            r"^(?:list|show|display)\s+(?:all\s+)?students"
            r"(?:\s+in\s+course\s+(?P<course>[a-z0-9\-]+))?$"
        ),
        "post": lambda m: (
            {"course": m.group("course")} if m.groupdict().get("course") else {}
        ),
    },

    # ---------- Student results ----------

    # show_student_result
    {
        "name": "show_student_result",
        "regex": re.compile(
            r"^(?:show|get|display).*(?:result|marks).*(?:student|roll)\s*(?P<student_id>\d+)$"
        ),
        "post": lambda m: {"student_id": int(m.group("student_id"))},
    },

    # ---------- Course CRUD & queries ----------

    # create_course
    {
        "name": "create_course",
        "regex": re.compile(
            r"^(?:add|create)\s+course\s+(?P<title>[a-z][a-z0-9\s\-]+)$"
        ),
        "post": lambda m: {"title": m.group("title").strip()},
    },

    # delete_course
    {
        "name": "delete_course",
        "regex": re.compile(
            r"^(?:delete|remove)\s+course\s+(?P<course_code>[a-z0-9\-]+)$"
        ),
        "post": lambda m: {"course_code": m.group("course_code")},
    },

    # ---------- Teachers & assignments ----------

    # count_teachers
    {
        "name": "count_teachers",
        "regex": re.compile(r"^(?:how\s+many|count)\s+teachers$"),
        "post": lambda m: {},
    },

    # assign_teacher_to_course
    {
        "name": "assign_teacher_to_course",
        "regex": re.compile(
            r"^(?:assign|set)\s+teacher\s+(?P<teacher>[a-z][a-z\s]+)"
            r"\s+to\s+course\s+(?P<course>[a-z0-9\-\s]+)$"
        ),
        "post": lambda m: {
            "teacher": m.group("teacher").strip(),
            "course": m.group("course").strip(),
        },
    },

    # ---------- Day 6 — richer list intents ----------

    # Extra list_students variant
    {
        "name": "list_students",
        "regex": re.compile(r"^(?:list|show|get)\s+(?:all\s+)?students(?:\s+list)?$"),
        "post": lambda m: {},
    },

    # list_courses — basic
    {
        "name": "list_courses",
        "regex": re.compile(r"^(?:list|show|get)\s+(?:all\s+)?courses(?:\s+list)?$"),
        "post": lambda m: {},
    },

    # list_courses in department
    {
        "name": "list_courses",
        "regex": re.compile(
            r"^(?:list|show|get)\s+courses\s+in\s+"
            r"(?:department\s+)?(?P<department>[a-z0-9\-]+)$"
        ),
        "post": lambda m: {"department": m.group("department").upper()},
    },

    # list_courses for teacher
    {
        "name": "list_courses",
        "regex": re.compile(
            r"^(?:list|show|get)\s+courses\s+(?:for|by)\s+teacher\s+(?P<teacher_id>\d+)$"
        ),
        "post": lambda m: {"teacher_id": int(m.group("teacher_id"))},
    },

    # list_teachers
    {
        "name": "list_teachers",
        "regex": re.compile(r"^(?:list|show|get)\s+(?:all\s+)?teachers(?:\s+list)?$"),
        "post": lambda m: {},
    },

    # list_enrollments_for_student
    {
        "name": "list_enrollments_for_student",
        "regex": re.compile(
            r"^(?:list|show|get)\s+(?:enrol?lments?|courses)\s+"
            r"(?:for|of)\s+student\s+(?P<student_id>\d+)$"
        ),
        "post": lambda m: {"student_id": int(m.group("student_id"))},
    },

    # ✅ ---------- Day 3 — Voice USP Part-1 (CGPA) ----------
    {
        "name": "show_my_cgpa",
        "regex": re.compile(
            r"^(?:show|what\s+is|tell\s+me)\s+my\s+(?:cgpa|gpa)$|^my\s+(?:cgpa|gpa)$"
        ),
        "post": lambda m: {},
    },

    # ✅ ---------- Day 4 — Voice Part-2 (My Courses) ----------
    # examples:
    #   "show my courses"
    #   "my courses"
    #   "which courses am i enrolled in"
    {
        "name": "show_my_courses",
        "regex": re.compile(
            r"^(?:show|list|get)\s+my\s+courses$"
            r"|^my\s+courses$"
            r"|^(?:which|what)\s+courses\s+am\s+i\s+enrolled\s+in$"
        ),
        "post": lambda m: {},
    },

    # ✅ ---------- Day 4 — Voice Part-2 (My Result) ----------
    # examples:
    #   "show my result"
    #   "my results"
    #   "show my grades"
    #   "what is my result"
    {
        "name": "show_my_result",
        "regex": re.compile(
            r"^(?:show|get)\s+my\s+results?$"
            r"|^my\s+results?$"
            r"|^(?:show|get)\s+my\s+grades$"
            r"|^what\s+is\s+my\s+results?$"
        ),
        "post": lambda m: {},
    },
]


def match_intent(text: str) -> Optional[Dict[str, Any]]:
    """Try each INTENT_PATTERNS entry and return the first match."""
    for spec in INTENT_PATTERNS:
        m = spec["regex"].match(text)
        if m:
            slots = spec.get("post")(m) if spec.get("post") else {}
            return {"intent": spec["name"], "slots": slots}
    return None
