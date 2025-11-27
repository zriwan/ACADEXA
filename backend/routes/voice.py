from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.models import Student, Teacher, User
from backend.security import get_current_user

router = APIRouter(
    prefix="/voice-command",
    tags=["Voice Commands"],
)


@router.post("/")
def process_voice_command(
    payload: dict,
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),  # ✅ auth required
):
    """
    Very simple version:
    - request body se "text" read karega
    - "show students" / "show teachers" detect karega
    - sirf authenticated user ke liye DB se data laa kar JSON me return karega
    """
    text = payload.get("text") if payload else ""

    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text provided",
        )

    text_lower = text.lower().strip()

    # -------------------------
    # 1) SHOW / LIST STUDENTS
    # -------------------------
    if "show students" in text_lower or "list students" in text_lower:
        students = db.query(Student).all()
        result = []
        for s in students:
            result.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "department": s.department,
                    "gpa": float(s.gpa) if s.gpa is not None else None,
                }
            )
        return {
            "command": text,
            "intent": "list_students",
            "result": result,
        }

    # -------------------------
    # 2) SHOW / LIST TEACHERS
    # -------------------------
    if "show teachers" in text_lower or "list teachers" in text_lower:
        teachers = db.query(Teacher).all()
        result = []
        for t in teachers:
            result.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "email": t.email,
                    "department": t.department,
                }
            )
        return {
            "command": text,
            "intent": "list_teachers",
            "result": result,
        }

    # Agar text match nahi hua:
    return {
        "command": text,
        "message": "Sorry, I did not understand the command (simple version).",
    }
