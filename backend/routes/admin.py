# backend/routes/admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.models import User, Student, Teacher, UserRole
from backend.security import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/overview")
def admin_overview(current_user: User = Depends(require_admin)):
    """
    Minimal admin-only endpoint for RBAC verification and dashboard health check.
    """
    return {"ok": True, "message": "Admin access granted"}


# -----------------------------
# Part-F: Link Student -> User
# -----------------------------
@router.post("/link-student", status_code=status.HTTP_200_OK)
def link_student_to_user(
    student_id: int,
    user_id: int,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(require_admin),
):
    """
    Link a student record to an auth user by setting students.user_id = users.id
    Admin-only.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # (optional safety) only allow linking if user role is student
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    if role_value != UserRole.student:
        raise HTTPException(
            status_code=400,
            detail="User role must be 'student' to link a student record",
        )

    # prevent 1 user -> multiple students
    existing = db.query(Student).filter(Student.user_id == user_id).first()
    if existing and existing.id != student_id:
        raise HTTPException(
            status_code=400,
            detail="This user is already linked to another student",
        )

    student.user_id = user_id
    db.add(student)
    db.commit()
    db.refresh(student)

    return {"ok": True, "student_id": student.id, "user_id": user.id}


# -----------------------------
# (Optional) Link Teacher -> User
# Useful for Day-2/Day-3
# -----------------------------
@router.post("/link-teacher", status_code=status.HTTP_200_OK)
def link_teacher_to_user(
    teacher_id: int,
    user_id: int,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(require_admin),
):
    """
    Link a teacher record to an auth user by setting teachers.user_id = users.id
    Admin-only.
    """
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # (optional safety) only allow linking if user role is teacher
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    if role_value != UserRole.teacher:
        raise HTTPException(
            status_code=400,
            detail="User role must be 'teacher' to link a teacher record",
        )

    existing = db.query(Teacher).filter(Teacher.user_id == user_id).first()
    if existing and existing.id != teacher_id:
        raise HTTPException(
            status_code=400,
            detail="This user is already linked to another teacher",
        )

    teacher.user_id = user_id
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return {"ok": True, "teacher_id": teacher.id, "user_id": user.id}
