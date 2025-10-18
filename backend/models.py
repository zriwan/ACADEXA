
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, String, Numeric, DateTime, func
from sqlalchemy.orm import relationship
from backend.database import Base



# --- existing ---
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    department = Column(String(50))
    gpa = Column(Numeric(3, 2))

# --- new: Teacher ---
class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    department = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    expertise = Column(String(100), nullable=True)

    # relation: one teacher -> many courses
    courses = relationship("Course", back_populates="teacher", cascade="all, delete-orphan")

# --- new: Course ---
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    credit_hours = Column(Integer, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)

    # relation: many courses -> one teacher
    teacher = relationship("Teacher", back_populates="courses")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_id  = Column(Integer, ForeignKey("courses.id",  ondelete="CASCADE"), nullable=False)

    # NEW fields
    semester   = Column(String(20), nullable=True)                      # e.g., "Fall 2025"
    status     = Column(String(20), nullable=True, default="enrolled")  # enrolled|dropped|completed
    grade      = Column(Numeric(3, 2), nullable=True)                   # e.g., 3.50

    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    student = relationship("Student")
    course  = relationship("Course")