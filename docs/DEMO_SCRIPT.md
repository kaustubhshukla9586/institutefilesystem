# 5-minute demo script

Before: backend on :8000 (`uvicorn app.main:app --port 8000`), frontend on :5173 (`npm run dev`), browser at http://localhost:5173. Password for all demo accounts: `demo1234`.

| Time | Do | Say |
|---|---|---|
| 0:00 | Landing page. Click **Public / Faculty / Admin** on the clearance toggle. | "Same question, three clearances. Students get a refusal, faculty get the document with names cut out, and only admins can open the original, which is logged." |
| 0:40 | **Sign in** -> click the *Student* demo chip -> Sign in. Show the student dashboard. | "Sign-up only ever creates students. Faculty and admin are granted, not chosen." |
| 1:00 | **Ask** -> *What is the late fee for paying tuition between August 16 and September 4?* | "The LLM answers from a public policy. The citation underneath shows the document, its level and the exact snippet used." |
| 1:40 | Ask: *What is the total departmental budget sanctioned for 2025-26?* | "That's an admin document. The student gets a refusal with no sources, and the same wording is used whether or not such a document exists, so the refusal doesn't leak anything." |
| 2:20 | Sign out -> sign in as **Admin** -> Ask the same budget question. | "Same question, admin role: answered from ADM004, cited. The role comes from the signed token and is re-checked against the database. The filter runs inside the ChromaDB query." |
| 3:00 | **Audit log** -> Result = *Refused* -> Apply filters. | "Every query is logged with user, role, question, sources and result. Here's the student's refused question." |
| 3:40 | **Documents** -> *Research Committee Meeting – April 2025*. Toggle **As stored** / **Original (logged)**. | "This is exactly what's embedded: names, roll numbers and emails are placeholders. Opening the original writes a reveal event to the audit log." |
| 4:20 | **Upload** -> pick a .txt with a name, email and phone -> level *Faculty* -> Upload and index. | "It's redacted before chunking. Before/after are shown, and the document is only retrievable at faculty level and above. Faculty can't tag above their own level." |
| 4:50 | Close on `backend/eval/results/results.md`. | "Measured: 0 leaks in 337 chunks, 57/60 role-matrix cases, recall@1 0.95. The three failures are over-cautious refusals, not leaks." |

Sample upload file (save as `note.txt`):

```
Chemistry Lab Safety Note, effective 1 December 2026. Report spills to Dr. Meera Iyer
(meera.iyer@thornwick.example, +91 98123 45678). Goggles are mandatory in Lab 2B.
```
