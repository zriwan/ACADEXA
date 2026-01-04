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

    Always returns at least:
      - raw_text: original text
      - parsed:   { intent, slots }

    For list-style intents, we also return:
      - info:         human-friendly message
      - results_type: one of "students" | "courses" | "teachers" | "enrollments"
      - results:      array of objects
    """
    parsed = parse_command(payload.text)

    base = {
        "raw_text": payload.text,
        "parsed": parsed.model_dump(),
    }

    intent = parsed.intent
    slots = parsed.slots or {}

    # -----------------------
    # 0) unknown intent
    # -----------------------
    if intent == "unknown":
        # Day 6 requirement: readable message for unknown commands
        return {
            **base,
            "info": (
                "I couldn't understand this command. "
                "Try commands like 'list students' or 'list courses'."
            ),
            "results_type": None,
            "results": [],
        }

    # -----------------------
    # 1) list_students
    # -----------------------
    if intent == "list_students":
        course_code = slots.get("course")

        query = db.query(Student)

        if course_code:
            # join with Enrollment + Course to filter students by course code
            query = (
                query.join(Enrollment, Enrollment.student_id == Student.id)
                .join(Course, Course.id == Enrollment.course_id)
                .filter(Course.code.ilike(course_code))
            )

        students = query.order_by(Student.id).all()

        if not students:
            if course_code:
                info = f"No students found in course {course_code}."
            else:
                info = "No students matched this query."
            return {
                **base,
                "info": info,
                "results_type": "students",
                "results": [],
            }

        results = [
            {
                "id": s.id,
                "name": s.name,
                "department": s.department,
                "gpa": float(s.gpa) if s.gpa is not None else None,
            }
            for s in students
        ]

        info = (
            f"Found {len(results)} student(s) in course {course_code}."
            if course_code
            else f"Found {len(results)} student(s)."
        )

        return {
            **base,
            "info": info,
            "results_type": "students",
            "results": results,
        }

    # -----------------------
    # 2) list_courses
    # -----------------------
    if intent == "list_courses":
        query = db.query(Course)

        department = slots.get("department")
        teacher_id = slots.get("teacher_id")

        if department:
            query = query.filter(Course.department.ilike(department))
        if teacher_id is not None:
            query = query.filter(Course.teacher_id == teacher_id)

        courses = query.order_by(Course.id).all()

        if not courses:
            if department:
                info = f"No courses found in department {department}."
            elif teacher_id is not None:
                info = f"No courses found for teacher {teacher_id}."
            else:
                info = "No courses found."
            return {
                **base,
                "info": info,
                "results_type": "courses",
                "results": [],
            }

        results = [
            {
                "id": c.id,
                "title": c.title,
                "code": c.code,
                "credit_hours": c.credit_hours,
                # extra fields for debugging if you want
                "department": getattr(c, "department", None),
                "teacher_id": getattr(c, "teacher_id", None),
            }
            for c in courses
        ]

        info = f"Found {len(results)} course(s)."

        # Old behavior: "Listed all courses"
        # Day 6: more informative count
        return {
            **base,
            "info": info,
            "results_type": "courses",
            "results": results,
        }

    # -----------------------
    # 3) list_teachers
    # -----------------------
    if intent == "list_teachers":
        teachers = db.query(Teacher).order_by(Teacher.id).all()

        if not teachers:
            return {
                **base,
                "info": "No teachers found.",
                "results_type": "teachers",
                "results": [],
            }

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

        info = f"Found {len(results)} teacher(s)."

        return {
            **base,
            "info": info,
            "results_type": "teachers",
            "results": results,
        }

    # -----------------------
    # 4) list_enrollments_for_student
    # -----------------------
    if intent == "list_enrollments_for_student":
        raw_sid = slots.get("student_id")

        try:
            student_id = int(raw_sid) if raw_sid is not None else None
        except (TypeError, ValueError):
            student_id = None

        if not student_id:
            # Day 6: clear message for bad / missing student id
            return {
                **base,
                "info": "Intent recognized but no valid student id found in command.",
                "results_type": "enrollments",
                "results": [],
            }

        q = (
            db.query(Enrollment, Student, Course)
            .join(Student, Student.id == Enrollment.student_id)
            .join(Course, Course.id == Enrollment.course_id)
            .filter(Enrollment.student_id == student_id)
            .order_by(Enrollment.id)
        )

        rows = q.all()

        if not rows:
            return {
                **base,
                "info": f"No enrollments found for student {student_id}.",
                "results_type": "enrollments",
                "results": [],
            }

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

        info = f"Found {len(results)} enrollment(s) for student {student_id}."

        return {
            **base,
            "info": info,
            "results_type": "enrollments",
            "results": results,
        }

    # ---- Fallback: known intent but not implemented above ----
    return {
        **base,
        "info": (
            "NLP parsed your command, but no concrete action is implemented "
            "for this intent yet."
        ),
        "results_type": None,
        "results": [],
    }
