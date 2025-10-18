# backend/routes/analytics.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, cast, Float
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.models import Student, Course, Teacher, Enrollment

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# ----------------------------------------------
# A) Enrollment counts per course
# ----------------------------------------------
@router.get("/courses/enrollment_counts")
def courses_enrollment_counts(
    db: Session = Depends(get_db_connection),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    q = (
        db.query(
            Course.id.label("course_id"),
            Course.title,
            Course.code,
            func.count(Enrollment.id).label("enrollment_count"),
        )
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .group_by(Course.id)
        .order_by(func.count(Enrollment.id).desc(), Course.id.asc())
        .offset(skip)
        .limit(limit)
    )
    return [dict(row._mapping) for row in q.all()]

# ----------------------------------------------
# B) Average GPA of enrolled students per course
# ----------------------------------------------
@router.get("/courses/avg_gpa")
def courses_avg_gpa(
    db: Session = Depends(get_db_connection),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    q = (
        db.query(
            Course.id.label("course_id"),
            Course.title,
            Course.code,
            cast(func.avg(Student.gpa), Float).label("avg_gpa"),
            func.count(Enrollment.id).label("enrollment_count"),
        )
        .join(Enrollment, Enrollment.course_id == Course.id)
        .join(Student, Student.id == Enrollment.student_id)
        .group_by(Course.id)
        .order_by(func.coalesce(func.avg(Student.gpa), 0).desc())
        .offset(skip)
        .limit(limit)
    )
    return [dict(row._mapping) for row in q.all()]

# ----------------------------------------------
# C) Average GPA by department (based on Students table)
# ----------------------------------------------
@router.get("/departments/avg_gpa")
def departments_avg_gpa(
    db: Session = Depends(get_db_connection),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    q = (
        db.query(
            Student.department,
            cast(func.avg(Student.gpa), Float).label("avg_gpa"),
            func.count(Student.id).label("student_count"),
        )
        .group_by(Student.department)
        .order_by(cast(func.avg(Student.gpa), Float).desc())
        .offset(skip)
        .limit(limit)
    )
    return [dict(row._mapping) for row in q.all()]

# ----------------------------------------------
# D) Teacher load: courses taught + total enrollments across their courses
# ----------------------------------------------
@router.get("/teachers/course_load")
def teachers_course_load(
    db: Session = Depends(get_db_connection),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    # courses_count = count distinct courses per teacher
    # total_enrollments = count enrollments on those courses
    sub = (
        db.query(
            Teacher.id.label("teacher_id"),
            Teacher.name.label("teacher_name"),
            func.count(func.distinct(Course.id)).label("courses_count"),
            func.count(Enrollment.id).label("total_enrollments"),
        )
        .outerjoin(Course, Course.teacher_id == Teacher.id)
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .group_by(Teacher.id)
        .order_by(func.count(Enrollment.id).desc(), func.count(func.distinct(Course.id)).desc())
        .offset(skip)
        .limit(limit)
    )
    return [dict(row._mapping) for row in sub.all()]
