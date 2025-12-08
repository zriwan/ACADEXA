from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.models import Enrollment, Student, Course
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
    _=Depends(get_current_user),
):
    """
    Partially update an enrollment.
    Typical editable fields:
    - semester
    - status
    - grade
    """
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    update_data = payload.model_dump(exclude_unset=True)

    # optionally you can restrict which fields are allowed to update
    # e.g. only: semester, status, grade
    allowed_fields = {"semester", "status", "grade"}
    for field, value in update_data.items():
        if field not in allowed_fields:
            continue
        setattr(e, field, value)

    db.add(e)
    db.commit()
    db.refresh(e)
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
