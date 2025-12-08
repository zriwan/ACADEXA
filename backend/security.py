# backend/security.py
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db_connection
from .models import User, UserRole

# ===== JWT & security settings =====
SECRET_KEY = "CHANGE_THIS_SECRET_KEY"  # in real app: os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ FIXED: use the *form* login endpoint here
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ===== Password hashing =====
def hash_password(password: str) -> str:
    """Hash plain password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against stored hash."""
    return pwd_context.verify(plain, hashed)


# ===== JWT creation =====
def create_access_token(
    sub: str, role: str, expires_delta: timedelta | None = None
) -> str:
    """Generate JWT token with subject (email) and role."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": sub, "role": role, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ===== Current user dependencies =====
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_connection),
) -> User:
    """Decode token and return the corresponding User."""
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise cred_exc
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Check if the current user has admin privileges."""
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
