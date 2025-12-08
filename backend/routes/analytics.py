from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db_connection
from backend.models import Enrollment, Course, Student, Teacher

from ..security import get_current_user, require_admin  # if you want admin-only, use this

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# -------------------------------------------------
# 1) Courses → enrollment counts (most popular etc.)
# -------------------------------------------------
@router.get("/courses/enrollment_counts")
def analytics_course_enrollment_counts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),  # ✅ at least logged-in user
):
    """
    Return per-course enrollment counts.

    Response example:
    [
      {
        "course_id": 1,
        "course_code": "CS101",
        "course_title": "Intro to CS",
        "department": "CS",
        "enrollment_count": 42
      },
      ...
    ]
    """

    q = (
        db.query(
            Course.id.label("course_id"),
            Course.code.label("course_code"),
            Course.title.label("course_title"),
            Course.department.label("department"),
            func.count(Enrollment.id).label("enrollment_count"),
        )
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .group_by(Course.id, Course.code, Course.title, Course.department)
        .order_by(func.count(Enrollment.id).desc())
        .offset(skip)
        .limit(limit)
    )

    rows = q.all()
    return [
        {
            "course_id": r.course_id,
            "course_code": r.course_code,
            "course_title": r.course_title,
            "department": r.department,
            "enrollment_count": int(r.enrollment_count),
        }
        for r in rows
    ]


# -------------------------------------------------
# 2) Departments → GPA summary
# -------------------------------------------------
@router.get("/departments/gpa_summary")
def analytics_department_gpa_summary(
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    """
    Department-wise GPA summary based on Enrollment.grade.

    Response example:
    [
      {
        "department": "CS",
        "student_count": 120,
        "avg_gpa": 3.12
      },
      ...
    ]

    Note: grade NULL / None values are ignored.
    """

    q = (
        db.query(
            Student.department.label("department"),
            func.count(func.distinct(Student.id)).label("student_count"),
            func.avg(Enrollment.grade).label("avg_gpa"),
        )
        .join(Enrollment, Enrollment.student_id == Student.id)
        .filter(Enrollment.grade.isnot(None))
        .group_by(Student.department)
        .order_by(Student.department)
    )

    rows = q.all()
    return [
        {
            "department": r.department,
            "student_count": int(r.student_count),
            "avg_gpa": float(r.avg_gpa) if r.avg_gpa is not None else None,
        }
        for r in rows
    ]


# -------------------------------------------------
# 3) Teachers → course load + total enrollments
# -------------------------------------------------
@router.get("/teachers/course_load")
def analytics_teacher_course_load(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),
):
    """
    Teacher-wise course load and total enrollments.

    Response example:
    [
      {
        "teacher_id": 5,
        "teacher_name": "Dr. Ahmed",
        "department": "CS",
        "course_count": 3,
        "total_enrollments": 95
      },
      ...
    ]
    """

    q = (
        db.query(
            Teacher.id.label("teacher_id"),
            Teacher.name.label("teacher_name"),
            Teacher.department.label("department"),
            func.count(func.distinct(Course.id)).label("course_count"),
            func.count(Enrollment.id).label("total_enrollments"),
        )
        .outerjoin(Course, Course.teacher_id == Teacher.id)
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .group_by(Teacher.id, Teacher.name, Teacher.department)
        .order_by(func.count(Enrollment.id).desc())
        .offset(skip)
        .limit(limit)
    )

    rows = q.all()
    return [
        {
            "teacher_id": r.teacher_id,
            "teacher_name": r.teacher_name,
            "department": r.department,
            "course_count": int(r.course_count),
            "total_enrollments": int(r.total_enrollments),
        }
        for r in rows
    ]
