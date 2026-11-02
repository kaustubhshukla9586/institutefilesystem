# University Privacy-Aware RAG System

A RAG (Retrieval-Augmented Generation) chatbot over university internal documents with:
- **PII Redaction** (Microsoft Presidio) — no raw PII ever sent to the LLM
- **Role-Based Access Control** — student/faculty/admin roles restrict which documents are retrieved
- **Audit Logging** — every query is logged with user, role, retrieved docs, and answer

## Architecture

```
Frontend (React/Vite :5173)
    ↕ REST + JWT
Backend (FastAPI :8000)
    ├── Auth: SQLite via SQLAlchemy
    ├── PII: Microsoft Presidio + spaCy
    ├── Vector DB: ChromaDB (local persistent)
    ├── Embeddings: sentence-transformers (all-MiniLM-L6-v2, local/free)
    └── Generation: Groq API (llama-3.1-8b-instant)
```

## Prerequisites

- **Python 3.9+** (tested on 3.14.5)
- **Node.js 18+**
- **Groq API key** — free at [console.groq.com](https://console.groq.com)

## Setup

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Download spaCy NLP model (needed by Presidio)
python -m spacy download en_core_web_lg
```

### 2. Environment variables

```bash
# Copy the example and fill in your key
cp .env.example .env
```

Edit `backend/.env`:
```
GROQ_API_KEY=gsk_your_key_here
SECRET_KEY=any-long-random-string-here
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 3. Generate synthetic documents (one-time)

```bash
cd backend
python -m app.seed_data.generate_docs
```

This calls Groq to generate ~65 synthetic university documents (public, faculty-only, admin-only) and saves them to `app/seed_data/raw_docs/documents.json`.

### 4. Ingest documents into ChromaDB (one-time, or to reset)

```bash
cd backend
python -m app.ingestion
```

This redacts PII from every document, chunks them, embeds them with the local sentence-transformer model, and stores everything in `chroma_db/`. Output will show the total chunk count.

### 5. Frontend

```bash
cd frontend
npm install
```

## Running

Start both servers (in separate terminals):

**Terminal 1 — Backend:**
```bash
cd backend
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Demo Credentials

Three accounts are auto-seeded on first backend startup:

| Email | Password | Role |
|-------|----------|------|
| student@demo.com | demo1234 | student |
| faculty@demo.com | demo1234 | faculty |
| admin@demo.com   | demo1234 | admin |

## Key Demo Flow

1. **Log in as `student@demo.com`** → ask "Tell me about disciplinary records or HR complaints"
   - Expected: "I don't have access to information that would answer this question." (no admin sources shown)

2. **Log in as `admin@demo.com`** → ask the same question
   - Expected: A real answer drawn from admin-level documents, with source badges showing `admin` access level

3. **Faculty view**: Log in as `faculty@demo.com` → ask about student grades or faculty meetings
   - Expected: Answers from `public` and `faculty` documents, but not `admin`

4. **Admin Dashboard** → view audit log showing both queries side-by-side

## Project Structure

```
backend/
  app/
    main.py           — FastAPI entrypoint, CORS, lifespan seeding
    auth.py           — JWT, bcrypt, demo user seeding
    models.py         — SQLAlchemy: User, AuditLog
    database.py       — SQLite engine/session
    pii_redaction.py  — Presidio wrapper with custom STUDENT_ID recognizer
    ingestion.py      — Redact → chunk → embed → store pipeline
    retrieval.py      — Role-filtered ChromaDB similarity search
    generation.py     — Groq LLM prompt builder + call
    routers/
      auth_router.py  — /auth/signup, /auth/login
      chat_router.py  — /chat/query (protected)
      admin_router.py — /admin/audit-log, /admin/documents (admin-only)
    seed_data/
      generate_docs.py        — One-time LLM document generator
      raw_docs/documents.json — Generated synthetic docs (gitignored)
  chroma_db/         — ChromaDB persistent storage (gitignored)
  app.db             — SQLite database (gitignored)

frontend/src/
  pages/
    Login.jsx         — Login form with demo credentials shown
    Signup.jsx        — Signup with role selection
    Chat.jsx          — Chat interface with sources section
    AdminDashboard.jsx — Audit log + documents tables (admin-only)
  components/
    Navbar.jsx        — Role badge, admin link, logout
    RoleBadge.jsx     — Colored badge: public/faculty/admin/student
  api/client.js       — Axios instance, JWT injection, 401 redirect
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/signup | None | Create account |
| POST | /auth/login | None | Login, returns JWT |
| POST | /chat/query | JWT | RAG query |
| GET | /admin/audit-log | Admin JWT | All audit logs |
| GET | /admin/documents | Admin JWT | Document list |
| GET | /health | None | Health check |

## Re-ingesting

If you re-run `generate_docs.py`, always follow with `python -m app.ingestion` to rebuild the vector store. The ingestion script drops and recreates the Chroma collection each run (idempotent).
