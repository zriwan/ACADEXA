from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db_connection
from backend.models import Course, Teacher, Student, Enrollment  # adjust if names differ
from backend.schemas import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
)

from ..security import get_current_user, require_admin

router = APIRouter(prefix="/courses", tags=["Courses"])


# ---------------------------
# CREATE — add course
# ---------------------------
@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),  # usually admin-only
):
    """
    Create a new course.
    Expected fields (example): code, title, department, teacher_id, credits, etc.
    """

    # optional: enforce unique course code
    exists = db.query(Course).filter(Course.code == payload.code).first()
    if exists:
        raise HTTPException(status_code=400, detail="Course code already in use")

    # optional: check teacher exists if teacher_id provided
    if getattr(payload, "teacher_id", None) is not None:
        teacher = db.get(Teacher, payload.teacher_id)
        if not teacher:
            raise HTTPException(status_code=404, detail="Assigned teacher not found")

    c = Course(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# --------------
# READ — list all
# --------------
@router.get("/", response_model=list[CourseResponse])
def list_courses(
    department: Optional[str] = None,
    teacher_id: Optional[int] = None,
    code_contains: Optional[str] = None,
    title_contains: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    """
    List courses with filters + pagination.
    """
    q = db.query(Course)

    if department:
        q = q.filter(Course.department == department)
    if teacher_id:
        q = q.filter(Course.teacher_id == teacher_id)
    if code_contains:
        q = q.filter(Course.code.ilike(f"%{code_contains}%"))
    if title_contains:
        q = q.filter(Course.title.ilike(f"%{title_contains}%"))

    return q.order_by(Course.id).offset(skip).limit(limit).all()


# ----------------
# READ — single by id
# ----------------
@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    return c


# -----------
# UPDATE — PUT
# -----------
@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),
):
    """
    Update existing course.

    Partial update: sirf woh fields change hongi
    jo request body me send ki gai hain.
    """
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = payload.model_dump(exclude_unset=True)

    # if code is being changed, keep it unique
    new_code = update_data.get("code")
    if new_code and new_code != c.code:
        exists = (
            db.query(Course)
            .filter(Course.code == new_code, Course.id != course_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Course code already in use")

    # if teacher_id changed, ensure teacher exists
    new_teacher_id = update_data.get("teacher_id")
    if new_teacher_id is not None:
        teacher = db.get(Teacher, new_teacher_id)
        if not teacher:
            raise HTTPException(status_code=404, detail="Assigned teacher not found")

    for field, value in update_data.items():
        setattr(c, field, value)

    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# ------------
# DELETE — by id
# ------------
@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),
):
    """
    Delete course by ID.
    Prevent deletion if enrollments exist.
    """
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")

    # check if any students still enrolled
    has_enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id)
        .count() > 0
    )
    if has_enrollments:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete: students are still enrolled in this course",
        )

    db.delete(c)
    db.commit()
    return None
