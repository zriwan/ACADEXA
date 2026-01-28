# backend/routes/voice.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db_connection
from backend.security import get_current_user, hash_password
from backend.models import (
    Student,
    Course,
    Enrollment,
    Teacher,
    User,
    UserRole,
    AttendanceSession,
    AttendanceRecord,
)

from nlp.nlp_processor import parse_command
from nlp.intents import match_intent  # (not used directly, but ok to keep)

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


def _require_admin_or_hod(user: User) -> None:
    role = _role_value(user.role)
    if role not in (UserRole.admin, UserRole.hod):
        raise HTTPException(status_code=403, detail="Admin/HOD access required")


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

    Already present:
      - student self intents (cgpa, my courses, my result)
      - teacher self intents (my teaching courses, enrollments)
    Now added:
      - Admin/HOD + role-based list_* intents
      - ✅ Attendance intents
    """

    raw_text = payload.text
    text = _normalize(raw_text)  # ✅ FIX: used by your keyword fallback section

    parsed = parse_command(raw_text)  # strong normalize inside
    matched = {"intent": parsed.intent, "slots": parsed.slots} if parsed.intent != "unknown" else None

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
    # ✅ Day-4: show_my_courses (intent-based)
    # =====================================================
    if matched and matched.get("intent") == "show_my_courses":
        student_id = _require_student(current_user)

        enrollments = db.query(Enrollment).filter(Enrollment.student_id == student_id).all()

        courses = []
        for e in enrollments:
            if e.course:
                c = e.course
                courses.append(
                    {"id": c.id, "title": c.title, "code": c.code, "credit_hours": c.credit_hours}
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
    # ✅ Day-4: show_my_result (intent-based)
    # =====================================================
    if matched and matched.get("intent") == "show_my_result":
        student_id = _require_student(current_user)

        enrollments = db.query(Enrollment).filter(Enrollment.student_id == student_id).all()

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
    # Existing keyword fallbacks (keep)
    # -----------------------------
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

    # -----------------------------
    # Teacher self intents (existing)
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
    # ✅ NLP flow (ADD REAL HANDLERS HERE)
    # -----------------------------
    base = {"raw_text": raw_text, "parsed": parsed.model_dump()}
    intent = parsed.intent
    slots = parsed.slots or {}

    # Global safety: Voice Console is read-only.
    # Block any create/update/delete intents at the API level.
    if intent.startswith("create_") or intent.startswith("update_") or intent.startswith("delete_"):
        return {
            **base,
            "info": "Voice console is read-only; please use the web forms for any create, update, or delete operations.",
            "results_type": None,
            "results": [],
        }

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

    # -----------------------------
    # ✅ Attendance (Student)
    # -----------------------------
    if intent == "show_my_attendance":
        student_id = _require_student(current_user)

        enrolls = (
            db.query(Enrollment, Course)
            .join(Course, Course.id == Enrollment.course_id)
            .filter(Enrollment.student_id == student_id)
            .order_by(Course.id)
            .all()
        )

        results = []

        def _sv(x):
            return x.value if hasattr(x, "value") else str(x)

        for en, co in enrolls:
            total_sessions = (
                db.query(AttendanceSession)
                .filter(AttendanceSession.course_id == co.id)
                .count()
            )

            recs = (
                db.query(AttendanceRecord)
                .join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)
                .filter(
                    AttendanceRecord.enrollment_id == en.id,
                    AttendanceSession.course_id == co.id,
                )
                .all()
            )

            present = sum(1 for r in recs if _sv(r.status) == "present")
            absent = sum(1 for r in recs if _sv(r.status) == "absent")
            late = sum(1 for r in recs if _sv(r.status) == "late")

            # If session exists but record missing => treat as absent
            missing = max(total_sessions - len(recs), 0)
            absent_total = absent + missing

            percent = (present / total_sessions) * 100 if total_sessions > 0 else 0.0

            results.append(
                {
                    "course_id": co.id,
                    "course_code": co.code,
                    "course_title": co.title,
                    "total_sessions": total_sessions,
                    "present": present,
                    "absent": absent_total,
                    "late": late,
                    "percent_present": round(percent, 2),
                }
            )

        if not results:
            return {
                **base,
                "info": "No attendance data found yet.",
                "results_type": "attendance_summary",
                "results": [],
            }

        return {
            **base,
            "info": f"Attendance summary loaded for {len(results)} course(s).",
            "results_type": "attendance_summary",
            "results": results,
        }

    if intent == "show_my_attendance_course":
        student_id = _require_student(current_user)
        course_code = (slots.get("course_code") or slots.get("course") or "").strip()

        if not course_code:
            return {
                **base,
                "info": "Please specify course code, e.g. 'show my attendance for CS-101'.",
                "results_type": "attendance_course_detail",
                "results": [],
            }

        co = db.query(Course).filter(Course.code.ilike(course_code)).first()
        if not co:
            return {
                **base,
                "info": f"No course found with code '{course_code}'.",
                "results_type": "attendance_course_detail",
                "results": [],
            }

        en = (
            db.query(Enrollment)
            .filter(Enrollment.student_id == student_id, Enrollment.course_id == co.id)
            .first()
        )
        if not en:
            return {
                **base,
                "info": "You are not enrolled in this course.",
                "results_type": "attendance_course_detail",
                "results": [],
            }

        sessions = (
            db.query(AttendanceSession)
            .filter(AttendanceSession.course_id == co.id)
            .order_by(AttendanceSession.lecture_date.desc(), AttendanceSession.id.desc())
            .all()
        )

        recs = db.query(AttendanceRecord).filter(AttendanceRecord.enrollment_id == en.id).all()
        status_map = {
            r.session_id: (r.status.value if hasattr(r.status, "value") else str(r.status))
            for r in recs
        }

        rows = []
        for s in sessions:
            rows.append(
                {
                    "session_id": s.id,
                    "lecture_date": str(s.lecture_date),
                    "start_time": getattr(s, "start_time", None),
                    "end_time": getattr(s, "end_time", None),
                    "status": status_map.get(s.id, "absent"),
                }
            )

        return {
            **base,
            "info": f"Attendance detail loaded for {co.code}.",
            "results_type": "attendance_course_detail",
            "results": {
                "student_id": student_id,
                "course_id": co.id,
                "course_code": co.code,
                "course_title": co.title,
                "rows": rows,
            },
        }

    # -----------------------------
    # ✅ NEW: role-based list_* intents
    # -----------------------------
    role = _role_value(current_user.role)

    # helper slot getters
    course_code = (slots.get("course") or slots.get("course_code") or "").strip()
    raw_sid = slots.get("student_id") or slots.get("student") or None

    # 1) list_teachers (Admin/HOD only)
    if intent == "list_teachers":
        _require_admin_or_hod(current_user)

        teachers = db.query(Teacher).order_by(Teacher.id).all()
        results = [
            {
                "id": t.id,
                "name": getattr(t, "name", None),
                "department": getattr(t, "department", None),
                "email": getattr(t, "email", None),
                "expertise": getattr(t, "expertise", None),
            }
            for t in teachers
        ]
        return {**base, "info": f"Found {len(results)} teacher(s).", "results_type": "teachers", "results": results}

    # 2) list_courses
    if intent == "list_courses":
        # Admin/HOD: all courses
        if role in (UserRole.admin, UserRole.hod):
            q = db.query(Course)

            if course_code:
                q = q.filter(Course.code.ilike(course_code))

            courses = q.order_by(Course.id).all()
            results = [
                {
                    "id": c.id,
                    "title": c.title,
                    "code": c.code,
                    "credit_hours": c.credit_hours,
                    "teacher_id": c.teacher_id,
                }
                for c in courses
            ]
            return {**base, "info": f"Found {len(results)} course(s).", "results_type": "courses", "results": results}

        # Teacher: only courses they teach
        if role == UserRole.teacher:
            teacher_id = _require_teacher(current_user)
            q = db.query(Course).filter(Course.teacher_id == teacher_id)
            if course_code:
                q = q.filter(Course.code.ilike(course_code))
            courses = q.order_by(Course.id).all()
            results = [
                {"id": c.id, "title": c.title, "code": c.code, "credit_hours": c.credit_hours}
                for c in courses
            ]
            return {**base, "info": f"Found {len(results)} course(s) you teach.", "results_type": "courses", "results": results}

        # Student: only courses they are enrolled in
        if role == UserRole.student:
            student_id = _require_student(current_user)

            q = (
                db.query(Course)
                .join(Enrollment, Enrollment.course_id == Course.id)
                .filter(Enrollment.student_id == student_id)
            )
            if course_code:
                q = q.filter(Course.code.ilike(course_code))

            courses = q.order_by(Course.id).all()
            results = [
                {"id": c.id, "title": c.title, "code": c.code, "credit_hours": c.credit_hours}
                for c in courses
            ]
            return {**base, "info": f"Found {len(results)} enrolled course(s).", "results_type": "courses", "results": results}

    # 3) list_students
    if intent == "list_students":
        # Admin/HOD: all students OR filter by course
        if role in (UserRole.admin, UserRole.hod):
            q = db.query(Student)

            # Optional: filter by course code
            if course_code:
                course = db.query(Course).filter(Course.code.ilike(course_code)).first()
                if not course:
                    return {
                        **base,
                        "info": f"No course found with code '{course_code}'.",
                        "results_type": "students",
                        "results": [],
                    }

                q = (
                    db.query(Student)
                    .join(Enrollment, Enrollment.student_id == Student.id)
                    .filter(Enrollment.course_id == course.id)
                )

            # Optional: filter by department (from NLP slot)
            dept = (slots.get("department") or "").strip()
            if dept:
                q = q.filter(Student.department.ilike(dept))

            students = q.order_by(Student.id).all()
            results = [
                {
                    "id": s.id,
                    "name": getattr(s, "name", None),
                    "department": getattr(s, "department", None),
                    "gpa": float(s.gpa) if getattr(s, "gpa", None) is not None else None,
                }
                for s in students
            ]
            return {**base, "info": f"Found {len(results)} student(s).", "results_type": "students", "results": results}

        # Teacher: only students in teacher courses (optional filter by course/department)
        if role == UserRole.teacher:
            teacher_id = _require_teacher(current_user)

            q = (
                db.query(Student, Course, Enrollment)
                .join(Enrollment, Enrollment.student_id == Student.id)
                .join(Course, Course.id == Enrollment.course_id)
                .filter(Course.teacher_id == teacher_id)
            )

            # Optional: filter by course code
            if course_code:
                q = q.filter(Course.code.ilike(course_code))

            # Optional: filter by department (from NLP slot)
            dept = (slots.get("department") or "").strip()
            if dept:
                q = q.filter(Student.department.ilike(dept))

            rows = q.order_by(Student.id).all()
            results = []
            for st, co, en in rows:
                results.append(
                    {
                        "student_id": st.id,
                        "student_name": getattr(st, "name", None),
                        "course_code": co.code,
                        "course_title": co.title,
                        "semester": en.semester,
                        "status": en.status,
                        "grade": float(en.grade) if en.grade is not None else None,
                    }
                )
            return {**base, "info": f"Found {len(results)} student record(s) in your courses.", "results_type": "students", "results": results}

        # Student: not allowed
        raise HTTPException(status_code=403, detail="You are not allowed to list all students")

    # 4) list_enrollments_for_student
    if intent == "list_enrollments_for_student":
        # student_id parsing
        try:
            student_id = int(raw_sid) if raw_sid is not None else None
        except (TypeError, ValueError):
            student_id = None

        # Student: allow only self (if id missing -> self)
        if role == UserRole.student:
            my_id = _require_student(current_user)
            if student_id is None:
                student_id = my_id
            if student_id != my_id:
                raise HTTPException(status_code=403, detail="You can only view your own enrollments")

            rows = (
                db.query(Enrollment, Course)
                .join(Course, Course.id == Enrollment.course_id)
                .filter(Enrollment.student_id == student_id)
                .order_by(Enrollment.id)
                .all()
            )

            results = []
            for en, co in rows:
                results.append(
                    {
                        "id": en.id,
                        "student_id": en.student_id,
                        "course_code": co.code,
                        "course_title": co.title,
                        "semester": en.semester,
                        "status": en.status,
                        "grade": float(en.grade) if en.grade is not None else None,
                    }
                )
            return {**base, "info": f"Found {len(results)} enrollment(s).", "results_type": "enrollments", "results": results}

        # Admin/HOD: allow any student
        if role in (UserRole.admin, UserRole.hod):
            if not student_id:
                return {**base, "info": "Please specify a valid student id.", "results_type": "enrollments", "results": []}

            rows = (
                db.query(Enrollment, Student, Course)
                .join(Student, Student.id == Enrollment.student_id)
                .join(Course, Course.id == Enrollment.course_id)
                .filter(Enrollment.student_id == student_id)
                .order_by(Enrollment.id)
                .all()
            )

            results = []
            for en, st, co in rows:
                results.append(
                    {
                        "id": en.id,
                        "student_id": st.id,
                        "student_name": getattr(st, "name", None),
                        "course_code": co.code,
                        "course_title": co.title,
                        "semester": en.semester,
                        "status": en.status,
                        "grade": float(en.grade) if en.grade is not None else None,
                    }
                )
            return {**base, "info": f"Found {len(results)} enrollment(s) for student {student_id}.", "results_type": "enrollments", "results": results}

        # Teacher: allow only if student is in teacher's courses
        if role == UserRole.teacher:
            teacher_id = _require_teacher(current_user)
            if not student_id:
                return {**base, "info": "Please specify a valid student id.", "results_type": "enrollments", "results": []}

            rows = (
                db.query(Enrollment, Course, Student)
                .join(Course, Course.id == Enrollment.course_id)
                .join(Student, Student.id == Enrollment.student_id)
                .filter(Course.teacher_id == teacher_id)
                .filter(Enrollment.student_id == student_id)
                .order_by(Enrollment.id)
                .all()
            )

            results = []
            for en, co, st in rows:
                results.append(
                    {
                        "id": en.id,
                        "student_id": st.id,
                        "student_name": getattr(st, "name", None),
                        "course_code": co.code,
                        "course_title": co.title,
                        "semester": en.semester,
                        "status": en.status,
                        "grade": float(en.grade) if en.grade is not None else None,
                    }
                )

            return {**base, "info": f"Found {len(results)} enrollment(s) for student {student_id} in your courses.", "results_type": "enrollments", "results": results}

    # -----------------------------
    # FINAL fallback
    # -----------------------------
    return {
        **base,
        "info": "NLP parsed your command, but no concrete action is implemented for this intent yet.",
        "results_type": None,
        "results": [],
    }
