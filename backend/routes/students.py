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
# CREATE (Day 2 se continued)
# ---------------------------
@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def add_student(
    payload: StudentCreate,
    db: Session = Depends(get_db_connection),
    _=Depends(get_current_user),  # ✅ login required
):
    s = Student(name=payload.name, department=payload.department, gpa=payload.gpa)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# --------------
# READ — list all
# --------------
@router.get("/", response_model=list[StudentResponse])
def list_students(
    department: str | None = None,
    name_contains: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
):
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
def get_student(student_id: int, db: Session = Depends(get_db_connection)):
    student = db.get(Student, student_id)  # SQLAlchemy 1.4/2.0 style
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
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
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    student.name = payload.name
    student.department = payload.department
    student.gpa = payload.gpa

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
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    db.delete(student)
    db.commit()
    # 204 No Content → koi body return nahi hoti
    return None
