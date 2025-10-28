from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db_connection
from backend.models import Course, Enrollment, Student
from backend.schemas import (
    EnrollmentCreate,
    EnrollmentDetailResponse,
    EnrollmentResponse,
    EnrollmentUpdate,
)

# ✅ NEW: auth dependencies
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


# -----------------------
# CREATE
# -----------------------
@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"description": "Student/Course not found or already enrolled"}},
)
def enroll(
    payload: EnrollmentCreate,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),  # ✅ login required
):
    # FK validation
    if not db.get(Student, payload.student_id):
        raise HTTPException(status_code=400, detail="Student does not exist")
    if not db.get(Course, payload.course_id):
        raise HTTPException(status_code=400, detail="Course does not exist")

    e = Enrollment(
        student_id=payload.student_id,
        course_id=payload.course_id,
        semester=(payload.semester.strip() if payload.semester else None),
        status="enrolled",
        grade=None,
    )
    db.add(e)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # UniqueConstraint on (student_id, course_id)
        raise HTTPException(
            status_code=400, detail="Student already enrolled in this course"
        )
    db.refresh(e)
    return e


# -----------------------
# UPDATE (partial)
# -----------------------
@router.patch("/{enrollment_id}", response_model=EnrollmentResponse)
def update_enrollment(
    enrollment_id: int,
    payload: EnrollmentUpdate,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),  # ✅ login required
):
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if payload.status is not None:
        allowed = {"enrolled", "dropped", "completed"}
        if payload.status not in allowed:
            raise HTTPException(
                status_code=400, detail=f"Invalid status. Allowed: {', '.join(allowed)}"
            )
        e.status = payload.status

    if payload.semester is not None:
        e.semester = payload.semester.strip() or None

    if payload.grade is not None:
        e.grade = round(float(payload.grade), 2)

    db.add(e)
    db.commit()
    db.refresh(e)
    return e


# -----------------------
# DELETE (unenroll)
# -----------------------
@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll(
    enrollment_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),  # ✅ admin-only
):
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    db.delete(e)
    db.commit()
    return None


# -----------------------
# SIMPLE LISTS
# -----------------------
@router.get("/student/{student_id}", response_model=list[EnrollmentResponse])
def list_student_enrollments(student_id: int, db: Session = Depends(get_db_connection)):
    # If you prefer strict behavior, uncomment next two lines:
    # if not db.get(Student, student_id):
    #     raise HTTPException(status_code=404, detail="Student not found")
    return (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id)
        .order_by(Enrollment.id)
        .all()
    )


@router.get("/course/{course_id}", response_model=list[EnrollmentResponse])
def list_course_enrollments(course_id: int, db: Session = Depends(get_db_connection)):
    # if not db.get(Course, course_id):
    #     raise HTTPException(status_code=404, detail="Course not found")
    return (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id)
        .order_by(Enrollment.id)
        .all()
    )


# -----------------------
# DETAILS WITH FILTERS + PAGINATION
# -----------------------
@router.get(
    "/student/{student_id}/details", response_model=list[EnrollmentDetailResponse]
)
def list_student_enrollments_with_details(
    student_id: int,
    semester: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
):
    if not db.get(Student, student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    q = (
        db.query(Enrollment)
        .options(selectinload(Enrollment.student), selectinload(Enrollment.course))
        .filter(Enrollment.student_id == student_id)
    )
    if semester:
        q = q.filter(Enrollment.semester == semester)
    if status:
        q = q.filter(Enrollment.status == status)

    return q.order_by(Enrollment.id).offset(skip).limit(limit).all()


@router.get(
    "/course/{course_id}/details", response_model=list[EnrollmentDetailResponse]
)
def list_course_enrollments_with_details(
    course_id: int,
    semester: str | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
):
    if not db.get(Course, course_id):
        raise HTTPException(status_code=404, detail="Course not found")

    q = (
        db.query(Enrollment)
        .options(selectinload(Enrollment.student), selectinload(Enrollment.course))
        .filter(Enrollment.course_id == course_id)
    )
    if semester:
        q = q.filter(Enrollment.semester == semester)
    if status:
        q = q.filter(Enrollment.status == status)

    return q.order_by(Enrollment.id).offset(skip).limit(limit).all()
