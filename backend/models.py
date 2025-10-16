from sqlalchemy import Column, Integer, String, Numeric
from backend.database import Base

class Student(Base):
    __tablename__ = "students"  # Must match your actual table name

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    department = Column(String(50))
    gpa = Column(Numeric(3, 2))
