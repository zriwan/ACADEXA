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
        "regex": re.compile(
            r"^(?:delete|remove)\s+student\s+(?P<student_id>\d+)$"
        ),
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

    # list_students — with optional course:
    #   "list all students"
    #   "show students in course cs101"
    #   "display students in course ai-101"
    {
        "name": "list_students",
        "regex": re.compile(
            r"^(?:list|show|display)\s+(?:all\s+)?students"
            r"(?:\s+in\s+course\s+(?P<course>[a-z0-9\-]+))?$"
        ),
        "post": lambda m: (
            {"course": m.group("course")}
            if m.groupdict().get("course")
            else {}
        ),
    },

    # ---------- Student results ----------

    # show_student_result:
    #   "Show result of student 125"
    #   "Get marks of roll 77"
    #   "display result student 9"
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
        "regex": re.compile(
            r"^(?:how\s+many|count)\s+teachers$"
        ),
        "post": lambda m: {},
    },

    # assign_teacher_to_course
    #   "assign teacher Ahmed Ali to course CS-101"
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

    # Extra list_students variant like:
    #   "list students"
    #   "get students list"
    {
        "name": "list_students",
        "regex": re.compile(
            r"^(?:list|show|get)\s+(?:all\s+)?students(?:\s+list)?$"
        ),
        "post": lambda m: {},
    },

    # list_courses — basic:
    #   "list courses"
    #   "show all courses"
    #   "get courses list"
    {
        "name": "list_courses",
        "regex": re.compile(
            r"^(?:list|show|get)\s+(?:all\s+)?courses(?:\s+list)?$"
        ),
        "post": lambda m: {},
    },

    # list_courses in department:
    #   "list courses in department CS"
    #   "show courses in cs"
    {
        "name": "list_courses",
        "regex": re.compile(
            r"^(?:list|show|get)\s+courses\s+in\s+"
            r"(?:department\s+)?(?P<department>[a-z0-9\-]+)$"
        ),
        # 🔹 normalize department to UPPER CASE for tests / backend
        "post": lambda m: {"department": m.group("department").upper()},
    },

    # list_courses for teacher:
    #   "list courses for teacher 2"
    #   "show courses by teacher 2"
    {
        "name": "list_courses",
        "regex": re.compile(
            r"^(?:list|show|get)\s+courses\s+(?:for|by)\s+teacher\s+(?P<teacher_id>\d+)$"
        ),
        "post": lambda m: {"teacher_id": int(m.group("teacher_id"))},
    },

    # list_teachers:
    #   "list teachers"
    #   "show all teachers"
    {
        "name": "list_teachers",
        "regex": re.compile(
            r"^(?:list|show|get)\s+(?:all\s+)?teachers(?:\s+list)?$"
        ),
        "post": lambda m: {},
    },

    # list_enrollments_for_student:
    #   "show enrollments for student 3"
    #   "list courses for student 3"
    {
        "name": "list_enrollments_for_student",
        "regex": re.compile(
            r"^(?:list|show|get)\s+(?:enrol?lments?|courses)\s+"
            r"(?:for|of)\s+student\s+(?P<student_id>\d+)$"
        ),
        "post": lambda m: {"student_id": int(m.group("student_id"))},
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
