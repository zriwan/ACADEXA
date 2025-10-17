from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db_connection
from backend.models import Course, Teacher
from backend.schemas import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, db: Session = Depends(get_db_connection)):
    # unique code
    exists = db.query(Course).filter(Course.code == payload.code).first()
    if exists:
        raise HTTPException(status_code=400, detail="Course code already exists")

    # validate teacher if provided
    if payload.teacher_id is not None:
        if not db.get(Teacher, payload.teacher_id):
            raise HTTPException(status_code=400, detail="Teacher does not exist")

    c = Course(
        title=payload.title,
        code=payload.code,
        credit_hours=payload.credit_hours,
        teacher_id=payload.teacher_id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.get("/", response_model=list[CourseResponse])
def list_courses(db: Session = Depends(get_db_connection)):
    return db.query(Course).order_by(Course.id).all()

@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db_connection)):
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    return c

@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, payload: CourseUpdate, db: Session = Depends(get_db_connection)):
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")

    # keep code unique if changed
    if payload.code != c.code:
        exists = db.query(Course).filter(Course.code == payload.code).first()
        if exists:
            raise HTTPException(status_code=400, detail="Course code already exists")

    # validate teacher if provided
    if payload.teacher_id is not None:
        if not db.get(Teacher, payload.teacher_id):
            raise HTTPException(status_code=400, detail="Teacher does not exist")

    c.title = payload.title
    c.code = payload.code
    c.credit_hours = payload.credit_hours
    c.teacher_id = payload.teacher_id
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(get_db_connection)):
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(c)
    db.commit()
    return None
