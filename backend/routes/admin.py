# backend/routes/admin.py

from fastapi import APIRouter, Depends

from backend.security import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user=Depends(get_current_user)):
    """
    Enforce admin role.
    get_current_user already returns a User with .role.
    """
    role = getattr(current_user, "role", None)
    # role may be Enum(UserRole) or str; normalize
    role_value = getattr(role, "value", role)

    if role_value != "admin":
        # Use 403 for authenticated but forbidden
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/overview")
def admin_overview(current_user=Depends(require_admin)):
    """
    Minimal admin-only endpoint for RBAC verification and dashboard health check.
    """
    return {"ok": True, "message": "Admin access granted"}
