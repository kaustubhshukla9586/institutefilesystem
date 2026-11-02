"""
One-time script to generate ~70 synthetic university documents via Groq LLM.
Run from the backend/ directory:
    python -m app.seed_data.generate_docs

Outputs: app/seed_data/raw_docs/documents.json
"""
import json
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

from groq import Groq

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_docs", "documents.json")
MODEL = "openai/gpt-oss-20b"

# Synthetic roll number format: RK3P25KZBxx (e.g. RK3P25KZB01 to RK3P25KZB99)
DOC_SPECS = [
    # PUBLIC docs (~20)
    {"doc_id": "PUB001", "access_level": "public", "category": "policy", "title": "Academic Integrity Policy"},
    {"doc_id": "PUB002", "access_level": "public", "category": "policy", "title": "Library Usage Guidelines"},
    {"doc_id": "PUB003", "access_level": "public", "category": "calendar", "title": "Academic Calendar 2025-26"},
    {"doc_id": "PUB004", "access_level": "public", "category": "announcement", "title": "Semester Registration Announcement"},
    {"doc_id": "PUB005", "access_level": "public", "category": "policy", "title": "Hostel Accommodation Rules"},
    {"doc_id": "PUB006", "access_level": "public", "category": "policy", "title": "Examination Rules and Regulations"},
    {"doc_id": "PUB007", "access_level": "public", "category": "announcement", "title": "Sports Week Announcement"},
    {"doc_id": "PUB008", "access_level": "public", "category": "policy", "title": "Fee Payment Deadlines and Late Fees Policy"},
    {"doc_id": "PUB009", "access_level": "public", "category": "announcement", "title": "Annual Research Symposium Notice"},
    {"doc_id": "PUB010", "access_level": "public", "category": "policy", "title": "Anti-Ragging Policy"},
    {"doc_id": "PUB011", "access_level": "public", "category": "policy", "title": "Student Grievance Redressal Procedure"},
    {"doc_id": "PUB012", "access_level": "public", "category": "announcement", "title": "Convocation Ceremony 2025 Notice"},
    {"doc_id": "PUB013", "access_level": "public", "category": "policy", "title": "IT Lab Usage Policy"},
    {"doc_id": "PUB014", "access_level": "public", "category": "announcement", "title": "Campus Placement Drive Schedule"},
    {"doc_id": "PUB015", "access_level": "public", "category": "policy", "title": "Scholarship Eligibility Criteria"},
    {"doc_id": "PUB016", "access_level": "public", "category": "announcement", "title": "National Holiday Revised Schedule"},
    {"doc_id": "PUB017", "access_level": "public", "category": "policy", "title": "Dress Code and Campus Conduct Policy"},
    {"doc_id": "PUB018", "access_level": "public", "category": "policy", "title": "Medical Facilities on Campus"},
    {"doc_id": "PUB019", "access_level": "public", "category": "announcement", "title": "New Elective Course Offerings 2025-26"},
    {"doc_id": "PUB020", "access_level": "public", "category": "policy", "title": "Parking and Transportation Policy"},

    # FACULTY docs (~25)
    {"doc_id": "FAC001", "access_level": "faculty", "category": "meeting_minutes", "title": "Faculty Senate Meeting Minutes – March 2025"},
    {"doc_id": "FAC002", "access_level": "faculty", "category": "meeting_minutes", "title": "Department of Computer Science Meeting – Feb 2025"},
    {"doc_id": "FAC003", "access_level": "faculty", "category": "grade_summary", "title": "CS301 Data Structures – Grade Summary Semester 1"},
    {"doc_id": "FAC004", "access_level": "faculty", "category": "grade_summary", "title": "MA201 Linear Algebra – Grade Summary Semester 1"},
    {"doc_id": "FAC005", "access_level": "faculty", "category": "performance_note", "title": "Student Performance Note – CS Department Probation List"},
    {"doc_id": "FAC006", "access_level": "faculty", "category": "meeting_minutes", "title": "Curriculum Review Committee Meeting – Jan 2025"},
    {"doc_id": "FAC007", "access_level": "faculty", "category": "grade_summary", "title": "PH101 Engineering Physics – Final Grade Report"},
    {"doc_id": "FAC008", "access_level": "faculty", "category": "performance_note", "title": "Academic Counselling Session Records – Batch 2023"},
    {"doc_id": "FAC009", "access_level": "faculty", "category": "meeting_minutes", "title": "Research Committee Meeting – April 2025"},
    {"doc_id": "FAC010", "access_level": "faculty", "category": "grade_summary", "title": "EE202 Circuit Theory – Mid-Semester Grade Report"},
    {"doc_id": "FAC011", "access_level": "faculty", "category": "performance_note", "title": "Internship Performance Feedback – Summer 2024"},
    {"doc_id": "FAC012", "access_level": "faculty", "category": "meeting_minutes", "title": "PhD Admissions Committee Minutes – August 2025"},
    {"doc_id": "FAC013", "access_level": "faculty", "category": "performance_note", "title": "TA Performance Evaluations – CS Department"},
    {"doc_id": "FAC014", "access_level": "faculty", "category": "grade_summary", "title": "CH301 Organic Chemistry – Practical Exam Results"},
    {"doc_id": "FAC015", "access_level": "faculty", "category": "meeting_minutes", "title": "Anti-Plagiarism Committee Findings – Semester 1"},
    {"doc_id": "FAC016", "access_level": "faculty", "category": "performance_note", "title": "Project Evaluation Notes – Final Year Batch 2025"},
    {"doc_id": "FAC017", "access_level": "faculty", "category": "grade_summary", "title": "CS401 Machine Learning – Grade Distribution Report"},
    {"doc_id": "FAC018", "access_level": "faculty", "category": "meeting_minutes", "title": "Department Heads Coordination Meeting – May 2025"},
    {"doc_id": "FAC019", "access_level": "faculty", "category": "performance_note", "title": "Remedial Programme Enrollment List"},
    {"doc_id": "FAC020", "access_level": "faculty", "category": "grade_summary", "title": "ME301 Thermodynamics – Supplementary Exam Results"},
    {"doc_id": "FAC021", "access_level": "faculty", "category": "meeting_minutes", "title": "Timetable Revision Committee Notes – Semester 2"},
    {"doc_id": "FAC022", "access_level": "faculty", "category": "performance_note", "title": "Scholarship Renewal Eligibility Assessment"},
    {"doc_id": "FAC023", "access_level": "faculty", "category": "grade_summary", "title": "BA201 Business Communication – Semester Grade Summary"},
    {"doc_id": "FAC024", "access_level": "faculty", "category": "meeting_minutes", "title": "Ethics and Research Integrity Workshop – Summary"},
    {"doc_id": "FAC025", "access_level": "faculty", "category": "performance_note", "title": "Student Attendance Shortfall Report – All Departments"},

    # ADMIN docs (~20)
    {"doc_id": "ADM001", "access_level": "admin", "category": "disciplinary", "title": "Disciplinary Case Report – Academic Misconduct 2024"},
    {"doc_id": "ADM002", "access_level": "admin", "category": "disciplinary", "title": "Disciplinary Hearing Minutes – Plagiarism Case A"},
    {"doc_id": "ADM003", "access_level": "admin", "category": "hr", "title": "HR Complaint – Faculty Misconduct Case"},
    {"doc_id": "ADM004", "access_level": "admin", "category": "budget", "title": "Departmental Budget Allocation 2025-26"},
    {"doc_id": "ADM005", "access_level": "admin", "category": "disciplinary", "title": "Suspension Notice – Student Code Violation"},
    {"doc_id": "ADM006", "access_level": "admin", "category": "hr", "title": "Staff Performance Appraisal Report – 2024"},
    {"doc_id": "ADM007", "access_level": "admin", "category": "budget", "title": "Research Grant Expenditure Report Q3 2025"},
    {"doc_id": "ADM008", "access_level": "admin", "category": "disciplinary", "title": "Ragging Incident Investigation Report"},
    {"doc_id": "ADM009", "access_level": "admin", "category": "hr", "title": "Faculty Salary Revision Proposal 2025"},
    {"doc_id": "ADM010", "access_level": "admin", "category": "disciplinary", "title": "Examination Malpractice Case – Detailed Report"},
    {"doc_id": "ADM011", "access_level": "admin", "category": "budget", "title": "Infrastructure Development Fund Utilization"},
    {"doc_id": "ADM012", "access_level": "admin", "category": "hr", "title": "New Faculty Recruitment – Offer Letters Summary"},
    {"doc_id": "ADM013", "access_level": "admin", "category": "disciplinary", "title": "Grievance Escalation – Hostel Harassment Case"},
    {"doc_id": "ADM014", "access_level": "admin", "category": "budget", "title": "Scholarship Fund Disbursement Records 2025"},
    {"doc_id": "ADM015", "access_level": "admin", "category": "hr", "title": "Retirement and Succession Planning Report"},
    {"doc_id": "ADM016", "access_level": "admin", "category": "disciplinary", "title": "Internal Audit – Library Fine Waiver Requests"},
    {"doc_id": "ADM017", "access_level": "admin", "category": "budget", "title": "Annual Fee Revision Proposal – Academic Council"},
    {"doc_id": "ADM018", "access_level": "admin", "category": "hr", "title": "Contract Staff Renewal and Termination Summary"},
    {"doc_id": "ADM019", "access_level": "admin", "category": "disciplinary", "title": "Student Expulsion Case – Final Order"},
    {"doc_id": "ADM020", "access_level": "admin", "category": "budget", "title": "External Audit Findings – Finance Department"},
]

