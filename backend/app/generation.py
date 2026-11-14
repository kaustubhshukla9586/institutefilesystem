import os
import re
import time
from datetime import date

from groq import Groq, RateLimitError

_client = None
MODEL = os.getenv("GROQ_MODEL") or "openai/gpt-oss-20b"
NO_ANSWER = "NO_ANSWER"

SYSTEM_PROMPT = """You answer questions for staff and students of Thornwick University using ONLY the documents given.
Today's date is {today}.

Rules:
- If the documents do not contain the answer, reply with exactly: NO_ANSWER
- Answer in concise Markdown: a direct answer first, then short bullet points if useful. No headings longer than one line.
- Never output HTML.
- Do not say "according to the provided context", "the documents say", or similar. Just answer.
- Placeholders such as [PERSON], [STUDENT_ID], [EMAIL_ADDRESS], [PHONE_NUMBER], [LOCATION] are redacted values. Keep them as they are; never guess what they hide.
- Do not invent facts, numbers or dates."""


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        _client = Groq(api_key=key, max_retries=0)
    return _client


def build_messages(question: str, chunks: list[dict]) -> list[dict]:
    parts = [f"[{c['metadata'].get('title', 'Untitled')}]\n{c['text']}" for c in chunks]
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(today=date.today().isoformat())},
        {"role": "user", "content": "Documents:\n\n" + "\n\n---\n\n".join(parts) + f"\n\n---\n\nQuestion: {question}"},
    ]


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")  # no raw HTML ever reaches the client
    text = re.sub(r"(?i)^\s*(according to|based on) the (provided )?(context|documents?)[^,.:]*[,.:]\s*", "", text)
    return text.strip()


def generate_answer(question: str, chunks: list[dict], retries: int = 1) -> str:
    """Returns the cleaned answer, or NO_ANSWER when the model finds nothing relevant.
    Live queries retry a Groq 429 once (5 s) so users aren't left waiting; the eval passes retries=4."""
    client = get_groq_client()
    delay = 5.0
    for attempt in range(retries + 1):
        try:
            r = client.chat.completions.create(model=MODEL, messages=build_messages(question, chunks),
                                               temperature=0.1, max_tokens=700)
            return _clean(r.choices[0].message.content)
        except RateLimitError:
            if attempt == retries:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")
