# backend/routes/analytics.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db_connection
from backend.security import get_current_user
from backend.models import Student, Course, Teacher, Enrollment

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db_connection),
    current_user=Depends(get_current_user),
):
    """
    Returns high-level stats for the dashboard.

    - total_students
    - total_courses
    - total_teachers
    - total_enrollments
    - avg_gpa (over all students with non-null gpa)
    """

    total_students = db.query(func.count(Student.id)).scalar() or 0
    total_courses = db.query(func.count(Course.id)).scalar() or 0
    total_teachers = db.query(func.count(Teacher.id)).scalar() or 0
    total_enrollments = db.query(func.count(Enrollment.id)).scalar() or 0

    avg_gpa = db.query(func.avg(Student.gpa)).scalar()
    avg_gpa = float(avg_gpa) if avg_gpa is not None else None

    return {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_teachers": total_teachers,
        "total_enrollments": total_enrollments,
        "avg_gpa": avg_gpa,
    }


@router.get("/course-stats")
def get_course_stats(
    db: Session = Depends(get_db_connection),
    current_user=Depends(get_current_user),
):
    """
    Per-course stats:

    - id
    - code
    - title
    - total_enrollments
    - avg_grade  (over enrollments with non-null grade)
    - pass_rate  (0..100, % of enrollments with status='passed' if status exists)
    """

    # LEFT JOIN Course <- Enrollment
    rows = (
        db.query(
            Course.id.label("id"),
            Course.code.label("code"),
            Course.title.label("title"),
            func.count(Enrollment.id).label("total_enrollments"),
            func.avg(Enrollment.grade).label("avg_grade"),
            func.sum(
                func.case(
                    (
                        (Enrollment.status == "passed"),
                        1,
                    ),
                    else_=0,
                )
            ).label("passed_count"),
        )
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .group_by(Course.id, Course.code, Course.title)
        .order_by(Course.code)
        .all()
    )

    results = []
    for row in rows:
        total_enrollments = int(row.total_enrollments or 0)
        avg_grade = float(row.avg_grade) if row.avg_grade is not None else None

        passed_count = int(row.passed_count or 0)
        if total_enrollments > 0:
            pass_rate = round((passed_count / total_enrollments) * 100, 2)
        else:
            pass_rate = None

        results.append(
            {
                "id": row.id,
                "code": row.code,
                "title": row.title,
                "total_enrollments": total_enrollments,
                "avg_grade": avg_grade,
                "pass_rate": pass_rate,  # percentage or None
            }
        )

    return results


@router.get("/department-stats")
def get_department_stats(
    db: Session = Depends(get_db_connection),
    current_user=Depends(get_current_user),
):
    """
    Per-department stats:

    - department
    - total_students
    - total_courses
    - avg_gpa
    """

    # From students: number & avg_gpa
    student_rows = (
        db.query(
            Student.department.label("department"),
            func.count(Student.id).label("total_students"),
            func.avg(Student.gpa).label("avg_gpa"),
        )
        .group_by(Student.department)
        .all()
    )

    # From courses: number of courses per department
    course_rows = (
        db.query(
            Course.department.label("department"),
            func.count(Course.id).label("total_courses"),
        )
        .group_by(Course.department)
        .all()
    )

    # Merge by department
    stats = {}

    for row in student_rows:
        dept = row.department
        if not dept:
            continue

        stats.setdefault(dept, {})
        stats[dept]["department"] = dept
        stats[dept]["total_students"] = int(row.total_students or 0)
        stats[dept]["avg_gpa"] = (
            float(row.avg_gpa) if row.avg_gpa is not None else None
        )

    for row in course_rows:
        dept = row.department
        if not dept:
            continue

        stats.setdefault(dept, {})
        stats[dept]["department"] = dept
        stats[dept]["total_courses"] = int(row.total_courses or 0)

    # fill defaults
    results = []
    for dept, info in stats.items():
        results.append(
            {
                "department": dept,
                "total_students": info.get("total_students", 0),
                "total_courses": info.get("total_courses", 0),
                "avg_gpa": info.get("avg_gpa", None),
            }
        )

    # Sort by department name for stable output
    results.sort(key=lambda x: x["department"])

    return results