PII_INSTRUCTION = """
Include realistic but clearly fake PII in the document where appropriate for this document type:
- Fake student names (Indian-style names like Ananya Verma, Rohan Sharma, Priya Nair, etc.)
- Fake student roll numbers in format RK3P25KZBxx where xx is a 2-digit number (e.g. RK3P25KZB01, RK3P25KZB42)
- Fake email addresses (format: firstname.rollnum@university.edu, e.g. ananya.rk3p25kzb01@university.edu)
- Fake phone numbers (Indian format: +91 98XXX XXXXX)
This is synthetic data for a university demo system, not real people.
"""

NO_PII_INSTRUCTION = "This is a public document — do not include any personal identifying information."


def generate_doc_content(client: Groq, spec: dict) -> str:
    access = spec["access_level"]
    pii_note = PII_INSTRUCTION if access in ("faculty", "admin") else NO_PII_INSTRUCTION

    prompt = f"""Generate a realistic synthetic university document with the following details:

Title: {spec['title']}
Category: {spec['category']}
Access Level: {access}

{pii_note}

Write the full document content (2-4 paragraphs, ~200-400 words).
Write it as an actual internal university document — not a placeholder or description of what the document would contain.
Include specific details that make it realistic (dates in 2024-2025, course codes, committee names, policy sections, case numbers, etc.).
Do NOT include the title as a heading — just write the body content directly."""

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=2500,
                reasoning_effort="low",
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            is_429 = "429" in str(e)
            if is_429 and attempt < max_retries:
                backoff = 2 ** attempt
                print(f"    [RATE LIMIT] Attempt {attempt}/{max_retries} failed, retrying in {backoff}s…")
                time.sleep(backoff)
                continue
            raise


def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set. Add it to backend/.env")
        sys.exit(1)

    client = Groq(api_key=api_key)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    documents = []
    total = len(DOC_SPECS)
    print(f"[GENERATE] Generating {total} documents via Groq ({MODEL})…\n")

    for i, spec in enumerate(DOC_SPECS, 1):
        print(f"  [{i:02d}/{total}] {spec['doc_id']} – {spec['title']}")
        try:
            content = generate_doc_content(client, spec)
            if not content:
                print(f"    [SKIP] Empty content for {spec['doc_id']} — skipping")
                continue
            documents.append({
                "doc_id": spec["doc_id"],
                "access_level": spec["access_level"],
                "category": spec["category"],
                "title": spec["title"],
                "content": content,
            })
        except Exception as e:
            print(f"    [ERROR] Failed: {e} — skipping")
        time.sleep(2)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)

    print(f"\n[GENERATE] Done. Saved {len(documents)} documents to:\n  {OUTPUT_PATH}")

    if len(documents) < 50:
        print(f"\n[FATAL ERROR] Only {len(documents)} documents were saved (minimum required: 50). Aborting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
