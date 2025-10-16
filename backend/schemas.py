# backend/schemas.py
from pydantic import BaseModel, ConfigDict
from decimal import Decimal

class StudentCreate(BaseModel):
    name: str
    department: str
    # either Decimal or float works; Decimal matches NUMERIC(3,2)
    gpa: Decimal

class StudentUpdate(BaseModel):
    name: str
    department: str
    gpa: Decimal

class StudentResponse(BaseModel):
    # this replaces orm_mode=True in pydantic v1
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    department: str
    gpa: Decimal
