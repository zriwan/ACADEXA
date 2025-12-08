# backend/routes/voice.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db_connection
from backend.security import get_current_user
from backend.models import Student, Course, Enrollment, Teacher
from nlp.nlp_processor import parse_command

router = APIRouter(prefix="/voice", tags=["Voice"])


class VoiceCommand(BaseModel):
    text: str


@router.post("/command")
def handle_command(
    payload: VoiceCommand,
    db: Session = Depends(get_db_connection),
    current_user=Depends(get_current_user),
):
    """
    Bridge: text -> NLP -> intent -> (optional) DB action.
    - Always returns: raw_text + parsed (intent, slots)
    - For some intents we also return 'results' + 'results_type'.
    """
    parsed = parse_command(payload.text)

    base = {
        "raw_text": payload.text,
        "parsed": parsed.model_dump(),
    }

    intent = parsed.intent
    slots = parsed.slots or {}

    # -----------------------
    # 1) list_students
    # -----------------------
    if intent == "list_students":
        course_code = slots.get("course")

        if course_code:
            q = (
                db.query(Student)
                .join(Enrollment, Enrollment.student_id == Student.id)
                .join(Course, Course.id == Enrollment.course_id)
                .filter(Course.code.ilike(str(course_code)))
            )
        else:
            q = db.query(Student)

        students = q.order_by(Student.id).all()

        results = [
            {
                "id": s.id,
                "name": s.name,
                "department": s.department,
                "gpa": float(s.gpa) if s.gpa is not None else None,
            }
            for s in students
        ]

        return {
            **base,
            "info": "Listed students"
            + (f" in course {course_code}" if course_code else ""),
            "results_type": "students",
            "results": results,
        }

    # -----------------------
    # 2) list_courses
    # -----------------------
    if intent == "list_courses":
        courses = db.query(Course).order_by(Course.id).all()
        results = [
            {
                "id": c.id,
                "title": c.title,
                "code": c.code,
                "credit_hours": c.credit_hours,
            }
            for c in courses
        ]
        return {
            **base,
            "info": "Listed all courses",
            "results_type": "courses",
            "results": results,
        }

    # -----------------------
    # 3) list_teachers
    # -----------------------
    if intent == "list_teachers":
        teachers = db.query(Teacher).order_by(Teacher.id).all()
        results = [
            {
                "id": t.id,
                "name": t.name,
                "department": t.department,
                "email": t.email,
                "expertise": t.expertise,
            }
            for t in teachers
        ]
        return {
            **base,
            "info": "Listed all teachers",
            "results_type": "teachers",
            "results": results,
        }

    # -----------------------
    # 4) list_enrollments_for_student
    # -----------------------
    # We support multiple possible intent names, depending on NLP rules
    if intent in ("list_enrollments_for_student", "list_enrollments_by_student"):
        # Try to get student id from slots
        raw_sid = (
            slots.get("student_id")
            or slots.get("student")
            or slots.get("id")
        )

        try:
            student_id = int(raw_sid) if raw_sid is not None else None
        except ValueError:
            student_id = None

        if not student_id:
            return {
                **base,
                "info": "Intent recognized but no student id found in command.",
            }

        q = (
            db.query(Enrollment, Student, Course)
            .join(Student, Student.id == Enrollment.student_id)
            .join(Course, Course.id == Enrollment.course_id)
            .filter(Enrollment.student_id == student_id)
            .order_by(Enrollment.id)
        )

        rows = q.all()
        results = []
        for en, stu, co in rows:
            results.append(
                {
                    "id": en.id,
                    "student_id": stu.id,
                    "student_name": stu.name,
                    "course_id": co.id,
                    "course_code": co.code,
                    "course_title": co.title,
                    "semester": en.semester,
                    "status": en.status,
                    "grade": float(en.grade) if en.grade is not None else None,
                }
            )

        return {
            **base,
            "info": f"Listed enrollments for student {student_id}",
            "results_type": "enrollments",
            "results": results,
        }

    # ---- Fallback: known intent but not implemented above ----
    return {
        **base,
        "info": "NLP parsed your command, but no concrete action is implemented for this intent yet.",
    }
