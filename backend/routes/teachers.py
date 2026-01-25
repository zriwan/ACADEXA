from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from pydantic import BaseModel, EmailStr
import secrets

from backend.database import get_db_connection
from backend.models import Teacher, Course, Enrollment, Student, User, UserRole
from backend.schemas import TeacherCreate, TeacherUpdate, TeacherResponse

# ✅ auth dependencies
from ..security import get_current_user, require_admin, hash_password

router = APIRouter(prefix="/teachers", tags=["Teachers"])


# =============================
# ✅ NEW: Admin creates teacher account (User + Teacher) with temp password
# =============================
class TeacherAccountCreate(BaseModel):
    name: str
    department: str
    email: EmailStr
    expertise: str | None = None
    password: str | None = None  # optional: admin can set, else auto-generate


class TeacherAccountCreated(BaseModel):
    teacher_id: int
    user_id: int
    email: EmailStr
    temp_password: str


@router.post("/create-account", response_model=TeacherAccountCreated, status_code=status.HTTP_201_CREATED)
def create_teacher_account(
    payload: TeacherAccountCreate,
    db: Session = Depends(get_db_connection),
    _admin: User = Depends(require_admin),  # ✅ admin-only
):
    """
    Admin creates teacher login account + teacher profile.
    Returns temp_password (only once) so admin can give it to teacher.
    """

    # 1) email unique in users
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # 2) email unique in teachers
    existing_teacher = db.query(Teacher).filter(Teacher.email == payload.email).first()
    if existing_teacher:
        raise HTTPException(status_code=400, detail="Teacher with this email already exists")

    # 3) temp password
    temp_password = payload.password or secrets.token_urlsafe(10)

    # 4) create user (login)
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(temp_password),
        role=UserRole.teacher,
    )
    db.add(user)
    db.flush()  # get user.id without commit

    # 5) create teacher profile linked to user
    teacher = Teacher(
        name=payload.name,
        department=payload.department,
        email=payload.email,
        expertise=payload.expertise,
        user_id=user.id,
    )
    db.add(teacher)

    db.commit()
    db.refresh(teacher)

    return TeacherAccountCreated(
        teacher_id=teacher.id,
        user_id=user.id,
        email=user.email,
        temp_password=temp_password,
    )


# -----------------------------
# /teachers/me → current teacher profile
# IMPORTANT: keep this ABOVE "/{teacher_id}" route
# -----------------------------
@router.get("/me", response_model=TeacherResponse)
def get_my_teacher_profile(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value != UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required")

    if not current_user.teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher record not linked")

    return current_user.teacher


# -----------------------------
# /teachers/me/courses
# -----------------------------
@router.get("/me/courses")
def get_my_courses_as_teacher(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value != UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required")

    if not current_user.teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher record not linked")

    teacher_id = current_user.teacher.id

    courses = (
        db.query(Course)
        .filter(Course.teacher_id == teacher_id)
        .order_by(Course.id)
        .all()
    )

    return {
        "teacher_id": teacher_id,
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "code": c.code,
                "credit_hours": c.credit_hours,
            }
            for c in courses
        ],
    }


# -----------------------------
# /teachers/me/enrollments
# teacher ki courses ke students/enrollments list
# -----------------------------
@router.get("/me/enrollments")
def get_my_enrollments_as_teacher(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    if role_value != UserRole.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher access required")

    if not current_user.teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher record not linked")

    teacher_id = current_user.teacher.id

    rows = (
        db.query(Enrollment, Course, Student)
        .join(Course, Course.id == Enrollment.course_id)
        .join(Student, Student.id == Enrollment.student_id)
        .filter(Course.teacher_id == teacher_id)
        .order_by(Enrollment.id)
        .all()
    )

    results = []
    for en, co, st in rows:
        results.append(
            {
                "enrollment_id": en.id,
                "course_id": co.id,
                "course_code": co.code,
                "course_title": co.title,
                "student_id": st.id,
                "student_name": st.name,
                "semester": en.semester,
                "status": en.status,
                "grade": float(en.grade) if en.grade is not None else None,
            }
        )

    return {"teacher_id": teacher_id, "enrollments": results}


# ---------------------------
# CREATE — add teacher (admin-only)
# ---------------------------
@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(
    payload: TeacherCreate,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),   # ✅ admin-only
):
    """
    Create a new teacher profile (NO LOGIN ACCOUNT).
    Prefer using /teachers/create-account for teacher login account.
    """
    exists = db.query(Teacher).filter(Teacher.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already in use")

    t = Teacher(
        name=payload.name,
        department=payload.department,
        email=payload.email,
        expertise=payload.expertise,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# --------------
# READ — list all
# --------------
@router.get("/", response_model=list[TeacherResponse])
def list_teachers(
    department: Optional[str] = None,
    email_contains: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
):
    """
    List teachers with optional filters + pagination.
    """
    q = db.query(Teacher)
    if department:
        q = q.filter(Teacher.department == department)
    if email_contains:
        q = q.filter(Teacher.email.ilike(f"%{email_contains}%"))

    return q.order_by(Teacher.id).offset(skip).limit(limit).all()


# ----------------
# READ — single by id
# ----------------
@router.get("/{teacher_id}", response_model=TeacherResponse)
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db_connection),
):
    """
    Get a single teacher by ID.
    """
    t = db.get(Teacher, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return t


# -----------
# UPDATE — PUT
# -----------
@router.put("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: int,
    payload: TeacherUpdate,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),   # ✅ login required
):
    """
    Update a teacher (partial update).
    """
    t = db.get(Teacher, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")

    update_data = payload.model_dump(exclude_unset=True)

    new_email = update_data.get("email")
    if new_email and new_email != t.email:
        exists = (
            db.query(Teacher)
            .filter(Teacher.email == new_email, Teacher.id != teacher_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Email already in use")

    for field, value in update_data.items():
        setattr(t, field, value)

    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# ------------
# DELETE — by id (admin-only)
# ------------
@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),      # ✅ admin-only
):
    """
    Delete a teacher by ID.
    Prevent delete if teacher still has assigned courses.
    """
    t = db.get(Teacher, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")

    has_courses = (
        db.query(Course)
        .filter(Course.teacher_id == teacher_id)
        .count() > 0
    )
    if has_courses:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete: teacher has assigned courses",
        )

    db.delete(t)
    db.commit()
    return None
