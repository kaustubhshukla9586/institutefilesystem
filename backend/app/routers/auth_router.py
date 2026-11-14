from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from ..auth import (MIN_PASSWORD_LENGTH, allowed_levels, check_rate_limit, clear_failures, create_access_token,
                    get_current_user, hash_password, record_failure, verify_password)
from ..database import get_db
from ..models import User

router = APIRouter(tags=["auth"])


class SignupRequest(BaseModel):
    # extra fields (e.g. "role") are ignored: self-registration always creates a student
    model_config = ConfigDict(extra="ignore")
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    expires_in: int = 3600


@router.post("/auth/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status_code=400, detail="That email is already registered. Try signing in.")
    user = User(email=body.email.lower(), hashed_password=hash_password(body.password), role="student")
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user), role=user.role, email=user.email)


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, body.email)
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        record_failure(request, body.email)
        raise HTTPException(status_code=401, detail="Wrong email or password.")
    clear_failures(request, body.email)
    return TokenResponse(access_token=create_access_token(user), role=user.role, email=user.email)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role, "allowed_levels": allowed_levels(user.role)}
