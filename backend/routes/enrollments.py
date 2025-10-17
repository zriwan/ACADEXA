from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db_connection
from backend.models import Enrollment, Student, Course
from backend.schemas import EnrollmentCreate, EnrollmentResponse

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])

@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"description": "Student/Course not found or already enrolled"}}
)
def enroll(payload: EnrollmentCreate, db: Session = Depends(get_db_connection)):
    # Validate foreign keys exist
    if not db.get(Student, payload.student_id):
        raise HTTPException(status_code=400, detail="Student does not exist")
    if not db.get(Course, payload.course_id):
        raise HTTPException(status_code=400, detail="Course does not exist")

    e = Enrollment(student_id=payload.student_id, course_id=payload.course_id)
    db.add(e)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # hits when (student_id, course_id) already exists due to unique constraint
        raise HTTPException(status_code=400, detail="Student already enrolled in this course")
    db.refresh(e)
    return e

@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll(enrollment_id: int, db: Session = Depends(get_db_connection)):
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    db.delete(e)
    db.commit()
    return None

@router.get("/student/{student_id}", response_model=list[EnrollmentResponse])
def list_student_enrollments(student_id: int, db: Session = Depends(get_db_connection)):
    # Optional: return 404 if student not found; for now, empty list if student has no enrollments
    return db.query(Enrollment).filter(Enrollment.student_id == student_id).all()

@router.get("/course/{course_id}", response_model=list[EnrollmentResponse])
def list_course_enrollments(course_id: int, db: Session = Depends(get_db_connection)):
    return db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
