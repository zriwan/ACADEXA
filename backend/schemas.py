# backend/schemas.py
from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

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


# ✅ Day-2 Part-C: /auth/me response schema
class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: Literal["admin", "student", "teacher", "hod", "user"]

    student_id: int | None = None
    teacher_id: int | None = None
