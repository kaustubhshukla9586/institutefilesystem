# Privacy-Aware RAG System for Sensitive Institutional Documents

A question-answering assistant over the documents of a fictional university. Personal data is redacted before
anything is indexed or sent to the LLM, retrieval is filtered by the user's role inside the vector-database query,
answers are generated only from documents the user may see, and every query is written to an audit log.
This is a **prototype on synthetic data**: all documents and people are invented, and redaction reduces the risk of
exposing personal data but does not guarantee it.

**Stack:** FastAPI · SQLite (SQLAlchemy) · ChromaDB · Presidio + spaCy · sentence-transformers (all-MiniLM-L6-v2) ·
Groq LLM · JWT + bcrypt · React (Vite) + Tailwind.

## Setup (Windows, Python 3.11+, Node 20+)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_lg
copy .env.example .env          # then fill in GROQ_API_KEY and JWT_SECRET
python -m app.ingestion         # only if backend/chroma_db is empty or missing

cd ..\frontend
npm install
```

## Run

```powershell
# Terminal 1
cd backend; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --port 8000
# Terminal 2
cd frontend; npm run dev
```

Open http://localhost:5173 (API docs at http://localhost:8000/docs).

## Demo accounts (password `demo1234`)

| Role | Email |
|---|---|
| Student | student@demo.com |
| Faculty | faculty@demo.com |
| Admin | admin@demo.com |

## Notes

Built with AI coding assistance.
