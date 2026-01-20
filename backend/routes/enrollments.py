from typing import Optional, List
from backend.models import Enrollment, Course, Student, User, UserRole

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_db_connection

from backend.schemas import (
    EnrollmentCreate,
    EnrollmentUpdate,
    EnrollmentResponse,
)

from ..security import get_current_user, require_admin

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


# ---------------------------
# CREATE — enroll a student in a course
# ---------------------------
@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),  # ✅ login required (teacher/admin/staff etc.)
):
    """
    Enroll a student into a course.

    Expected EnrollmentCreate fields (example):
    - student_id: int
    - course_id: int
    - semester: str | None
    - status: str | None (e.g., "enrolled")
    - grade: float | None
    """

    # ensure student exists
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # ensure course exists
    course = db.get(Course, payload.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # prevent duplicate enrollment (same student, same course)
    exists = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == payload.student_id,
            Enrollment.course_id == payload.course_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=400,
            detail="Student is already enrolled in this course",
        )

    e = Enrollment(**payload.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


# --------------
# READ — list all (with filters)
# --------------
@router.get("/", response_model=List[EnrollmentResponse])
def list_enrollments(
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    semester: Optional[str] = None,
    status_: Optional[str] = Query(None, alias="status"),  # ?status=active etc.
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    """
    List enrollments with optional filters + pagination.
    """
    q = db.query(Enrollment)

    if student_id is not None:
        q = q.filter(Enrollment.student_id == student_id)
    if course_id is not None:
        q = q.filter(Enrollment.course_id == course_id)
    if semester is not None:
        q = q.filter(Enrollment.semester == semester)
    if status_ is not None:
        q = q.filter(Enrollment.status == status_)

    return q.order_by(Enrollment.id).offset(skip).limit(limit).all()


# ----------------
# READ — by student
# ----------------
@router.get("/by-student/{student_id}", response_model=List[EnrollmentResponse])
def list_enrollments_by_student(
    student_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    """
    Get all enrollments for a given student.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id)
        .order_by(Enrollment.id)
        .all()
    )
    return enrollments


# ----------------
# READ — by course
# ----------------
@router.get("/by-course/{course_id}", response_model=List[EnrollmentResponse])
def list_enrollments_by_course(
    course_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    """
    Get all enrollments for a given course (all students in the course).
    """
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id)
        .order_by(Enrollment.id)
        .all()
    )
    return enrollments


# -----------
# UPDATE — PATCH (status / semester / grade etc.)
# -----------
@router.patch("/{enrollment_id}", response_model=EnrollmentResponse)
def update_enrollment(
    enrollment_id: int,
    payload: EnrollmentUpdate,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),  # ✅ get user
):
    """
    Teacher-only: update an enrollment (grade/status/semester)
    Rules:
      - Only TEACHER can update
      - Teacher can update ONLY enrollments of courses they teach
      - After grade update, student GPA is auto recalculated
    """
    # ✅ role check
    role_val = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_val != UserRole.teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")

    # ✅ teacher linked check
    if not current_user.teacher:
        raise HTTPException(status_code=404, detail="Teacher record not linked")

    teacher_id = current_user.teacher.id

    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    # ✅ ownership check: enrollment course must belong to this teacher
    course = db.get(Course, e.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.teacher_id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update enrollments of your own courses",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # ✅ only allowed fields
    allowed_fields = {"semester", "status", "grade"}
    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(e, field, value)

    db.add(e)
    db.commit()
    db.refresh(e)

    # ✅ GPA auto recalculation after grade update
    # GPA = sum(grade*credit_hours) / sum(credit_hours) for non-null grades
    enroll_rows = (
        db.query(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Enrollment.student_id == e.student_id)
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

    student = db.get(Student, e.student_id)
    if student:
        student.gpa = new_gpa
        db.add(student)
        db.commit()

    return e


# ------------
# DELETE — drop enrollment
# ------------
@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),  # ✅ admin-only (ya policy ke hisaab se)
):
    """
    Delete (drop) an enrollment by ID.
    """
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    db.delete(e)
    db.commit()
    return None  # 204
