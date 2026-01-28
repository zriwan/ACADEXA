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

    # list_students — by department
    {
        "name": "list_students",
        "regex": re.compile(
            r"^(?:list|show|get)\s+students\s+in\s+"
            r"(?:department\s+)?(?P<department>[a-z0-9\-]+)$"
        ),
        "post": lambda m: {"department": m.group("department").upper()},
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

    {
        "name": "list_students",
        "regex": re.compile(r"^(?:list|show|get)\s+(?:all\s+)?students(?:\s+list)?$"),
        "post": lambda m: {},
    },

    {
        "name": "list_courses",
        "regex": re.compile(r"^(?:list|show|get)\s+(?:all\s+)?courses(?:\s+list)?$"),
        "post": lambda m: {},
    },

    {
        "name": "list_courses",
        "regex": re.compile(
            r"^(?:list|show|get)\s+courses\s+in\s+"
            r"(?:department\s+)?(?P<department>[a-z0-9\-]+)$"
        ),
        "post": lambda m: {"department": m.group("department").upper()},
    },

    {
        "name": "list_courses",
        "regex": re.compile(
            r"^(?:list|show|get)\s+courses\s+(?:for|by)\s+teacher\s+(?P<teacher_id>\d+)$"
        ),
        "post": lambda m: {"teacher_id": int(m.group("teacher_id"))},
    },

    {
        "name": "list_teachers",
        "regex": re.compile(r"^(?:list|show|get)\s+(?:all\s+)?teachers(?:\s+list)?$"),
        "post": lambda m: {},
    },

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

    # ✅ ---------- Attendance (My Attendance Summary) ----------
    # Supports BOTH spellings: attendance / attendence
    {
        "name": "show_my_attendance",
        "regex": re.compile(
            r"^(?:show|get|display)\s+my\s+attend(?:ance|ence)$"
            r"|^my\s+attend(?:ance|ence)$"
            r"|^attend(?:ance|ence)\s+summary$"
        ),
        "post": lambda m: {},
    },

    # ✅ ---------- Attendance (My Attendance for a Course) ----------
    # Supports "cs-101" AND "cs 101" (converts spaces -> hyphen)
    {
        "name": "show_my_attendance_course",
        "regex": re.compile(
            r"^(?:show|get|display)\s+my\s+attend(?:ance|ence)\s+(?:in|for)\s+(?P<course_code>[a-z0-9\- ]+)$"
            r"|^attend(?:ance|ence)\s+(?P<course_code2>[a-z0-9\- ]+)$"
        ),
        "post": lambda m: {
            "course_code": re.sub(
                r"\s+",
                "-",
                (m.group("course_code") or m.group("course_code2") or "").strip(),
            ).upper()
        },
    },

    # ---------- CREATE Operations ----------

    {
        "name": "create_student",
        "regex": re.compile(
            r"^(?:add|create|register)\s+student\s+"
            r"(?P<name>[a-z][a-z\s]+?)"
            r"(?:\s+in\s+department\s+(?P<department>[a-z0-9\s]+))?"
            r"(?:\s+with\s+gpa\s+(?P<gpa>\d+\.?\d*))?"
            r"(?:\s+email\s+(?P<email>[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}))?"
            r"(?:\s+password\s+(?P<password>[a-z0-9]+))?$"
        ),
        "post": lambda m: {
            "name": m.group("name").strip(),
            "department": m.group("department").strip() if m.group("department") else None,
            "gpa": float(m.group("gpa")) if m.group("gpa") else None,
            "email": m.group("email") if m.group("email") else None,
            "password": m.group("password") if m.group("password") else None,
        },
    },

    {
        "name": "create_teacher",
        "regex": re.compile(
            r"^(?:add|create|register)\s+teacher\s+"
            r"(?P<name>[a-z][a-z\s]+?)"
            r"(?:\s+in\s+department\s+(?P<department>[a-z0-9\s]+))?"
            r"(?:\s+email\s+(?P<email>[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}))?"
            r"(?:\s+expertise\s+(?P<expertise>[a-z0-9\s]+))?"
            r"(?:\s+password\s+(?P<password>[a-z0-9]+))?$"
        ),
        "post": lambda m: {
            "name": m.group("name").strip(),
            "department": m.group("department").strip() if m.group("department") else None,
            "email": m.group("email") if m.group("email") else None,
            "expertise": m.group("expertise").strip() if m.group("expertise") else None,
            "password": m.group("password") if m.group("password") else None,
        },
    },

    {
        "name": "create_course",
        "regex": re.compile(
            r"^(?:add|create)\s+course\s+"
            r"(?P<title>[a-z][a-z0-9\s\-]+?)"
            r"(?:\s+code\s+(?P<code>[a-z0-9\-]+))?"
            r"(?:\s+credit\s+hours?\s+(?P<credit_hours>\d+))?"
            r"(?:\s+teacher\s+(?P<teacher_id>\d+))?$"
        ),
        "post": lambda m: {
            "title": m.group("title").strip(),
            "code": m.group("code") if m.group("code") else None,
            "credit_hours": int(m.group("credit_hours")) if m.group("credit_hours") else None,
            "teacher_id": int(m.group("teacher_id")) if m.group("teacher_id") else None,
        },
    },

    {
        "name": "create_enrollment",
        "regex": re.compile(
            r"^(?:enroll|add|register)\s+student\s+(?P<student_id>\d+)"
            r"\s+in\s+course\s+(?P<course_id>\d+)"
            r"(?:\s+semester\s+(?P<semester>[a-z0-9\s]+))?"
            r"(?:\s+status\s+(?P<status>[a-z]+))?$"
        ),
        "post": lambda m: {
            "student_id": int(m.group("student_id")),
            "course_id": int(m.group("course_id")),
            "semester": m.group("semester").strip() if m.group("semester") else None,
            "status": m.group("status") if m.group("status") else None,
        },
    },

    # ---------- UPDATE Operations ----------
    {
        "name": "update_student",
        "regex": re.compile(
            r"^update\s+student\s+(?P<student_id>\d+)"
            r"(?:\s+name\s+to\s+(?P<name>[a-z][a-z\s]+))?"
            r"(?:\s+department\s+to\s+(?P<department>[a-z0-9\s]+))?"
            r"(?:\s+gpa\s+to\s+(?P<gpa>\d+\.?\d*))?$"
        ),
        "post": lambda m: {
            "student_id": int(m.group("student_id")),
            "name": m.group("name").strip() if m.group("name") else None,
            "department": m.group("department").strip() if m.group("department") else None,
            "gpa": float(m.group("gpa")) if m.group("gpa") else None,
        },
    },

    {
        "name": "update_teacher",
        "regex": re.compile(
            r"^update\s+teacher\s+(?P<teacher_id>\d+)"
            r"(?:\s+name\s+to\s+(?P<name>[a-z][a-z\s]+))?"
            r"(?:\s+department\s+to\s+(?P<department>[a-z0-9\s]+))?"
            r"(?:\s+expertise\s+to\s+(?P<expertise>[a-z0-9\s]+))?$"
        ),
        "post": lambda m: {
            "teacher_id": int(m.group("teacher_id")),
            "name": m.group("name").strip() if m.group("name") else None,
            "department": m.group("department").strip() if m.group("department") else None,
            "expertise": m.group("expertise").strip() if m.group("expertise") else None,
        },
    },

    {
        "name": "update_course",
        "regex": re.compile(
            r"^update\s+course\s+(?P<course_id>\d+)"
            r"(?:\s+title\s+to\s+(?P<title>[a-z][a-z0-9\s\-]+))?"
            r"(?:\s+code\s+to\s+(?P<code>[a-z0-9\-]+))?"
            r"(?:\s+credit\s+hours?\s+to\s+(?P<credit_hours>\d+))?"
            r"(?:\s+teacher\s+to\s+(?P<teacher_id>\d+))?$"
        ),
        "post": lambda m: {
            "course_id": int(m.group("course_id")),
            "title": m.group("title").strip() if m.group("title") else None,
            "code": m.group("code") if m.group("code") else None,
            "credit_hours": int(m.group("credit_hours")) if m.group("credit_hours") else None,
            "teacher_id": int(m.group("teacher_id")) if m.group("teacher_id") else None,
        },
    },

    {
        "name": "update_enrollment",
        "regex": re.compile(
            r"^update\s+enrollment\s+(?P<enrollment_id>\d+)"
            r"(?:\s+grade\s+to\s+(?P<grade>\d+\.?\d*))?"
            r"(?:\s+status\s+to\s+(?P<status>[a-z]+))?"
            r"(?:\s+semester\s+to\s+(?P<semester>[a-z0-9\s]+))?$"
        ),
        "post": lambda m: {
            "enrollment_id": int(m.group("enrollment_id")),
            "grade": float(m.group("grade")) if m.group("grade") else None,
            "status": m.group("status") if m.group("status") else None,
            "semester": m.group("semester").strip() if m.group("semester") else None,
        },
    },

    # ---------- DELETE Operations ----------
    {
        "name": "delete_student",
        "regex": re.compile(r"^(?:delete|remove)\s+student\s+(?P<student_id>\d+)$"),
        "post": lambda m: {"student_id": int(m.group("student_id"))},
    },

    {
        "name": "delete_teacher",
        "regex": re.compile(r"^(?:delete|remove)\s+teacher\s+(?P<teacher_id>\d+)$"),
        "post": lambda m: {"teacher_id": int(m.group("teacher_id"))},
    },

    {
        "name": "delete_course",
        "regex": re.compile(
            r"^(?:delete|remove)\s+course\s+(?P<course_id>\d+)$"
            r"|^(?:delete|remove)\s+course\s+code\s+(?P<course_code>[a-z0-9\-]+)$"
        ),
        "post": lambda m: {
            "course_id": int(m.group("course_id")) if m.group("course_id") else None,
            "course_code": m.group("course_code") if m.group("course_code") else None,
        },
    },

    {
        "name": "delete_enrollment",
        "regex": re.compile(
            r"^(?:delete|remove|drop)\s+enrollment\s+(?P<enrollment_id>\d+)$"
            r"|^(?:drop|unenroll)\s+student\s+(?P<student_id>\d+)\s+from\s+course\s+(?P<course_id>\d+)$"
        ),
        "post": lambda m: {
            "enrollment_id": int(m.group("enrollment_id")) if m.group("enrollment_id") else None,
            "student_id": int(m.group("student_id")) if m.group("student_id") else None,
            "course_id": int(m.group("course_id")) if m.group("course_id") else None,
        },
    },

    # ---------- GET Operations (single item) ----------
    {
        "name": "get_student",
        "regex": re.compile(r"^(?:show|get|display)\s+student\s+(?P<student_id>\d+)$"),
        "post": lambda m: {"student_id": int(m.group("student_id"))},
    },

    {
        "name": "get_teacher",
        "regex": re.compile(r"^(?:show|get|display)\s+teacher\s+(?P<teacher_id>\d+)$"),
        "post": lambda m: {"teacher_id": int(m.group("teacher_id"))},
    },

    {
        "name": "get_course",
        "regex": re.compile(
            r"^(?:show|get|display)\s+course\s+(?P<course_id>\d+)$"
            r"|^(?:show|get|display)\s+course\s+code\s+(?P<course_code>[a-z0-9\-]+)$"
        ),
        "post": lambda m: {
            "course_id": int(m.group("course_id")) if m.group("course_id") else None,
            "course_code": m.group("course_code") if m.group("course_code") else None,
        },
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
