# backend/schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
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
# Enrollments  (❗️missing before)
# -------------------------
class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int

class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    course_id: int
