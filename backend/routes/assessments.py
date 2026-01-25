# backend/routes/assessments.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.security import get_current_user
from backend.models import (
    User,
    UserRole,
    Course,
    Enrollment,
    AssessmentItem,
    AssessmentScore,
    AssessmentCategory,
)
from backend.schemas import AssessmentItemCreate, AssessmentItemResponse, ScoreUpsert

router = APIRouter(prefix="/assessments", tags=["Assessments"])


def _role_value(role):
    return role.value if hasattr(role, "value") else role


def _require_teacher(user: User) -> int:
    if _role_value(user.role) != UserRole.teacher:
        raise HTTPException(status_code=403, detail="Teacher access required")
    if not user.teacher:
        raise HTTPException(status_code=404, detail="Teacher record not linked")
    return user.teacher.id


def _teacher_course_or_404(db: Session, teacher_id: int, course_id: int) -> Course:
    c = db.get(Course, course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    if c.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Not allowed for this course")
    return c


# -------------------------
# Teacher: Items
# -------------------------
@router.get("/teacher/course/{course_id}/items", response_model=list[AssessmentItemResponse])
def teacher_list_items(
    course_id: int,
    category: str | None = Query(default=None),  # ✅ NEW: filter by category
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    teacher_id = _require_teacher(current_user)
    _teacher_course_or_404(db, teacher_id, course_id)

    q = db.query(AssessmentItem).filter(AssessmentItem.course_id == course_id)

    # ✅ filter by category if provided
    if category:
        try:
            q = q.filter(AssessmentItem.category == AssessmentCategory(category))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid category (quiz/assignment/mid/final)")

    items = q.order_by(AssessmentItem.id).all()
    return items


@router.post(
    "/teacher/course/{course_id}/items",
    response_model=AssessmentItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def teacher_create_item(
    course_id: int,
    payload: AssessmentItemCreate,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    teacher_id = _require_teacher(current_user)
    _teacher_course_or_404(db, teacher_id, course_id)

    if payload.course_id != course_id:
        raise HTTPException(status_code=400, detail="course_id mismatch")

    item = AssessmentItem(
        course_id=course_id,
        title=payload.title.strip(),
        category=AssessmentCategory(payload.category),
        max_marks=float(payload.max_marks),
        due_date=payload.due_date,
        created_by_user_id=current_user.id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# -------------------------
# Teacher: Scores
# (returns only existing rows; frontend treats missing as 0)
# -------------------------
@router.get("/teacher/course/{course_id}/scores")
def teacher_list_scores(
    course_id: int,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    teacher_id = _require_teacher(current_user)
    _teacher_course_or_404(db, teacher_id, course_id)

    rows = (
        db.query(AssessmentScore)
        .join(Enrollment, Enrollment.id == AssessmentScore.enrollment_id)
        .filter(Enrollment.course_id == course_id)
        .order_by(AssessmentScore.id)
        .all()
    )

    return [
        {
            "assessment_item_id": r.assessment_item_id,
            "enrollment_id": r.enrollment_id,
            "obtained_marks": float(r.obtained_marks or 0),
        }
        for r in rows
    ]


@router.post("/teacher/course/{course_id}/scores/bulk")
def teacher_upsert_scores_bulk(
    course_id: int,
    payload: dict,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    teacher_id = _require_teacher(current_user)
    _teacher_course_or_404(db, teacher_id, course_id)

    scores = payload.get("scores", [])
    if not isinstance(scores, list):
        raise HTTPException(status_code=400, detail="scores must be a list")

    # cache items for this course
    items = db.query(AssessmentItem.id).filter(AssessmentItem.course_id == course_id).all()
    item_ids = {i[0] for i in items}

    # cache enrollments for this course
    enrolls = db.query(Enrollment.id).filter(Enrollment.course_id == course_id).all()
    enrollment_ids = {e[0] for e in enrolls}

    updated = 0
    created = 0

    for raw in scores:
        s = ScoreUpsert(**raw)

        if s.assessment_item_id not in item_ids:
            continue
        if s.enrollment_id not in enrollment_ids:
            continue

        row = (
            db.query(AssessmentScore)
            .filter(
                AssessmentScore.assessment_item_id == s.assessment_item_id,
                AssessmentScore.enrollment_id == s.enrollment_id,
            )
            .first()
        )

        if row:
            row.obtained_marks = float(s.obtained_marks)
            row.graded_by_user_id = current_user.id
            updated += 1
        else:
            row = AssessmentScore(
                assessment_item_id=s.assessment_item_id,
                enrollment_id=s.enrollment_id,
                obtained_marks=float(s.obtained_marks),
                graded_by_user_id=current_user.id,
            )
            db.add(row)
            created += 1

    db.commit()

    return {"ok": True, "updated": updated, "created": created}
# -------------------------
# Student: Grades summary
# -------------------------
@router.get("/my")
def student_my_grades_summary(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    role = _role_value(current_user.role)
    if role != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")
    if not current_user.student:
        raise HTTPException(status_code=404, detail="Student record not linked")

    student_id = current_user.student.id

    # all enrollments for this student
    enrolls = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id)
        .all()
    )
    course_ids = [e.course_id for e in enrolls]

    if not course_ids:
        return []

    courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
    course_map = {c.id: c for c in courses}

    # weights (change if you want)
    INTERNAL_W = 30.0
    MID_W = 30.0
    FINAL_W = 40.0

    results = []

    for e in enrolls:
        course = course_map.get(e.course_id)

        # fetch all items for this course
        items = (
            db.query(AssessmentItem)
            .filter(AssessmentItem.course_id == e.course_id)
            .all()
        )
        if not items:
            # still return course row (all zeros)
            results.append({
                "course_id": e.course_id,
                "course_code": course.code if course else None,
                "course_title": course.title if course else None,
                "internal_percent": 0.0,
                "mid_percent": 0.0,
                "final_percent": 0.0,
                "total_out_of_100": 0.0,
            })
            continue

        item_ids = [it.id for it in items]

        scores = (
            db.query(AssessmentScore)
            .filter(
                AssessmentScore.enrollment_id == e.id,
                AssessmentScore.assessment_item_id.in_(item_ids),
            )
            .all()
        )
        score_map = {s.assessment_item_id: float(s.obtained_marks or 0) for s in scores}

        # sums by category
        cat_max = {"quiz": 0.0, "assignment": 0.0, "mid": 0.0, "final": 0.0}
        cat_obt = {"quiz": 0.0, "assignment": 0.0, "mid": 0.0, "final": 0.0}

        for it in items:
            cat = _role_value(it.category)  # enum -> str
            cat_max[cat] += float(it.max_marks or 0)
            cat_obt[cat] += float(score_map.get(it.id, 0.0))

        # internal = quiz + assignment (percentage)
        internal_max = cat_max["quiz"] + cat_max["assignment"]
        internal_obt = cat_obt["quiz"] + cat_obt["assignment"]
        internal_pct = (internal_obt / internal_max * 100.0) if internal_max > 0 else 0.0

        mid_pct = (cat_obt["mid"] / cat_max["mid"] * 100.0) if cat_max["mid"] > 0 else 0.0
        final_pct = (cat_obt["final"] / cat_max["final"] * 100.0) if cat_max["final"] > 0 else 0.0

        # convert to weighted out of 100
        total = (internal_pct/100.0)*INTERNAL_W + (mid_pct/100.0)*MID_W + (final_pct/100.0)*FINAL_W

        results.append({
            "course_id": e.course_id,
            "course_code": course.code if course else None,
            "course_title": course.title if course else None,
            "internal_percent": float(internal_pct),
            "mid_percent": float(mid_pct),
            "final_percent": float(final_pct),
            "total_out_of_100": float(total),
        })

    return results


# -------------------------
# Student: Course grade detail
# -------------------------
@router.get("/my/course/{course_id}")
def student_my_course_detail(
    course_id: int,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    role = _role_value(current_user.role)
    if role != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")
    if not current_user.student:
        raise HTTPException(status_code=404, detail="Student record not linked")

    student_id = current_user.student.id

    enroll = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id, Enrollment.course_id == course_id)
        .first()
    )
    if not enroll:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")

    course = db.get(Course, course_id)

    items = (
        db.query(AssessmentItem)
        .filter(AssessmentItem.course_id == course_id)
        .order_by(AssessmentItem.id)
        .all()
    )

    item_ids = [it.id for it in items]
    scores = (
        db.query(AssessmentScore)
        .filter(
            AssessmentScore.enrollment_id == enroll.id,
            AssessmentScore.assessment_item_id.in_(item_ids),
        )
        .all()
    )
    score_map = {s.assessment_item_id: float(s.obtained_marks or 0) for s in scores}

    # calc same as summary
    INTERNAL_W = 30.0
    MID_W = 30.0
    FINAL_W = 40.0

    cat_max = {"quiz": 0.0, "assignment": 0.0, "mid": 0.0, "final": 0.0}
    cat_obt = {"quiz": 0.0, "assignment": 0.0, "mid": 0.0, "final": 0.0}

    out_items = []
    for it in items:
        cat = _role_value(it.category)
        obt = score_map.get(it.id, None)
        cat_max[cat] += float(it.max_marks or 0)
        cat_obt[cat] += float(obt or 0)

        out_items.append({
            "item_id": it.id,
            "title": it.title,
            "category": cat,
            "max_marks": float(it.max_marks or 0),
            "obtained_marks": obt,  # null if not entered
            "due_date": it.due_date.isoformat() if it.due_date else None,
        })

    internal_max = cat_max["quiz"] + cat_max["assignment"]
    internal_obt = cat_obt["quiz"] + cat_obt["assignment"]
    internal_pct = (internal_obt / internal_max * 100.0) if internal_max > 0 else 0.0
    mid_pct = (cat_obt["mid"] / cat_max["mid"] * 100.0) if cat_max["mid"] > 0 else 0.0
    final_pct = (cat_obt["final"] / cat_max["final"] * 100.0) if cat_max["final"] > 0 else 0.0
    total = (internal_pct/100.0)*INTERNAL_W + (mid_pct/100.0)*MID_W + (final_pct/100.0)*FINAL_W

    return {
        "course_id": course_id,
        "course_code": course.code if course else None,
        "course_title": course.title if course else None,
        "items": out_items,
        "internal_percent": float(internal_pct),
        "mid_percent": float(mid_pct),
        "final_percent": float(final_pct),
        "total_out_of_100": float(total),
    }
