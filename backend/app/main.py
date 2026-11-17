import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from .auth import seed_demo_users  # noqa: E402  (refuses to import without JWT_SECRET outside dev)
from .database import SessionLocal, engine  # noqa: E402
from .models import Base  # noqa: E402
from .routers import admin_router, auth_router, chat_router  # noqa: E402

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_demo_users(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Privacy-Aware RAG (Thornwick University)", version="2.0.0", lifespan=lifespan)

# Only the frontend origin(s) may call the API from a browser.
# Comma-separated; spaces and trailing slashes are stripped, empty entries and "*" are ignored.
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
ALLOWED_ORIGINS = [o for o in ALLOWED_ORIGINS if o and o != "*"] or ["http://localhost:5173"]
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=False,
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type"], max_age=600)

app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(admin_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
