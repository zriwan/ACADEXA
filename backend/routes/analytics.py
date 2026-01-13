# backend/routes/analytics.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from backend.database import get_db_connection
from backend.security import get_current_user
from backend.models import Student, Course, Teacher, Enrollment

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

# =====================================================
# SUMMARY ANALYTICS
# =====================================================
@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db_connection),
    current_user=Depends(get_current_user),
):
    """
    High-level system summary.
    """

    total_students = db.query(func.count(Student.id)).scalar() or 0
    total_courses = db.query(func.count(Course.id)).scalar() or 0
    total_teachers = db.query(func.count(Teacher.id)).scalar() or 0
    total_enrollments = db.query(func.count(Enrollment.id)).scalar() or 0

    avg_gpa_raw = db.query(func.avg(Student.gpa)).scalar()
    avg_gpa = float(avg_gpa_raw) if avg_gpa_raw is not None else None

    return {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_teachers": total_teachers,
        "total_enrollments": total_enrollments,
        "avg_gpa": avg_gpa,
    }


# =====================================================
# COURSE STATISTICS
# =====================================================
@router.get("/course-stats")
def get_course_stats(
    db: Session = Depends(get_db_connection),
    current_user=Depends(get_current_user),
):
    """
    Per-course analytics:
    - total enrollments
    - average grade
    - pass rate
    """

    rows = (
        db.query(
            Course.id.label("id"),
            Course.code.label("code"),
            Course.title.label("title"),
            func.count(Enrollment.id).label("total_enrollments"),
            func.avg(Enrollment.grade).label("avg_grade"),
            func.sum(
                case(
                    (Enrollment.status == "passed", 1),
                    else_=0
                )
            ).label("passed_count"),
        )
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .group_by(Course.id, Course.code, Course.title)
        .order_by(Course.code)
        .all()
    )

    results = []

    for r in rows:
        total = int(r.total_enrollments or 0)
        passed = int(r.passed_count or 0)

        avg_grade = None
        if r.avg_grade is not None:
            try:
                avg_grade = float(r.avg_grade)
            except Exception:
                avg_grade = None

        pass_rate = round((passed / total) * 100, 2) if total > 0 else None

        results.append({
            "id": r.id,
            "code": r.code,
            "title": r.title,
            "total_enrollments": total,
            "avg_grade": avg_grade,
            "pass_rate": pass_rate,
        })

    return results


# =====================================================
# DEPARTMENT STATISTICS (DEFENSIVE & BUG-FREE)
# =====================================================
@router.get("/department-stats")
def get_department_stats(
    db: Session = Depends(get_db_connection),
    current_user=Depends(get_current_user),
):
    """
    Per-department analytics:
    - total students
    - total courses
    - average GPA
    """

    stats: dict[str, dict] = {}

    # -----------------------------
    # Students per department
    # -----------------------------
    student_rows = (
        db.query(
            Student.department.label("department"),
            func.count(Student.id).label("total_students"),
            func.avg(Student.gpa).label("avg_gpa"),
        )
        .filter(Student.department.isnot(None))
        .group_by(Student.department)
        .all()
    )

    for r in student_rows:
        dept = str(r.department).strip()
        if not dept:
            continue

        avg_gpa = None
        if r.avg_gpa is not None:
            try:
                avg_gpa = float(r.avg_gpa)
            except Exception:
                avg_gpa = None

        stats[dept] = {
            "department": dept,
            "total_students": int(r.total_students or 0),
            "total_courses": 0,
            "avg_gpa": avg_gpa,
        }

    # -----------------------------
    # Courses per department (optional)
    # -----------------------------
    if hasattr(Course, "department"):
        course_rows = (
            db.query(
                Course.department.label("department"),
                func.count(Course.id).label("total_courses"),
            )
            .filter(Course.department.isnot(None))
            .group_by(Course.department)
            .all()
        )

        for r in course_rows:
            dept = str(r.department).strip()
            if not dept:
                continue

            stats.setdefault(
                dept,
                {
                    "department": dept,
                    "total_students": 0,
                    "total_courses": 0,
                    "avg_gpa": None,
                }
            )
            stats[dept]["total_courses"] = int(r.total_courses or 0)

    return sorted(stats.values(), key=lambda x: x["department"])
