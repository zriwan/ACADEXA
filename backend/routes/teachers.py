from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db_connection
from backend.models import Teacher, Course
from backend.schemas import TeacherCreate, TeacherUpdate, TeacherResponse

# ✅ auth dependencies
from ..security import get_current_user, require_admin

router = APIRouter(prefix="/teachers", tags=["Teachers"])


# ---------------------------
# CREATE — add teacher
# ---------------------------
@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(
    payload: TeacherCreate,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),   # ✅ login required
):
    """
    Create a new teacher.
    Enforces unique email.
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
    Update a teacher.

    Uses TeacherUpdate; sirf woh fields update hongi
    jo request body me send ki gai hain (partial update).
    """
    t = db.get(Teacher, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")

    update_data = payload.model_dump(exclude_unset=True)

    # if email is being changed, keep it unique
    new_email = update_data.get("email")
    if new_email and new_email != t.email:
        exists = (
            db.query(Teacher)
            .filter(Teacher.email == new_email, Teacher.id != teacher_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Email already in use")

    # apply all other fields
    for field, value in update_data.items():
        setattr(t, field, value)

    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# ------------
# DELETE — by id
# ------------
@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db_connection),
    _=Depends(require_admin),      # ✅ admin-only
):
    """
    Delete a teacher by ID.

    Prevents delete if teacher still has assigned courses.
    """
    t = db.get(Teacher, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # prevent deleting if courses still assigned (safer than silent cascade)
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
