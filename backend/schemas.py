# backend/schemas.py
from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# -------------------------
# Students
# -------------------------
class StudentCreate(BaseModel):
    name: str
    department: str
    gpa: Decimal

    # ✅ NEW: create login account for student
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class StudentUpdate(BaseModel):
    name: str
    department: str
    gpa: Decimal


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    department: str
    gpa: Decimal


# -------------------------
# Teachers
# -------------------------
class TeacherCreate(BaseModel):
    name: str
    department: str
    email: EmailStr
    expertise: str | None = None


class TeacherUpdate(BaseModel):
    name: str
    department: str
    email: EmailStr
    expertise: str | None = None


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    department: str
    email: EmailStr
    expertise: str | None = None


# -------------------------
# Courses
# -------------------------
class CourseCreate(BaseModel):
    title: str
    code: str
    credit_hours: int
    teacher_id: Optional[int] = None


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    code: Optional[str] = None
    credit_hours: Optional[int] = None
    teacher_id: Optional[int] = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    code: str
    credit_hours: int
    teacher_id: int | None = None


# -------------------------
# Enrollments
# -------------------------
class StudentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    department: str
    gpa: Decimal


class CourseBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    code: str
    credit_hours: int
    teacher_id: int | None = None


class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    semester: str | None = Field(default=None, max_length=20)


class EnrollmentUpdate(BaseModel):
    semester: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None)  # enrolled|dropped|completed
    grade: float | None = Field(default=None, ge=0, le=4)  # 0.00..4.00


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    semester: str | None = None
    status: str | None = None
    grade: float | None = None


class EnrollmentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    semester: str | None = None
    status: str | None = None
    grade: float | None = None
    student: StudentBrief
    course: CourseBrief


# ======================
# AUTH SCHEMAS
# ======================
class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role: Literal["admin", "student", "teacher", "hod", "user"] = "student"


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int | None = None
    teacher_id: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: Literal["admin", "student", "teacher", "hod", "user"]
    student_id: int | None = None
    teacher_id: int | None = None


# -------------------------
# Assessments (Items + Scores)
# -------------------------
class AssessmentItemCreate(BaseModel):
    course_id: int
    title: str = Field(min_length=1, max_length=120)
    category: Literal["quiz", "assignment", "mid", "final"]
    max_marks: float = Field(ge=0)
    due_date: datetime | None = None


class AssessmentItemUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    max_marks: float | None = Field(default=None, ge=0)
    due_date: datetime | None = None


class AssessmentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    category: Literal["quiz", "assignment", "mid", "final"]
    max_marks: float
    due_date: datetime | None = None


class ScoreUpsert(BaseModel):
    assessment_item_id: int
    enrollment_id: int
    obtained_marks: float = Field(ge=0)


class AssessmentScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_item_id: int
    enrollment_id: int
    obtained_marks: float


class CourseGradeSummary(BaseModel):
    course_id: int
    course_code: str | None = None
    course_title: str | None = None

    internal_percent: float
    mid_percent: float
    final_percent: float
    total_out_of_100: float


class CourseGradeDetailItem(BaseModel):
    item_id: int
    title: str
    category: Literal["quiz", "assignment", "mid", "final"]
    max_marks: float
    obtained_marks: float | None = None
    due_date: datetime | None = None


class CourseGradeDetail(BaseModel):
    course_id: int
    course_code: str | None = None
    course_title: str | None = None

    items: list[CourseGradeDetailItem]

    internal_percent: float
    mid_percent: float
    final_percent: float
    total_out_of_100: float


# -------------------------
# Fees
# -------------------------
class FeeAccountSet(BaseModel):
    student_id: int
    total_fee: float = Field(ge=0)


class FeeTxnCreate(BaseModel):
    student_id: int
    txn_type: Literal["payment", "fine", "scholarship", "adjustment"]
    amount: float
    note: str | None = Field(default=None, max_length=255)


class FeeTxnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    txn_type: Literal["payment", "fine", "scholarship", "adjustment"]
    amount: float
    note: str | None = None
    created_at: datetime


class FeeMyResponse(BaseModel):
    student_id: int
    total_fee: float
    paid: float
    pending: float
    transactions: list[FeeTxnResponse]


# -------------------------
# ✅ Attendance
# -------------------------
class AttendanceSessionCreate(BaseModel):
    course_id: int
    lecture_date: date  # ✅ FIXED
    start_time: str | None = Field(default=None, max_length=10)  # "09:00"
    end_time: str | None = Field(default=None, max_length=10)    # "10:30"


class AttendanceSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    lecture_date: date  # ✅ FIXED
    start_time: str | None = None
    end_time: str | None = None
    created_at: datetime


class AttendanceMarkItem(BaseModel):
    enrollment_id: int
    status: Literal["present", "absent", "late"]


class AttendanceBulkMark(BaseModel):
    records: list[AttendanceMarkItem]


class AttendanceCourseSummary(BaseModel):
    course_id: int
    course_code: str | None = None
    course_title: str | None = None

    total_sessions: int
    present: int
    absent: int
    late: int
    percent_present: float


class AttendanceMySummaryResponse(BaseModel):
    student_id: int
    courses: list[AttendanceCourseSummary]


class AttendanceCourseDetailRow(BaseModel):
    session_id: int
    lecture_date: date
    start_time: str | None = None
    end_time: str | None = None
    status: Literal["present", "absent", "late"]


class AttendanceCourseDetailResponse(BaseModel):
    student_id: int
    course_id: int
    course_code: str | None = None
    course_title: str | None = None
    rows: list[AttendanceCourseDetailRow]
