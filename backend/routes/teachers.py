from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.models import Course, Teacher
from backend.schemas import TeacherCreate, TeacherResponse, TeacherUpdate

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db_connection)):
    # enforce unique email
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


@router.get("/", response_model=list[TeacherResponse])
def list_teachers(
    department: str | None = None,
    email_contains: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_connection),
):
    q = db.query(Teacher)
    if department:
        q = q.filter(Teacher.department == department)
    if email_contains:
        q = q.filter(Teacher.email.ilike(f"%{email_contains}%"))
    return q.order_by(Teacher.id).offset(skip).limit(limit).all()


@router.get("/{teacher_id}", response_model=TeacherResponse)
def get_teacher(teacher_id: int, db: Session = Depends(get_db_connection)):
    t = db.get(Teacher, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return t


@router.put("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: int, payload: TeacherUpdate, db: Session = Depends(get_db_connection)
):
    t = db.get(Teacher, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # if email changed, keep it unique
    if payload.email != t.email:
        exists = db.query(Teacher).filter(Teacher.email == payload.email).first()
        if exists:
            raise HTTPException(status_code=400, detail="Email already in use")

    t.name = payload.name
    t.department = payload.department
    t.email = payload.email
    t.expertise = payload.expertise
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(teacher_id: int, db: Session = Depends(get_db_connection)):
    t = db.get(Teacher, teacher_id)
    if not t:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # prevent deleting if courses still assigned (safer than silent cascade)
    has_courses = db.query(Course).filter(Course.teacher_id == teacher_id).count() > 0
    if has_courses:
        raise HTTPException(
            status_code=400, detail="Cannot delete: teacher has assigned courses"
        )

    db.delete(t)
    db.commit()
    return None
