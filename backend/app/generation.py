import os
from groq import Groq

_client = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        _client = Groq(api_key=api_key)
    return _client


MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are a helpful assistant for a university information system.
You answer questions ONLY using the context documents provided below.
Each context chunk comes from an internal university document.

Rules:
- If the provided context is empty or does not contain enough information to answer the question, respond with exactly: "I don't have access to information that would answer this question."
- Do NOT hallucinate, invent, or add information beyond what is in the context.
- Do NOT reveal or reconstruct any redacted PII markers like [PERSON], [STUDENT_ID], [EMAIL_ADDRESS], etc. — treat them as opaque placeholders.
- Be concise and factual.
- If multiple chunks are relevant, synthesize them into a single coherent answer."""


def generate_answer(question: str, chunks: list[dict]) -> str:
    client = get_groq_client()

    if not chunks:
        context_text = "(No relevant documents found for your access level.)"
    else:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            title = meta.get("title", "Unknown")
            access = meta.get("access_level", "unknown")
            parts.append(f"[Document {i}: {title} (access: {access})]\n{chunk['text']}")
        context_text = "\n\n---\n\n".join(parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context documents:\n\n{context_text}\n\n---\n\nQuestion: {question}",
        },
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()
