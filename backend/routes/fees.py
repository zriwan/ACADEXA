# backend/routes/fees.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db_connection
from backend.security import get_current_user, require_admin
from backend.models import User, UserRole, Student, FeeAccount, FeeTransaction, FeeTxnType
from backend.schemas import FeeAccountSet, FeeTxnCreate

router = APIRouter(prefix="/fees", tags=["Fees"])


def _role_value(role):
    return role.value if hasattr(role, "value") else role


def _require_student(user: User) -> int:
    if _role_value(user.role) != UserRole.student:
        raise HTTPException(status_code=403, detail="Student access required")
    if not user.student:
        raise HTTPException(status_code=404, detail="Student record not linked")
    return user.student.id


def _build_fee_status_for_student(db: Session, student_id: int):
    acc = db.query(FeeAccount).filter(FeeAccount.student_id == student_id).first()
    total_fee = float(acc.total_fee) if acc else 0.0

    txns = (
        db.query(FeeTransaction)
        .filter(FeeTransaction.student_id == student_id)
        .order_by(FeeTransaction.created_at.desc())
        .all()
    )

    paid = 0.0
    fine = 0.0
    scholarship = 0.0
    adjustment = 0.0

    out = []
    for t in txns:
        ttype = t.txn_type.value if hasattr(t.txn_type, "value") else str(t.txn_type)
        amt = float(t.amount or 0)

        if ttype == "payment":
            paid += amt
        elif ttype == "fine":
            fine += amt
        elif ttype == "scholarship":
            scholarship += amt
        elif ttype == "adjustment":
            adjustment += amt

        out.append(
            {
                "id": t.id,
                "student_id": t.student_id,
                "txn_type": ttype,
                "amount": amt,
                "note": t.note,
                "created_at": t.created_at,
            }
        )

    pending = total_fee + fine + adjustment - paid - scholarship
    if pending < 0:
        pending = 0.0

    return {
        "student_id": student_id,
        "total_fee": total_fee,
        "paid": paid + scholarship,   # credit view
        "pending": pending,
        "transactions": out,
    }


# -------------------------
# Admin: set total fee
# -------------------------
@router.post("/accounts/set", status_code=status.HTTP_200_OK)
def admin_set_fee_account(
    payload: FeeAccountSet,
    db: Session = Depends(get_db_connection),
    admin_user: User = Depends(require_admin),
):
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    acc = db.query(FeeAccount).filter(FeeAccount.student_id == payload.student_id).first()
    if not acc:
        acc = FeeAccount(student_id=payload.student_id, total_fee=payload.total_fee)
        db.add(acc)
    else:
        acc.total_fee = payload.total_fee

    db.commit()
    return {"ok": True, "student_id": payload.student_id, "total_fee": float(acc.total_fee)}


# -------------------------
# Admin: add transaction
# -------------------------
@router.post("/transactions", status_code=status.HTTP_201_CREATED)
def admin_add_fee_transaction(
    payload: FeeTxnCreate,
    db: Session = Depends(get_db_connection),
    admin_user: User = Depends(require_admin),
):
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    txn = FeeTransaction(
        student_id=payload.student_id,
        txn_type=FeeTxnType(payload.txn_type),
        amount=payload.amount,
        note=payload.note,
        created_by_user_id=admin_user.id,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return {
        "id": txn.id,
        "student_id": txn.student_id,
        "txn_type": txn.txn_type.value if hasattr(txn.txn_type, "value") else str(txn.txn_type),
        "amount": float(txn.amount),
        "note": txn.note,
        "created_at": txn.created_at,
    }


# ✅ NEW: Admin can view any student's fee status
@router.get("/student/{student_id}")
def admin_get_student_fees(
    student_id: int,
    db: Session = Depends(get_db_connection),
    admin_user: User = Depends(require_admin),
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return _build_fee_status_for_student(db, student_id)


# -------------------------
# Student: my fee status
# -------------------------
@router.get("/me")
def student_my_fees(
    db: Session = Depends(get_db_connection),
    current_user: User = Depends(get_current_user),
):
    student_id = _require_student(current_user)
    return _build_fee_status_for_student(db, student_id)
