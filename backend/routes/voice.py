# backend/routes/voice.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db_connection
from backend.security import get_current_user
from backend.models import Student, Course, Enrollment, Teacher, User, UserRole
from nlp.nlp_processor import parse_command

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
      - student self intents (gpa, my courses, my enrollments)

    Day-5 (added here):
      - teacher self intents (my teaching courses, my course enrollments/students)

    Then fallback to existing NLP intents.
    """

    raw_text = payload.text
    text = _normalize(raw_text)

    # -----------------------------
    # Student self intents (no IDs needed)
    # -----------------------------
    # 1) GPA / CGPA
    if ("gpa" in text) or ("cgpa" in text):
        student_id = _require_student(current_user)
        gpa = current_user.student.gpa
        gpa_val = float(gpa) if gpa is not None else None

        if gpa_val is None:
            return {
                "raw_text": raw_text,
                "parsed": {"intent": "student_gpa", "slots": {}},
                "info": "Your GPA is not set yet.",
                "results_type": "gpa",
                "results": [{"student_id": student_id, "gpa": None}],
            }

        return {
            "raw_text": raw_text,
            "parsed": {"intent": "student_gpa", "slots": {}},
            "info": f"Your GPA is {gpa_val:.2f}.",
            "results_type": "gpa",
            "results": [{"student_id": student_id, "gpa": gpa_val}],
        }

    # 2) My Courses (student)
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

    # 3) My Enrollments (student)
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
    # Teacher: My Courses (teaching courses)
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

    # Teacher: Students / Enrollments in my courses
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
    # Existing NLP flow (your current behavior)
    # -----------------------------
    parsed = parse_command(raw_text)

    base = {
        "raw_text": raw_text,
        "parsed": parsed.model_dump(),
    }

    intent = parsed.intent
    slots = parsed.slots or {}

    # 0) unknown intent
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

    # 1) list_students
    if intent == "list_students":
        course_code = slots.get("course")

        query = db.query(Student)

        if course_code:
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

    # 2) list_courses
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
                "department": getattr(c, "department", None),
                "teacher_id": getattr(c, "teacher_id", None),
            }
            for c in courses
        ]

        info = f"Found {len(results)} course(s)."

        return {
            **base,
            "info": info,
            "results_type": "courses",
            "results": results,
        }

    # 3) list_teachers
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

    # 4) list_enrollments_for_student
    if intent == "list_enrollments_for_student":
        raw_sid = slots.get("student_id")

        try:
            student_id = int(raw_sid) if raw_sid is not None else None
        except (TypeError, ValueError):
            student_id = None

        if not student_id:
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

    # fallback
    return {
        **base,
        "info": (
            "NLP parsed your command, but no concrete action is implemented "
            "for this intent yet."
        ),
        "results_type": None,
        "results": [],
    }
