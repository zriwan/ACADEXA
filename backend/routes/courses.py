from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db_connection
from backend.models import Course, Teacher, Enrollment
from backend.schemas import CourseCreate, CourseUpdate, CourseResponse
from backend.security import get_current_user, require_admin

router = APIRouter(prefix="/courses", tags=["Courses"])


# =====================================================
# CREATE COURSE (ADMIN ONLY)
# =====================================================
@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),
):
    # Enforce unique course code
    exists = db.query(Course).filter(Course.code == payload.code).first()
    if exists:
        raise HTTPException(status_code=400, detail="Course code already in use")

    # Validate teacher if provided
    if payload.teacher_id is not None:
        teacher = db.get(Teacher, payload.teacher_id)
        if not teacher:
            raise HTTPException(status_code=404, detail="Assigned teacher not found")

    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


# =====================================================
# LIST COURSES (AUTH REQUIRED)
# =====================================================
@router.get("/", response_model=list[CourseResponse])
def list_courses(
    teacher_id: Optional[int] = None,
    code_contains: Optional[str] = None,
    title_contains: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    q = db.query(Course)

    if teacher_id is not None:
        q = q.filter(Course.teacher_id == teacher_id)

    if code_contains:
        q = q.filter(Course.code.ilike(f"%{code_contains}%"))

    if title_contains:
        q = q.filter(Course.title.ilike(f"%{title_contains}%"))

    return q.order_by(Course.id).offset(skip).limit(limit).all()


# =====================================================
# GET SINGLE COURSE (AUTH REQUIRED)
# =====================================================
@router.get("/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


# =====================================================
# UPDATE COURSE (ADMIN ONLY)
# =====================================================
@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Unique code check
    if "code" in update_data and update_data["code"] != course.code:
        exists = (
            db.query(Course)
            .filter(Course.code == update_data["code"], Course.id != course_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Course code already in use")

    # Validate teacher
    if "teacher_id" in update_data and update_data["teacher_id"] is not None:
        teacher = db.get(Teacher, update_data["teacher_id"])
        if not teacher:
            raise HTTPException(status_code=404, detail="Assigned teacher not found")

    for field, value in update_data.items():
        setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return course


# =====================================================
# DELETE COURSE (ADMIN ONLY)
# =====================================================
@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),
):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Prevent delete if enrollments exist
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

    db.delete(course)
    db.commit()
    return None
