# backend/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db_connection
from ..models import User, UserRole
from ..schemas import TokenResponse, UserCreate, UserResponse, UserLogin
from ..security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# -----------------------------
# REGISTER
# -----------------------------
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db_connection),
):
    """
    Register a new user (admin or normal user).

    Expects JSON body:
    {
      "name": "...",
      "email": "...",
      "password": "...",
      "role": "admin" | "user"
    }
    """
    # check if email already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # validate role string -> Enum
    try:
        role = UserRole[user_in.role]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role, must be 'admin' or 'user'",
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# -----------------------------
# INTERNAL AUTH HELPERS
# -----------------------------
def _authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def _make_token_for_user(user: User) -> TokenResponse:
    token = create_access_token(sub=user.email, role=user.role.value)
    return TokenResponse(access_token=token)


# -----------------------------
# LOGIN (FORM)  → /auth/login
# -----------------------------
@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_connection),
):
    """
    Standard OAuth2-style login:
    - Tests and Swagger usually send form fields:
      username=<email>, password=<password>
    """
    email = form_data.username
    password = form_data.password

    user = _authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return _make_token_for_user(user)


# -----------------------------
# LOGIN (FORM) ALIAS → /auth/token
# -----------------------------
@router.post("/token", response_model=TokenResponse)
def login_token_alias(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_connection),
):
    """
    Alias for /auth/login.
    Some tests / tools call /auth/token instead.
    """
    email = form_data.username
    password = form_data.password

    user = _authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return _make_token_for_user(user)


# -----------------------------
# OPTIONAL JSON LOGIN → /auth/login/json
# (convenience if you want to log in with JSON)
# -----------------------------
@router.post("/login/json", response_model=TokenResponse)
def login_json(
    user_in: UserLogin,
    db: Session = Depends(get_db_connection),
):
    """
    JSON-based login (optional convenience endpoint):

    Body:
    {
      "email": "...",
      "password": "..."
    }
    """
    user = _authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return _make_token_for_user(user)


# -----------------------------
# /auth/me → current user
# -----------------------------
@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user based on the JWT token.
    """
    return current_user
