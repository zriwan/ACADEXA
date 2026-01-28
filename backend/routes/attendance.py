# backend/routes/attendance.py
from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.security import get_current_user
from backend.models import (
    User,
    UserRole,
    Course,
    Enrollment,
    Student,
    AttendanceSession,
    AttendanceRecord,
    AttendanceStatus,
)

from backend.schemas import (
    AttendanceSessionCreate,
    AttendanceSessionResponse,
    AttendanceBulkMark,
    AttendanceCourseSummary,
    AttendanceMySummaryResponse,
    AttendanceCourseDetailRow,
    AttendanceCourseDetailResponse,
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def _role_value(role):
    return role.value if hasattr(role, "value") else role


def _require_teacher(user: User) -> int:
    if _role_value(user.role) != UserRole.teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")
    if not user.teacher:
        raise HTTPException(status_code=404, detail="Teacher record not linked")
    return user.teacher.id


def _require_student(user: User) -> int:
    if _role_value(user.role) != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")
    if not user.student:
        raise HTTPException(status_code=404, detail="Student record not linked")
    return user.student.id


def _teacher_course_or_404(db: Session, teacher_id: int, course_id: int) -> Course:
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    if c.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Not allowed for this course")
    return c


# -------------------------
# Teacher: list my enrollments in a course
# -------------------------
@router.get("/teacher/course/{course_id}/enrollments")
def teacher_course_enrollments(
    course_id: int,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    teacher_id = _require_teacher(current_user)
    _teacher_course_or_404(db, teacher_id, course_id)

    rows = (
        db.query(Enrollment, Student)
        .join(Student, Student.id == Enrollment.student_id)
        .filter(Enrollment.course_id == course_id)
        .order_by(Enrollment.id)
        .all()
    )

    return [
        {
            "enrollment_id": e.id,
            "student_id": s.id,
            "student_name": s.name,
            "department": s.department,
        }
        for e, s in rows
    ]


# -------------------------
# Teacher: create a lecture/session
# -------------------------
@router.post("/teacher/course/{course_id}/sessions", response_model=AttendanceSessionResponse, status_code=status.HTTP_201_CREATED)
def teacher_create_session(
    course_id: int,
    payload: AttendanceSessionCreate,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    teacher_id = _require_teacher(current_user)
    _teacher_course_or_404(db, teacher_id, course_id)

    if payload.course_id != course_id:
        raise HTTPException(status_code=400, detail="course_id mismatch")

    ses = AttendanceSession(
        course_id=course_id,
        lecture_date=payload.lecture_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        created_by_user_id=current_user.id,
    )
    db.add(ses)
    db.commit()
    db.refresh(ses)
    return ses


# -------------------------
# Teacher: list sessions for a course
# -------------------------
@router.get("/teacher/course/{course_id}/sessions", response_model=list[AttendanceSessionResponse])
def teacher_list_sessions(
    course_id: int,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    teacher_id = _require_teacher(current_user)
    _teacher_course_or_404(db, teacher_id, course_id)

    sessions = (
        db.query(AttendanceSession)
        .filter(AttendanceSession.course_id == course_id)
        .order_by(AttendanceSession.lecture_date.desc(), AttendanceSession.id.desc())
        .all()
    )
    return sessions


# -------------------------
# Teacher: bulk mark attendance for a session
# -------------------------
@router.post("/teacher/session/{session_id}/mark/bulk")
def teacher_bulk_mark(
    session_id: int,
    payload: AttendanceBulkMark,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    teacher_id = _require_teacher(current_user)

    ses = db.get(AttendanceSession, session_id)
    if not ses:
        raise HTTPException(status_code=404, detail="Session not found")

    # permission
    _teacher_course_or_404(db, teacher_id, ses.course_id)

    # valid enrollment ids for this course
    enroll_ids = {
        r[0] for r in db.query(Enrollment.id).filter(Enrollment.course_id == ses.course_id).all()
    }

    updated = 0
    created = 0

    for rec in payload.records:
        if rec.enrollment_id not in enroll_ids:
            continue

        row = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.enrollment_id == rec.enrollment_id,
            )
            .first()
        )

        if row:
            row.status = AttendanceStatus(rec.status)
            row.marked_by_user_id = current_user.id
            updated += 1
        else:
            row = AttendanceRecord(
                session_id=session_id,
                enrollment_id=rec.enrollment_id,
                status=AttendanceStatus(rec.status),
                marked_by_user_id=current_user.id,
            )
            db.add(row)
            created += 1

    db.commit()
    return {"ok": True, "updated": updated, "created": created}


# -------------------------
# Student: summary (all courses)
# -------------------------
@router.get("/my", response_model=AttendanceMySummaryResponse)
def student_my_attendance_summary(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    student_id = _require_student(current_user)

    # enrollments for student
    enrolls = (
        db.query(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Enrollment.student_id == student_id)
        .order_by(Course.id)
        .all()
    )

    out: list[AttendanceCourseSummary] = []

    for en, co in enrolls:
        total_sessions = db.query(AttendanceSession).filter(AttendanceSession.course_id == co.id).count()

        # records for this enrollment
        recs = db.query(AttendanceRecord).join(AttendanceSession, AttendanceSession.id == AttendanceRecord.session_id)\
            .filter(AttendanceRecord.enrollment_id == en.id, AttendanceSession.course_id == co.id)\
            .all()

        present = sum(1 for r in recs if (r.status.value if hasattr(r.status, "value") else str(r.status)) == "present")
        absent = sum(1 for r in recs if (r.status.value if hasattr(r.status, "value") else str(r.status)) == "absent")
        late = sum(1 for r in recs if (r.status.value if hasattr(r.status, "value") else str(r.status)) == "late")

        # sessions without record => absent (optional). We'll count them as absent in view:
        missing = max(total_sessions - len(recs), 0)
        absent_total = absent + missing

        percent = (present / total_sessions) * 100 if total_sessions > 0 else 0.0

        out.append(
            AttendanceCourseSummary(
                course_id=co.id,
                course_code=co.code,
                course_title=co.title,
                total_sessions=total_sessions,
                present=present,
                absent=absent_total,
                late=late,
                percent_present=percent,
            )
        )

    return AttendanceMySummaryResponse(student_id=student_id, courses=out)


# -------------------------
# Student: detail for one course
# -------------------------
@router.get("/my/course/{course_id}", response_model=AttendanceCourseDetailResponse)
def student_my_attendance_course(
    course_id: int,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    student_id = _require_student(current_user)

    # enrollment for this course
    en = db.query(Enrollment).filter(Enrollment.student_id == student_id, Enrollment.course_id == course_id).first()
    if not en:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")

    co = db.get(Course, course_id)
    if not co:
        raise HTTPException(status_code=404, detail="Course not found")

    sessions = (
        db.query(AttendanceSession)
        .filter(AttendanceSession.course_id == course_id)
        .order_by(AttendanceSession.lecture_date.desc(), AttendanceSession.id.desc())
        .all()
    )

    # map session_id -> status for this enrollment
    recs = db.query(AttendanceRecord).filter(AttendanceRecord.enrollment_id == en.id).all()
    m = {r.session_id: (r.status.value if hasattr(r.status, "value") else str(r.status)) for r in recs}

    rows: list[AttendanceCourseDetailRow] = []
    for s in sessions:
        rows.append(
            AttendanceCourseDetailRow(
                session_id=s.id,
                lecture_date=s.lecture_date,
                start_time=s.start_time,
                end_time=s.end_time,
                status=m.get(s.id, "absent"),  # missing => absent
            )
        )

    return AttendanceCourseDetailResponse(
        student_id=student_id,
        course_id=co.id,
        course_code=co.code,
        course_title=co.title,
        rows=rows,
    )
