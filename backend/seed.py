# backend/seed.py
"""
Seed script for ACADEXA demo (Day-7)

Creates:
- 1 Admin
- 1 HOD
- 1 Teacher
- 2 Students
- 2 Courses
- Enrollments + grades
"""

from backend.database import SessionLocal, engine
from backend.models import (
    User,
    Student,
    Teacher,
    Course,
    Enrollment,
    UserRole,
)
from backend.security import get_password_hash

def run_seed():
    db = SessionLocal()

    print("🌱 Seeding database...")

    # ---------- USERS ----------
    admin = User(
        name="Admin User",
        email="admin@acadexa.com",
        role=UserRole.admin,
        hashed_password=get_password_hash("admin123"),
    )

    hod = User(
        name="HOD User",
        email="hod@acadexa.com",
        role=UserRole.hod,
        hashed_password=get_password_hash("hod123"),
    )

    teacher_user = User(
        name="Teacher One",
        email="teacher@acadexa.com",
        role=UserRole.teacher,
        hashed_password=get_password_hash("teacher123"),
    )

    student_user1 = User(
        name="Student One",
        email="student1@acadexa.com",
        role=UserRole.student,
        hashed_password=get_password_hash("student123"),
    )

    student_user2 = User(
        name="Student Two",
        email="student2@acadexa.com",
        role=UserRole.student,
        hashed_password=get_password_hash("student123"),
    )

    db.add_all([admin, hod, teacher_user, student_user1, student_user2])
    db.commit()

    # ---------- TEACHER / STUDENTS ----------
    teacher = Teacher(
        name="Teacher One",
        department="CS",
        email="teacher@acadexa.com",
        expertise="AI",
        user_id=teacher_user.id,
    )

    student1 = Student(
        name="Student One",
        department="CS",
        user_id=student_user1.id,
        gpa=3.4,
    )

    student2 = Student(
        name="Student Two",
        department="CS",
        user_id=student_user2.id,
        gpa=3.8,
    )

    db.add_all([teacher, student1, student2])
    db.commit()

    # ---------- COURSES ----------
    course1 = Course(
        title="Artificial Intelligence",
        code="CS-401",
        credit_hours=3,
        department="CS",
        teacher_id=teacher.id,
    )

    course2 = Course(
        title="Machine Learning",
        code="CS-402",
        credit_hours=3,
        department="CS",
        teacher_id=teacher.id,
    )

    db.add_all([course1, course2])
    db.commit()

    # ---------- ENROLLMENTS ----------
    e1 = Enrollment(
        student_id=student1.id,
        course_id=course1.id,
        semester="Fall 2025",
        status="completed",
        grade=3.3,
    )

    e2 = Enrollment(
        student_id=student1.id,
        course_id=course2.id,
        semester="Fall 2025",
        status="completed",
        grade=3.5,
    )

    e3 = Enrollment(
        student_id=student2.id,
        course_id=course1.id,
        semester="Fall 2025",
        status="completed",
        grade=3.9,
    )

    db.add_all([e1, e2, e3])
    db.commit()

    print("✅ Seeding complete!")
    print("\n🔐 DEMO CREDENTIALS:")
    print("Admin   → admin@acadexa.com / admin123")
    print("HOD     → hod@acadexa.com / hod123")
    print("Teacher → teacher@acadexa.com / teacher123")
    print("Student → student1@acadexa.com / student123")
    print("Student → student2@acadexa.com / student123")

    db.close()

if __name__ == "__main__":
    run_seed()
