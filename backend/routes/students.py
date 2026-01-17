from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.models import Student, User, UserRole, Enrollment

from backend.database import get_db_connection
from backend.models import Student, User, UserRole
from backend.schemas import (
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)

from ..security import get_current_user, require_admin  # ✅ auth guards

router = APIRouter(prefix="/students", tags=["Students"])


# -----------------------------
# /students/me → current student's profile (Day-2 Part-E)
# IMPORTANT: keep this ABOVE "/{student_id}" route
# -----------------------------
@router.get("/me", response_model=StudentResponse)
def get_my_student_profile(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    # ✅ Only students can access
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )

    # ✅ Must be linked to a Student row (students.user_id = users.id)
    if not current_user.student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record not linked to this user",
        )

    return current_user.student


# ---------------------------
# CREATE
# ---------------------------
@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def add_student(
    payload: StudentCreate,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),  # ✅ login required
):
    """
    Create a new student.
    Uses StudentCreate schema (name, department, gpa, etc.).
    """
    data = payload.model_dump()
    s = Student(**data)

    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# --------------
# READ — list all (with filters + pagination)
# --------------
@router.get("/", response_model=list[StudentResponse])
def list_students(
    department: str | None = None,
    name_contains: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
):
    """
    List students with optional filters.

    Query params:
    - department: exact match filter
    - name_contains: case-insensitive search on name
    - skip: pagination offset
    - limit: pagination page size
    """
    q = db.query(Student)

    if department:
        q = q.filter(Student.department == department)

    if name_contains:
        q = q.filter(Student.name.ilike(f"%{name_contains}%"))

    return q.order_by(Student.id).offset(skip).limit(limit).all()


# ----------------
# READ — single by id
# ----------------
@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db_connection),
):
    """
    Get single student by numeric ID.
    """
    student = db.get(Student, student_id)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


# -----------
# UPDATE — PUT
# -----------
@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),  # ✅ login required
):
    """
    Update existing student.
    Uses StudentUpdate schema.
    - partial update: only fields provided will be updated.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    db.add(student)
    db.commit()
    db.refresh(student)
    return student


# ------------
# DELETE — by id
# ------------
@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),  # ✅ admin-only
):
    """
    Delete a student by ID.
    Admin-only operation.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    db.delete(student)
    db.commit()
    return None


# -----------------------------
# /students/me/gpa
# -----------------------------
@router.get("/me/gpa")
def get_my_gpa(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    # role check
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")

    if not current_user.student:
        raise HTTPException(status_code=404, detail="Student record not linked")

    return {
        "student_id": current_user.student.id,
        "gpa": float(current_user.student.gpa) if current_user.student.gpa is not None else None,
    }

# -----------------------------
# /students/me/courses
# -----------------------------
@router.get("/me/courses")
def get_my_courses(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")

    if not current_user.student:
        raise HTTPException(status_code=404, detail="Student record not linked")

    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == current_user.student.id)
        .all()
    )

    courses = []
    for e in enrollments:
        if e.course:
            courses.append({
                "course_id": e.course.id,
                "title": e.course.title,
                "code": e.course.code,
                "credit_hours": e.course.credit_hours,
            })

    return {
        "student_id": current_user.student.id,
        "courses": courses,
    }
# -----------------------------
# /students/me/enrollments
# -----------------------------
@router.get("/me/enrollments")
def get_my_enrollments(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")

    if not current_user.student:
        raise HTTPException(status_code=404, detail="Student record not linked")

    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == current_user.student.id)
        .all()
    )

    return enrollments
