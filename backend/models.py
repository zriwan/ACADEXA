# backend/models.py
from __future__ import annotations

from datetime import datetime, date
import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Float,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SAEnum

from backend.database import Base


# ------------------------
# Core Models
# ------------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    department = Column(String(50), index=True)
    gpa = Column(Numeric(3, 2))

    # Link Student -> User (auth)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    user = relationship("User", back_populates="student", uselist=False)


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    department = Column(String(50), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    expertise = Column(String(100), nullable=True)

    courses = relationship("Course", back_populates="teacher", cascade="all, delete-orphan")

    # Link Teacher -> User (auth)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    user = relationship("User", back_populates="teacher", uselist=False)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    credit_hours = Column(Integer, nullable=False)

    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    teacher = relationship("Teacher", back_populates="courses")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    semester = Column(String(20), nullable=True)
    status = Column(String(20), nullable=True, default="enrolled")
    grade = Column(Numeric(3, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    student = relationship("Student")
    course = relationship("Course")


# ------------------------
# Auth Models
# ------------------------
class UserRole(str, enum.Enum):
    admin = "admin"
    student = "student"
    teacher = "teacher"
    hod = "hod"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.student)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student = relationship("Student", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)


Index("ix_enrollments_student", Enrollment.student_id)
Index("ix_enrollments_course", Enrollment.course_id)


# ------------------------
# Assessments + Fees Enums
# ------------------------
class AssessmentCategory(str, enum.Enum):
    quiz = "quiz"
    assignment = "assignment"
    mid = "mid"
    final = "final"


class FeeTxnType(str, enum.Enum):
    payment = "payment"
    fine = "fine"
    scholarship = "scholarship"
    adjustment = "adjustment"


# ------------------------
# Assessments
# ------------------------
class AssessmentItem(Base):
    __tablename__ = "assessment_items"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(120), nullable=False)
    category = Column(SAEnum(AssessmentCategory, name="assessment_category"), nullable=False, index=True)
    max_marks = Column(Float, nullable=False, default=0)

    due_date = Column(DateTime, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    course = relationship("Course", backref="assessment_items")
    scores = relationship("AssessmentScore", back_populates="item", cascade="all, delete-orphan")


class AssessmentScore(Base):
    __tablename__ = "assessment_scores"

    id = Column(Integer, primary_key=True, index=True)

    assessment_item_id = Column(Integer, ForeignKey("assessment_items.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)

    obtained_marks = Column(Float, nullable=False, default=0)
    graded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    item = relationship("AssessmentItem", back_populates="scores")
    enrollment = relationship("Enrollment", backref="assessment_scores")

    __table_args__ = (
        UniqueConstraint("assessment_item_id", "enrollment_id", name="uq_assessment_scores_item_enrollment"),
    )


# ------------------------
# Fees
# ------------------------
class FeeAccount(Base):
    __tablename__ = "fee_accounts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    total_fee = Column(Numeric(12, 2), nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student = relationship("Student", backref="fee_account")


class FeeTransaction(Base):
    __tablename__ = "fee_transactions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    amount = Column(Numeric(12, 2), nullable=False, default=0)
    txn_type = Column(SAEnum(FeeTxnType, name="fee_txn_type"), nullable=False, index=True)
    note = Column(String(255), nullable=True)

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("Student", backref="fee_transactions")


# ------------------------
# ✅ Attendance
# ------------------------
class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"


class AttendanceSession(Base):
    """
    One lecture/session for a course. Teacher creates it with date + time.
    """
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lecture_date = Column(Date, nullable=False, index=True)

    # keep simple (UI friendly)
    start_time = Column(String(10), nullable=True)  # "09:00"
    end_time = Column(String(10), nullable=True)    # "10:30"

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    course = relationship("Course", backref="attendance_sessions")
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")


class AttendanceRecord(Base):
    """
    One student attendance for one session.
    """
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(SAEnum(AttendanceStatus, name="attendance_status"), nullable=False, default=AttendanceStatus.absent)

    marked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    marked_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    session = relationship("AttendanceSession", back_populates="records")
    enrollment = relationship("Enrollment", backref="attendance_records")

    __table_args__ = (
        UniqueConstraint("session_id", "enrollment_id", name="uq_attendance_session_enrollment"),
    )


Index("ix_attendance_sessions_course", AttendanceSession.course_id)
Index("ix_attendance_records_session", AttendanceRecord.session_id)
Index("ix_attendance_records_enrollment", AttendanceRecord.enrollment_id)
