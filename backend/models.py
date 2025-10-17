from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
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
