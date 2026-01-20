# backend/routes/voice.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db_connection
from backend.security import get_current_user
from backend.models import Student, Course, Enrollment, Teacher, User, UserRole

from nlp.nlp_processor import parse_command
from nlp.intents import match_intent  # ✅ already added

router = APIRouter(prefix="/voice", tags=["Voice"])


# -------------------------
# Helpers
# -------------------------
def _role_value(role):
    return role.value if hasattr(role, "value") else role


def _require_student(user: User) -> int:
    if _role_value(user.role) != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")
    if not user.student:
        raise HTTPException(status_code=404, detail="Student record not linked")
    return user.student.id


def _require_teacher(user: User) -> int:
    if _role_value(user.role) != UserRole.teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")
    if not user.teacher:
        raise HTTPException(status_code=404, detail="Teacher record not linked")
    return user.teacher.id


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


class VoiceCommand(BaseModel):
    text: str


@router.post("/command")
def handle_command(
    payload: VoiceCommand,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    """
    Bridge: text -> NLP -> intent -> (optional) DB action.

    Day-3:
      - student self intents (cgpa)

    Day-4:
      - student self intents (my courses, my result)

    Day-5 (already exists):
      - teacher self intents (my teaching courses, enrollments/students)

    Then fallback to existing NLP intents.
    """

    raw_text = payload.text
    text = _normalize(raw_text)

    matched = match_intent(text)

    # =====================================================
    # ✅ Day-3: show_my_cgpa (intent-based)
    # =====================================================
    if matched and matched.get("intent") == "show_my_cgpa":
        student_id = _require_student(current_user)

        gpa = current_user.student.gpa
        gpa_val = float(gpa) if gpa is not None else None

        if gpa_val is None:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "show_my_cgpa", "slots": {}},
                "intent": "show_my_cgpa",
                "cgpa": None,
                "info": "Your CGPA is not set yet.",
                "results_type": "gpa",
                "results": [{"student_id": student_id, "gpa": None}],
            }

        return {
            "raw_text": raw_text,
            "parsed": {"intent": "show_my_cgpa", "slots": {}},
            "intent": "show_my_cgpa",
            "cgpa": gpa_val,
            "info": f"Your CGPA is {gpa_val:.2f}.",
            "results_type": "gpa",
            "results": [{"student_id": student_id, "gpa": gpa_val}],
        }

    # =====================================================
    # ✅ Day-4 Step 4.2: show_my_courses (intent-based)
    # =====================================================
    if matched and matched.get("intent") == "show_my_courses":
        student_id = _require_student(current_user)

        enrollments = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == student_id)
            .all()
        )

        courses = []
        for e in enrollments:
            if e.course:
                c = e.course
                courses.append(
                    {
                        "id": c.id,
                        "title": c.title,
                        "code": c.code,
                        "credit_hours": c.credit_hours,
                    }
                )

        if not courses:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "show_my_courses", "slots": {}},
                "info": "You are not enrolled in any courses yet.",
                "results_type": "courses",
                "results": [],
            }

        pretty = ", ".join([f"{c['code']} ({c['title']})" for c in courses])
        return {
            "raw_text": raw_text,
            "parsed": {"intent": "show_my_courses", "slots": {}},
            "info": f"You are enrolled in: {pretty}.",
            "results_type": "courses",
            "results": courses,
        }

    # =====================================================
    # ✅ Day-4 Step 4.2: show_my_result (intent-based)
    # =====================================================
    if matched and matched.get("intent") == "show_my_result":
        student_id = _require_student(current_user)

        enrollments = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == student_id)
            .all()
        )

        if not enrollments:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "show_my_result", "slots": {}},
                "info": "You have no enrollments yet.",
                "results_type": "enrollments",
                "results": [],
            }

        results = []
        for e in enrollments:
            results.append(
                {
                    "id": e.id,
                    "student_id": e.student_id,
                    "course_id": e.course_id,
                    "course_code": e.course.code if e.course else None,
                    "course_title": e.course.title if e.course else None,
                    "semester": e.semester,
                    "status": e.status,
                    "grade": float(e.grade) if e.grade is not None else None,
                }
            )

        return {
            "raw_text": raw_text,
            "parsed": {"intent": "show_my_result", "slots": {}},
            "info": f"Found {len(results)} result record(s).",
            "results_type": "enrollments",
            "results": results,
        }

    # -----------------------------
    # Student self intents (fallback keyword rules)
    # -----------------------------
    # GPA / CGPA (fallback)
    if ("gpa" in text) or ("cgpa" in text):
        student_id = _require_student(current_user)
        gpa = current_user.student.gpa
        gpa_val = float(gpa) if gpa is not None else None

        if gpa_val is None:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "show_my_cgpa", "slots": {}},
                "intent": "show_my_cgpa",
                "cgpa": None,
                "info": "Your CGPA is not set yet.",
                "results_type": "gpa",
                "results": [{"student_id": student_id, "gpa": None}],
            }

        return {
            "raw_text": raw_text,
            "parsed": {"intent": "show_my_cgpa", "slots": {}},
            "intent": "show_my_cgpa",
            "cgpa": gpa_val,
            "info": f"Your CGPA is {gpa_val:.2f}.",
            "results_type": "gpa",
            "results": [{"student_id": student_id, "gpa": gpa_val}],
        }

    # My Courses (fallback)
    if (
        ("my courses" in text)
        or ("enrolled" in text and "course" in text)
        or ("courses" in text and "enrolled" in text)
        or ("subjects" in text)
        or ("course" in text and "my" in text)
    ):
        student_id = _require_student(current_user)

        enrollments = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == student_id)
            .all()
        )

        courses = []
        for e in enrollments:
            if e.course:
                c = e.course
                courses.append(
                    {
                        "id": c.id,
                        "title": c.title,
                        "code": c.code,
                        "credit_hours": c.credit_hours,
                    }
                )

        if not courses:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "student_courses", "slots": {}},
                "info": "You are not enrolled in any courses yet.",
                "results_type": "courses",
                "results": [],
            }

        pretty = ", ".join([f"{c['code']} ({c['title']})" for c in courses])
        return {
            "raw_text": raw_text,
            "parsed": {"intent": "student_courses", "slots": {}},
            "info": f"You are enrolled in: {pretty}.",
            "results_type": "courses",
            "results": courses,
        }

    # My Enrollments (fallback)
    if (
        ("my enrollments" in text)
        or ("my enrollment" in text)
        or ("enrollments" in text and "my" in text)
        or ("enrolled" in text and "in" in text)
    ):
        student_id = _require_student(current_user)

        enrollments = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == student_id)
            .all()
        )

        if not enrollments:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "student_enrollments", "slots": {}},
                "info": "You have no enrollments yet.",
                "results_type": "enrollments",
                "results": [],
            }

        results = []
        for e in enrollments:
            results.append(
                {
                    "id": e.id,
                    "student_id": e.student_id,
                    "course_id": e.course_id,
                    "semester": e.semester,
                    "status": e.status,
                    "grade": float(e.grade) if e.grade is not None else None,
                }
            )

        return {
            "raw_text": raw_text,
            "parsed": {"intent": "student_enrollments", "slots": {}},
            "info": f"You have {len(results)} enrollment(s).",
            "results_type": "enrollments",
            "results": results,
        }

    # -----------------------------
    # Teacher self intents (Day-5)
    # -----------------------------
    if (
        ("courses am i teaching" in text)
        or ("which courses am i teaching" in text)
        or ("my teaching courses" in text)
        or ("courses i teach" in text)
        or ("teaching" in text and "course" in text)
        or ("my courses" in text and "teacher" in text)
    ):
        teacher_id = _require_teacher(current_user)

        courses = (
            db.query(Course)
            .filter(Course.teacher_id == teacher_id)
            .order_by(Course.id)
            .all()
        )

        if not courses:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "teacher_courses", "slots": {}},
                "info": "You are not assigned to any courses yet.",
                "results_type": "courses",
                "results": [],
            }

        results = [
            {"id": c.id, "title": c.title, "code": c.code, "credit_hours": c.credit_hours}
            for c in courses
        ]

        pretty = ", ".join([f"{c['code']} ({c['title']})" for c in results])
        return {
            "raw_text": raw_text,
            "parsed": {"intent": "teacher_courses", "slots": {}},
            "info": f"You are teaching: {pretty}.",
            "results_type": "courses",
            "results": results,
        }

    if (
        ("show my enrollments" in text)
        or ("my enrollments" in text and "teacher" in text)
        or ("students in my courses" in text)
        or ("list students" in text and "my course" in text)
        or ("students" in text and "my" in text)
        or ("enrollments" in text and "my" in text)
    ):
        teacher_id = _require_teacher(current_user)

        rows = (
            db.query(Enrollment, Course, Student)
            .join(Course, Course.id == Enrollment.course_id)
            .join(Student, Student.id == Enrollment.student_id)
            .filter(Course.teacher_id == teacher_id)
            .order_by(Enrollment.id)
            .all()
        )

        if not rows:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "teacher_enrollments", "slots": {}},
                "info": "No enrollments found for your courses yet.",
                "results_type": "enrollments",
                "results": [],
            }

        results = []
        for en, co, st in rows:
            results.append(
                {
                    "enrollment_id": en.id,
                    "course_id": co.id,
                    "course_code": co.code,
                    "course_title": co.title,
                    "student_id": st.id,
                    "student_name": st.name,
                    "semester": en.semester,
                    "status": en.status,
                    "grade": float(en.grade) if en.grade is not None else None,
                }
            )

        return {
            "raw_text": raw_text,
            "parsed": {"intent": "teacher_enrollments", "slots": {}},
            "info": f"Found {len(results)} enrollment(s) in your courses.",
            "results_type": "enrollments",
            "results": results,
        }

    # -----------------------------
    # Existing NLP flow
    # -----------------------------
    parsed = parse_command(raw_text)

    base = {
        "raw_text": raw_text,
        "parsed": parsed.model_dump(),
    }

    intent = parsed.intent
    slots = parsed.slots or {}

    if intent == "unknown":
        return {
            **base,
            "info": (
                "I couldn't understand this command. "
                "Try commands like 'list students' or 'list courses'."
            ),
            "results_type": None,
            "results": [],
        }

    # fallback (keep your real handlers below in your full file)
    return {
        **base,
        "info": (
            "NLP parsed your command, but no concrete action is implemented "
            "for this intent yet."
        ),
        "results_type": None,
        "results": [],
    }
