# backend/routes/voice.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db_connection
from backend.security import get_current_user, hash_password
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
    parsed = parse_command(raw_text)

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
    # ✅ CREATE Operations
    # -----------------------------
    
    # create_student
    if intent == "create_student":
        _require_admin_or_hod(current_user)
        
        name = slots.get("name")
        if not name:
            return {**base, "info": "Please provide a student name.", "results_type": None, "results": []}
        
        student_data = {
            "name": name,
            "department": slots.get("department") or "CS",
            "gpa": slots.get("gpa") or 0.0,
        }
        
        email = slots.get("email")
        password = slots.get("password")
        
        if email and password:
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return {**base, "info": f"Email {email} already registered.", "results_type": None, "results": []}
            
            user = User(
                name=name,
                email=email,
                hashed_password=hash_password(password),
                role=UserRole.student,
            )
            db.add(user)
            db.flush()
            student_data["user_id"] = user.id
        
        student = Student(**student_data)
        db.add(student)
        db.commit()
        db.refresh(student)
        
        return {
            **base,
            "info": f"Student '{name}' created successfully with ID {student.id}.",
            "results_type": "student",
            "results": [{"id": student.id, "name": student.name, "department": student.department, "gpa": float(student.gpa) if student.gpa else None}],
        }
    
    # create_teacher
    if intent == "create_teacher":
        _require_admin_or_hod(current_user)
        
        name = slots.get("name")
        if not name:
            return {**base, "info": "Please provide a teacher name.", "results_type": None, "results": []}
        
        import secrets
        
        email = slots.get("email")
        if not email:
            return {**base, "info": "Please provide an email address.", "results_type": None, "results": []}
        
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return {**base, "info": f"Email {email} already registered.", "results_type": None, "results": []}
        
        password = slots.get("password")
        temp_password = password or secrets.token_urlsafe(10)
        
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(temp_password),
            role=UserRole.teacher,
        )
        db.add(user)
        db.flush()
        
        teacher = Teacher(
            name=name,
            department=slots.get("department") or "CS",
            email=email,
            expertise=slots.get("expertise"),
            user_id=user.id,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        
        return {
            **base,
            "info": f"Teacher '{name}' created successfully. Teacher ID: {teacher.id}, Password: {temp_password}",
            "results_type": "teacher",
            "results": [{"id": teacher.id, "name": teacher.name, "department": teacher.department, "email": teacher.email}],
        }
    
    # create_course
    if intent == "create_course":
        _require_admin_or_hod(current_user)
        
        title = slots.get("title")
        if not title:
            return {**base, "info": "Please provide a course title.", "results_type": None, "results": []}
        
        code = slots.get("code") or f"CS-{db.query(Course).count() + 1}"
        credit_hours = slots.get("credit_hours") or 3
        teacher_id = slots.get("teacher_id")
        
        existing = db.query(Course).filter(Course.code == code).first()
        if existing:
            return {**base, "info": f"Course code '{code}' already exists.", "results_type": None, "results": []}
        
        if teacher_id:
            teacher = db.get(Teacher, teacher_id)
            if not teacher:
                return {**base, "info": f"Teacher with ID {teacher_id} not found.", "results_type": None, "results": []}
        
        course = Course(
            title=title,
            code=code,
            credit_hours=credit_hours,
            teacher_id=teacher_id,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        
        return {
            **base,
            "info": f"Course '{title}' ({code}) created successfully with ID {course.id}.",
            "results_type": "course",
            "results": [{"id": course.id, "title": course.title, "code": course.code, "credit_hours": course.credit_hours}],
        }
    
    # create_enrollment
    if intent == "create_enrollment":
        role = _role_value(current_user.role)
        if role not in (UserRole.admin, UserRole.hod, UserRole.teacher):
            raise HTTPException(status_code=403, detail="Admin/HOD/Teacher access required")
        
        student_id = slots.get("student_id")
        course_id = slots.get("course_id")
        
        if not student_id or not course_id:
            return {**base, "info": "Please provide both student ID and course ID.", "results_type": None, "results": []}
        
        student = db.get(Student, student_id)
        if not student:
            return {**base, "info": f"Student with ID {student_id} not found.", "results_type": None, "results": []}
        
        course = db.get(Course, course_id)
        if not course:
            return {**base, "info": f"Course with ID {course_id} not found.", "results_type": None, "results": []}
        
        # Check if already enrolled
        existing = db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        ).first()
        if existing:
            return {**base, "info": f"Student {student_id} is already enrolled in course {course_id}.", "results_type": None, "results": []}
        
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            semester=slots.get("semester"),
            status=slots.get("status") or "enrolled",
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        
        return {
            **base,
            "info": f"Student {student_id} enrolled in course {course_id} successfully.",
            "results_type": "enrollment",
            "results": [{"id": enrollment.id, "student_id": enrollment.student_id, "course_id": enrollment.course_id, "status": enrollment.status}],
        }
    
    # -----------------------------
    # ✅ UPDATE Operations
    # -----------------------------
    
    # update_student
    if intent == "update_student":
        _require_admin_or_hod(current_user)
        
        student_id = slots.get("student_id")
        if not student_id:
            return {**base, "info": "Please provide a student ID.", "results_type": None, "results": []}
        
        student = db.get(Student, student_id)
        if not student:
            return {**base, "info": f"Student with ID {student_id} not found.", "results_type": None, "results": []}
        
        if slots.get("name"):
            student.name = slots.get("name")
        if slots.get("department"):
            student.department = slots.get("department")
        if slots.get("gpa") is not None:
            student.gpa = slots.get("gpa")
        
        db.add(student)
        db.commit()
        db.refresh(student)
        
        return {
            **base,
            "info": f"Student {student_id} updated successfully.",
            "results_type": "student",
            "results": [{"id": student.id, "name": student.name, "department": student.department, "gpa": float(student.gpa) if student.gpa else None}],
        }
    
    # update_teacher
    if intent == "update_teacher":
        _require_admin_or_hod(current_user)
        
        teacher_id = slots.get("teacher_id")
        if not teacher_id:
            return {**base, "info": "Please provide a teacher ID.", "results_type": None, "results": []}
        
        teacher = db.get(Teacher, teacher_id)
        if not teacher:
            return {**base, "info": f"Teacher with ID {teacher_id} not found.", "results_type": None, "results": []}
        
        if slots.get("name"):
            teacher.name = slots.get("name")
        if slots.get("department"):
            teacher.department = slots.get("department")
        if slots.get("expertise"):
            teacher.expertise = slots.get("expertise")
        
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        
        return {
            **base,
            "info": f"Teacher {teacher_id} updated successfully.",
            "results_type": "teacher",
            "results": [{"id": teacher.id, "name": teacher.name, "department": teacher.department, "expertise": teacher.expertise}],
        }
    
    # update_course
    if intent == "update_course":
        _require_admin_or_hod(current_user)
        
        course_id = slots.get("course_id")
        course_code = slots.get("course_code")
        
        if not course_id and not course_code:
            return {**base, "info": "Please provide a course ID or code.", "results_type": None, "results": []}
        
        if course_code and not course_id:
            course = db.query(Course).filter(Course.code.ilike(course_code)).first()
            if not course:
                return {**base, "info": f"Course with code '{course_code}' not found.", "results_type": None, "results": []}
        else:
            course = db.get(Course, course_id)
            if not course:
                return {**base, "info": f"Course with ID {course_id} not found.", "results_type": None, "results": []}
        
        if slots.get("title"):
            course.title = slots.get("title")
        if slots.get("code"):
            existing = db.query(Course).filter(Course.code == slots.get("code"), Course.id != course.id).first()
            if existing:
                return {**base, "info": f"Course code '{slots.get('code')}' already exists.", "results_type": None, "results": []}
            course.code = slots.get("code")
        if slots.get("credit_hours"):
            course.credit_hours = slots.get("credit_hours")
        if slots.get("teacher_id"):
            teacher = db.get(Teacher, slots.get("teacher_id"))
            if not teacher:
                return {**base, "info": f"Teacher with ID {slots.get('teacher_id')} not found.", "results_type": None, "results": []}
            course.teacher_id = slots.get("teacher_id")
        
        db.add(course)
        db.commit()
        db.refresh(course)
        
        return {
            **base,
            "info": f"Course {course.id} updated successfully.",
            "results_type": "course",
            "results": [{"id": course.id, "title": course.title, "code": course.code, "credit_hours": course.credit_hours}],
        }
    
    # update_enrollment
    if intent == "update_enrollment":
        role = _role_value(current_user.role)
        if role not in (UserRole.admin, UserRole.hod, UserRole.teacher):
            raise HTTPException(status_code=403, detail="Admin/HOD/Teacher access required")
        
        enrollment_id = slots.get("enrollment_id")
        if not enrollment_id:
            return {**base, "info": "Please provide an enrollment ID.", "results_type": None, "results": []}
        
        enrollment = db.get(Enrollment, enrollment_id)
        if not enrollment:
            return {**base, "info": f"Enrollment with ID {enrollment_id} not found.", "results_type": None, "results": []}
        
        # Teacher can only update enrollments in their courses
        if role == UserRole.teacher:
            teacher_id = _require_teacher(current_user)
            course = db.get(Course, enrollment.course_id)
            if not course or course.teacher_id != teacher_id:
                raise HTTPException(status_code=403, detail="You can only update enrollments of your own courses")
        
        if slots.get("grade") is not None:
            enrollment.grade = slots.get("grade")
        if slots.get("status"):
            enrollment.status = slots.get("status")
        if slots.get("semester"):
            enrollment.semester = slots.get("semester")
        
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        
        # Recalculate GPA if grade was updated
        if slots.get("grade") is not None:
            enroll_rows = (
                db.query(Enrollment, Course)
                .join(Course, Course.id == Enrollment.course_id)
                .filter(Enrollment.student_id == enrollment.student_id)
                .all()
            )
            
            total_points = 0.0
            total_credits = 0.0
            
            for en, co in enroll_rows:
                if en.grade is None:
                    continue
                ch = float(getattr(co, "credit_hours", 0) or 0)
                if ch <= 0:
                    continue
                total_points += float(en.grade) * ch
                total_credits += ch
            
            new_gpa = round(total_points / total_credits, 2) if total_credits > 0 else None
            
            student = db.get(Student, enrollment.student_id)
            if student:
                student.gpa = new_gpa
                db.add(student)
                db.commit()
        
        return {
            **base,
            "info": f"Enrollment {enrollment_id} updated successfully.",
            "results_type": "enrollment",
            "results": [{"id": enrollment.id, "student_id": enrollment.student_id, "course_id": enrollment.course_id, "grade": float(enrollment.grade) if enrollment.grade else None, "status": enrollment.status}],
        }
    
    # -----------------------------
    # ✅ DELETE Operations
    # -----------------------------
    
    # delete_student
    if intent == "delete_student":
        _require_admin_or_hod(current_user)
        
        student_id = slots.get("student_id")
        if not student_id:
            return {**base, "info": "Please provide a student ID.", "results_type": None, "results": []}
        
        student = db.get(Student, student_id)
        if not student:
            return {**base, "info": f"Student with ID {student_id} not found.", "results_type": None, "results": []}
        
        db.delete(student)
        db.commit()
        
        return {
            **base,
            "info": f"Student {student_id} deleted successfully.",
            "results_type": None,
            "results": [],
        }
    
    # delete_teacher
    if intent == "delete_teacher":
        _require_admin_or_hod(current_user)
        
        teacher_id = slots.get("teacher_id")
        if not teacher_id:
            return {**base, "info": "Please provide a teacher ID.", "results_type": None, "results": []}
        
        teacher = db.get(Teacher, teacher_id)
        if not teacher:
            return {**base, "info": f"Teacher with ID {teacher_id} not found.", "results_type": None, "results": []}
        
        has_courses = db.query(Course).filter(Course.teacher_id == teacher_id).count() > 0
        if has_courses:
            return {**base, "info": f"Cannot delete teacher {teacher_id}: teacher has assigned courses.", "results_type": None, "results": []}
        
        db.delete(teacher)
        db.commit()
        
        return {
            **base,
            "info": f"Teacher {teacher_id} deleted successfully.",
            "results_type": None,
            "results": [],
        }
    
    # delete_course
    if intent == "delete_course":
        _require_admin_or_hod(current_user)
        
        course_id = slots.get("course_id")
        course_code = slots.get("course_code")
        
        if not course_id and not course_code:
            return {**base, "info": "Please provide a course ID or code.", "results_type": None, "results": []}
        
        if course_code and not course_id:
            course = db.query(Course).filter(Course.code.ilike(course_code)).first()
            if not course:
                return {**base, "info": f"Course with code '{course_code}' not found.", "results_type": None, "results": []}
            course_id = course.id
        else:
            course = db.get(Course, course_id)
            if not course:
                return {**base, "info": f"Course with ID {course_id} not found.", "results_type": None, "results": []}
        
        has_enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).count() > 0
        if has_enrollments:
            return {**base, "info": f"Cannot delete course {course_id}: students are still enrolled.", "results_type": None, "results": []}
        
        db.delete(course)
        db.commit()
        
        return {
            **base,
            "info": f"Course {course_id} deleted successfully.",
            "results_type": None,
            "results": [],
        }
    
    # delete_enrollment
    if intent == "delete_enrollment":
        _require_admin_or_hod(current_user)
        
        enrollment_id = slots.get("enrollment_id")
        student_id = slots.get("student_id")
        course_id = slots.get("course_id")
        
        if enrollment_id:
            enrollment = db.get(Enrollment, enrollment_id)
            if not enrollment:
                return {**base, "info": f"Enrollment with ID {enrollment_id} not found.", "results_type": None, "results": []}
            db.delete(enrollment)
            db.commit()
            return {
                **base,
                "info": f"Enrollment {enrollment_id} deleted successfully.",
                "results_type": None,
                "results": [],
            }
        elif student_id and course_id:
            enrollment = db.query(Enrollment).filter(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
            ).first()
            if not enrollment:
                return {**base, "info": f"Enrollment not found for student {student_id} in course {course_id}.", "results_type": None, "results": []}
            db.delete(enrollment)
            db.commit()
            return {
                **base,
                "info": f"Enrollment deleted successfully for student {student_id} in course {course_id}.",
                "results_type": None,
                "results": [],
            }
        else:
            return {**base, "info": "Please provide enrollment ID or both student ID and course ID.", "results_type": None, "results": []}
    
    # -----------------------------
    # ✅ GET Operations (single item)
    # -----------------------------
    
    # get_student
    if intent == "get_student":
        _require_admin_or_hod(current_user)
        
        student_id = slots.get("student_id")
        if not student_id:
            return {**base, "info": "Please provide a student ID.", "results_type": None, "results": []}
        
        student = db.get(Student, student_id)
        if not student:
            return {**base, "info": f"Student with ID {student_id} not found.", "results_type": "student", "results": []}
        
        return {
            **base,
            "info": f"Found student {student_id}.",
            "results_type": "student",
            "results": [{"id": student.id, "name": student.name, "department": student.department, "gpa": float(student.gpa) if student.gpa else None}],
        }
    
    # get_teacher
    if intent == "get_teacher":
        _require_admin_or_hod(current_user)
        
        teacher_id = slots.get("teacher_id")
        if not teacher_id:
            return {**base, "info": "Please provide a teacher ID.", "results_type": None, "results": []}
        
        teacher = db.get(Teacher, teacher_id)
        if not teacher:
            return {**base, "info": f"Teacher with ID {teacher_id} not found.", "results_type": "teacher", "results": []}
        
        return {
            **base,
            "info": f"Found teacher {teacher_id}.",
            "results_type": "teacher",
            "results": [{"id": teacher.id, "name": teacher.name, "department": teacher.department, "email": teacher.email, "expertise": teacher.expertise}],
        }
    
    # get_course
    if intent == "get_course":
        role = _role_value(current_user.role)
        if role not in (UserRole.admin, UserRole.hod, UserRole.teacher, UserRole.student):
            raise HTTPException(status_code=403, detail="Access required")
        
        course_id = slots.get("course_id")
        course_code = slots.get("course_code")
        
        if not course_id and not course_code:
            return {**base, "info": "Please provide a course ID or code.", "results_type": None, "results": []}
        
        if course_code and not course_id:
            course = db.query(Course).filter(Course.code.ilike(course_code)).first()
            if not course:
                return {**base, "info": f"Course with code '{course_code}' not found.", "results_type": "course", "results": []}
        else:
            course = db.get(Course, course_id)
            if not course:
                return {**base, "info": f"Course with ID {course_id} not found.", "results_type": "course", "results": []}
        
        return {
            **base,
            "info": f"Found course {course.id}.",
            "results_type": "course",
            "results": [{"id": course.id, "title": course.title, "code": course.code, "credit_hours": course.credit_hours, "teacher_id": course.teacher_id}],
        }
    
    # -----------------------------
    # FINAL fallback
    # -----------------------------
    return {
        **base,
        "info": "NLP parsed your command, but no concrete action is implemented for this intent yet.",
        "results_type": None,
        "results": [],
    }
