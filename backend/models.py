# backend/models.py
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from backend.database import Base


# --- Student ---
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    department = Column(String(50), index=True)
    gpa = Column(Numeric(3, 2))


# --- Teacher ---
class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    department = Column(String(50), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    expertise = Column(String(100), nullable=True)

    # one teacher -> many courses (ORM-level cascade)
    courses = relationship(
        "Course", back_populates="teacher", cascade="all, delete-orphan"
    )


# --- Course ---
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    credit_hours = Column(Integer, nullable=False)

    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    teacher = relationship("Teacher")



# --- Enrollment ---
class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    semester = Column(String(20), nullable=True)  # e.g., "Fall 2025"
    status = Column(
        String(20), nullable=True, default="enrolled"
    )  # enrolled|dropped|completed
    grade = Column(Numeric(3, 2), nullable=True)  # e.g., 3.50

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )

    student = relationship("Student")
    course = relationship("Course")


# ===== Auth models =====
class UserRole(str, Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.user
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# Optional extra composite indexes
Index("ix_enrollments_student", Enrollment.student_id)
Index("ix_enrollments_course", Enrollment.course_id)
