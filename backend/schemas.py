# backend/schemas.py
from __future__ import annotations  # ✅ handles forward refs in Pydantic v2

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, Literal
from decimal import Decimal

# -------------------------
# Students
# -------------------------
class StudentCreate(BaseModel):
    name: str
    department: str
    gpa: Decimal

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
    expertise: Optional[str] = None

class TeacherUpdate(BaseModel):
    name: str
    department: str
    email: EmailStr
    expertise: Optional[str] = None

class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    department: str
    email: EmailStr
    expertise: Optional[str] = None

# -------------------------
# Courses
# -------------------------
class CourseCreate(BaseModel):
    title: str
    code: str
    credit_hours: int
    teacher_id: Optional[int] = None

class CourseUpdate(BaseModel):
    title: str
    code: str
    credit_hours: int
    teacher_id: Optional[int] = None

class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    code: str
    credit_hours: int
    teacher_id: Optional[int] = None

# -------------------------
# Enrollments (single, extended versions only)
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
    semester: Optional[str] = Field(default=None, max_length=20)

class EnrollmentUpdate(BaseModel):
    semester: Optional[str] = Field(default=None, max_length=20)
    status:   Optional[str] = Field(default=None)   # "enrolled" | "dropped" | "completed"
    grade:    Optional[float] = Field(default=None, ge=0, le=4)  # 0.00..4.00

class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    course_id: int
    semester: Optional[str] = None
    status:   Optional[str] = None
    grade:    Optional[float] = None

class EnrollmentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    semester: Optional[str] = None
    status:   Optional[str] = None
    grade:    Optional[float] = None
    student: StudentBrief
    course:  CourseBrief

# ======================
# AUTH SCHEMAS (Day 8)
# ======================
class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role: Literal["admin", "user"] = "user"

class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
