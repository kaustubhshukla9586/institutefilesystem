import os
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

APP_ENV = os.getenv("APP_ENV", "dev").lower()
SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if APP_ENV != "dev":
        raise RuntimeError("JWT_SECRET must be set when APP_ENV is not 'dev'")
    SECRET_KEY = "dev-only-insecure-secret"
    print("[AUTH] WARNING: JWT_SECRET not set; using an insecure dev secret")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MIN_PASSWORD_LENGTH = 8

ROLE_LEVEL = {"student": 0, "faculty": 1, "admin": 2}
ACCESS_LEVELS = ["public", "faculty", "admin"]  # index == clearance

import logging  # noqa: E402

# passlib probes bcrypt.__about__ (gone in bcrypt 4) and logs a harmless traceback on every start
logging.getLogger("passlib").setLevel(logging.ERROR)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Verify the JWT signature/expiry, then load the user from the DB.
    The role used for access control is the DB role, and must match the token's role
    (a token issued before a role change is rejected)."""
    exc = HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise exc
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
        token_role = payload.get("role")
    except (JWTError, KeyError, ValueError):
        raise exc
    user = db.get(User, user_id)
    if user is None or user.role != token_role:
        raise exc
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("faculty", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faculty or admin access required")
    return current_user


def allowed_levels(role: str) -> list[str]:
    return ACCESS_LEVELS[: ROLE_LEVEL.get(role, 0) + 1]


# ---- simple in-memory login rate limit: 5 failures per (ip,email) per 5 minutes ----
_FAILS: dict[str, deque] = defaultdict(deque)
MAX_FAILS, WINDOW_S = 5, 300


def _key(request: Request, email: str) -> str:
    return f"{request.client.host if request.client else '?'}|{email.lower()}"


def check_rate_limit(request: Request, email: str):
    q = _FAILS[_key(request, email)]
    now = time.monotonic()
    while q and now - q[0] > WINDOW_S:
        q.popleft()
    if len(q) >= MAX_FAILS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in a few minutes.")


def record_failure(request: Request, email: str):
    _FAILS[_key(request, email)].append(time.monotonic())


def clear_failures(request: Request, email: str):
    _FAILS.pop(_key(request, email), None)


def seed_demo_users(db: Session):
    demo = [("student@demo.com", "student"), ("faculty@demo.com", "faculty"), ("admin@demo.com", "admin")]
    for email, role in demo:
        if not db.query(User).filter(User.email == email).first():
            db.add(User(email=email, hashed_password=hash_password("demo1234"), role=role))
    # remove leftover RBAC test accounts from earlier manual testing
    db.query(User).filter(User.email.like("rbaccheck%")).delete(synchronize_session=False)
    db.commit()
    print("[DEMO] student@demo.com / faculty@demo.com / admin@demo.com  (password: demo1234)")
