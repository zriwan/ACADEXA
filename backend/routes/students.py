from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.models import Student
from backend.schemas import (
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)

from ..security import get_current_user, require_admin  # ✅ auth guards

router = APIRouter(prefix="/students", tags=["Students"])


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
    # Agar future me StudentCreate me extra fields aajayen,
    # to yeh approach automatically map kar dega:
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
    student = db.get(Student, student_id)  # SQLAlchemy 1.4/2.0 style

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
    - Agar StudentUpdate me fields OPTIONAL hon,
      to sirf wahi fields update hongi jo request me aayi hain.
    """
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    # ✅ Partial update using Pydantic v2 style
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
    # 204 No Content → koi body return nahi hoti
    return None
