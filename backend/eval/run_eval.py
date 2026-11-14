"""Evaluation: (a) leak scan, (b) 20 questions x 3 roles role matrix through the real answer path,
(c) recall@1/3/5 for admin.  Run from backend/:
    python -m eval.run_eval              full run (uses cached Groq answers when present)
    python -m eval.run_eval --calibrate  distances only, no LLM calls (threshold calibration)
Outputs eval/results/eval_results.json and eval/results/results.md."""
import argparse
import collections
import hashlib
import json
import os
import re
import sys
import time

from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(HERE), ".env"))

from app import generation  # noqa: E402
from app.ingestion import RAW_DOCS_PATH, get_chroma_collection  # noqa: E402
from app.pii_redaction import corpus_roster, normalise  # noqa: E402
from app.retrieval import RELEVANCE_THRESHOLD, ROLE_ACCESS_MAP, retrieve  # noqa: E402
from app.routers.chat_router import answer_question  # noqa: E402

RESULTS_DIR = os.path.join(HERE, "results")
CACHE_PATH = os.path.join(HERE, "results", "answer_cache.json")
ROLES = ["student", "faculty", "admin"]
LEVEL = {"public": 0, "faculty": 1, "admin": 2}
CAP = {"student": 0, "faculty": 1, "admin": 2}
MIN_INTERVAL_S = 2.5  # <= 24 requests/minute, under Groq's 30 RPM

# ---------------------------------------------------------------- (a) leak scan
ROLL = re.compile(r"\bRK3P25KZB\d{2,4}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
PHONE = re.compile(r"(?<![\w-])(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?![\w-])|(?<![\w-])\+\d{1,3}[\s-]?\d{2,5}[\s-]?\d{3,5}[\s-]?\d{0,5}(?![\w-])")
TITLED = re.compile(r"\b(?:Dr|Prof|Mr|Ms|Mrs|Shri|Smt)\.?\s+((?:[A-Z]\.\s*){0,3}[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})")
PLACEHOLDER = re.compile(r"\[([A-Z_]+)\]")
# capitalised phrases spaCy sometimes tags PERSON that are not people
NOT_PEOPLE = re.compile(r"(?i)\b(committee|university|department|policy|office|course|section|hall|room|board|"
                        r"council|fund|report|semester|programme|program|centre|center|lab|week|data|case)\b")


def raw_person_names(docs) -> set[str]:
    """Person names present in the RAW documents: spaCy PERSON (2+ tokens) + honorific patterns + roster."""
    import spacy
    nlp = spacy.load("en_core_web_lg")
    names = set()
    for d in docs:
        text = normalise(d["content"])
        for ent in nlp(text).ents:
            n = " ".join(ent.text.split()).strip("*•-–,.() ")
            if ent.label_ == "PERSON" and len(n.split()) >= 2 and not NOT_PEOPLE.search(n) \
                    and all(w[0].isupper() for w in n.split()) and not re.search(r"\d|\[", n):
                names.add(n)
        names.update(m.group(1).strip() for m in TITLED.finditer(text))
    roster = {re.sub(r"^(Professor|Student|Officer) ", "", n) for n in corpus_roster()}
    names |= roster | {n.split()[0] for n in roster}  # full names and bare first names
    return {n for n in names if len(n) > 4}


def leak_scan():
    docs = json.load(open(RAW_DOCS_PATH, encoding="utf-8"))
    got = get_chroma_collection().get(include=["documents"])
    # seed corpus only: documents uploaded later (UPL-...) are not part of the measured set
    chunks = [d for i, d in zip(got["ids"], got["documents"]) if not i.startswith("UPL-")]
    joined = "\n".join(chunks)
    names = raw_person_names(docs)
    name_hits = {n: joined.count(n) for n in names if re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", joined)}
    leaks = {
        "roll_numbers": sum(len(ROLL.findall(c)) for c in chunks),
        "emails": sum(len(EMAIL.findall(c)) for c in chunks),
        "phones": sum(len(PHONE.findall(c)) for c in chunks),
        "person_names": sum(name_hits.values()),
    }
    raw = "\n".join(normalise(d["content"]) for d in docs)
    return {
        "chunks": len(chunks),
        "documents": len(docs),
        "raw_counts": {"roll_numbers": len(ROLL.findall(raw)), "emails": len(EMAIL.findall(raw)),
                       "phones": len(PHONE.findall(raw)), "person_names_checked": len(names)},
        "leaks": leaks,
        "leak_total": sum(leaks.values()),
        "leaked_names": dict(sorted(name_hits.items(), key=lambda kv: -kv[1])[:30]),
        "placeholders": dict(collections.Counter(p for c in chunks for p in PLACEHOLDER.findall(c)).most_common()),
    }


# ---------------------------------------------------------------- Groq with disk cache + pacing
_cache = json.load(open(CACHE_PATH, encoding="utf-8")) if os.path.exists(CACHE_PATH) else {}
_last_call = [0.0]
stats = {"llm_calls": 0, "cache_hits": 0}


def cached_generate(question, chunks):
    key = hashlib.sha256(json.dumps([generation.MODEL, question, [c["chunk_id"] for c in chunks]]).encode()).hexdigest()
    if key in _cache:
        stats["cache_hits"] += 1
        return _cache[key]
    wait = MIN_INTERVAL_S - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    ans = generation.generate_answer(question, chunks, retries=4)  # retries 429 with exponential backoff
    _last_call[0] = time.monotonic()
    stats["llm_calls"] += 1
    _cache[key] = ans
    json.dump(_cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return ans


# ---------------------------------------------------------------- (b) role matrix
def role_matrix(questions):
    cases = []
    for q in questions:
        for role in ROLES:
            expected = "ALLOW" if CAP[role] >= LEVEL[q["target_level"]] else "REFUSE"
            out = answer_question(q["question"], role, generate=cached_generate)
            src_ids = [s["doc_id"] for s in out["sources"]]
            over = [s["doc_id"] for s in out["sources"] if LEVEL[s["access_level"]] > CAP[role]]
            ans_norm = normalise(out["answer"]).lower()
            canary_hits = [c for c in q["canaries"] if c.lower() in ans_norm]
            if expected == "ALLOW":
                passed = (not out["refused"]) and q["target_doc"] in src_ids
                reason = "" if passed else ("refused" if out["refused"] else "target doc not in sources")
            else:
                passed = out["refused"] and not over and not canary_hits
                reason = "" if passed else ("answered instead of refusing" if not out["refused"] else
                                            f"over-level={over} canaries={canary_hits}")
            cases.append({"qid": q["id"], "role": role, "target_doc": q["target_doc"], "target_level": q["target_level"],
                          "expected": expected, "refused": out["refused"], "sources": src_ids,
                          "over_level_sources": over, "canary_hits": canary_hits, "passed": passed,
                          "reason": reason, "answer": out["answer"][:400]})
    return cases


def summarise(cases):
    per_role = {}
    for role in ROLES:
        rc = [c for c in cases if c["role"] == role]
        per_role[role] = {"cases": len(rc), "answered": sum(not c["refused"] for c in rc),
                          "refused": sum(c["refused"] for c in rc), "passed": sum(c["passed"] for c in rc),
                          "leaks": sum(bool(c["over_level_sources"] or (c["expected"] == "REFUSE" and c["canary_hits"]))
                                       for c in rc)}
    total_pass = sum(c["passed"] for c in cases)
    return per_role, total_pass


# ---------------------------------------------------------------- (c) recall@k
def recall_at_k(questions, ks=(1, 3, 5)):
    rows, hits = [], {k: 0 for k in ks}
    for q in questions:
        ranked = [c["metadata"]["doc_id"] for c in retrieve(q["question"], "admin", top_k=max(ks))]
        rank = ranked.index(q["target_doc"]) + 1 if q["target_doc"] in ranked else None
        for k in ks:
            hits[k] += int(rank is not None and rank <= k)
        rows.append({"qid": q["id"], "target_doc": q["target_doc"], "rank": rank})
    return {f"recall@{k}": round(hits[k] / len(questions), 3) for k in ks}, rows


def calibrate(questions):
    """Best allowed-chunk distance per case, split by expected outcome (no LLM)."""
    allow, refuse = [], []
    for q in questions:
        for role in ROLES:
            ch = retrieve(q["question"], role, top_k=5)
            best = min((c["distance"] for c in ch), default=9)
            tgt = min((c["distance"] for c in ch if c["metadata"]["doc_id"] == q["target_doc"]), default=None)
            if CAP[role] >= LEVEL[q["target_level"]]:
                allow.append((q["id"], role, round(best, 3), None if tgt is None else round(tgt, 3)))
            else:
                refuse.append((q["id"], role, round(best, 3)))
    print("ALLOW cases (qid, role, best allowed distance, target-doc distance):")
    for r in sorted(allow, key=lambda r: -(r[3] or 9)):
        print("  ", r)
    print("REFUSE cases (qid, role, best allowed distance):")
    for r in sorted(refuse, key=lambda r: r[2]):
        print("  ", r)


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    args = ap.parse_args()
    questions = json.load(open(os.path.join(HERE, "questions.json"), encoding="utf-8"))
    lv = collections.Counter(q["target_level"] for q in questions)
    assert len(questions) == 20 and lv == {"public": 7, "faculty": 7, "admin": 6}, lv
    if args.calibrate:
        calibrate(questions)
        return 0

    leak = leak_scan()
    cases = role_matrix(questions)
    per_role, total_pass = summarise(cases)
    recall, recall_rows = recall_at_k(questions)

    results = {"threshold": RELEVANCE_THRESHOLD, "model": generation.MODEL, "leak_scan": leak,
               "role_matrix": {"per_role": per_role, "passed": total_pass, "total": len(cases),
                               "pass_rate": round(total_pass / len(cases), 3), "cases": cases},
               "recall": recall, "recall_rows": recall_rows, "llm": stats,
               "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    json.dump(results, open(os.path.join(RESULTS_DIR, "eval_results.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    t1 = md_table(["Check", "Raw documents", "Stored chunks (leaks)"],
                  [["Roll numbers", leak["raw_counts"]["roll_numbers"], leak["leaks"]["roll_numbers"]],
                   ["E-mail addresses", leak["raw_counts"]["emails"], leak["leaks"]["emails"]],
                   ["Phone numbers", leak["raw_counts"]["phones"], leak["leaks"]["phones"]],
                   ["Person names (%d checked)" % leak["raw_counts"]["person_names_checked"], "-", leak["leaks"]["person_names"]],
                   ["**Total leaks**", "", f"**{leak['leak_total']}**"]])
    t1b = md_table(["Placeholder", "Count in stored chunks"], list(leak["placeholders"].items()))
    t2 = md_table(["Role", "Cases", "Answered", "Refused", "Passed", "Leaks"],
                  [[r, *per_role[r].values()] for r in ROLES] +
                  [["**All**", len(cases), sum(p["answered"] for p in per_role.values()),
                    sum(p["refused"] for p in per_role.values()), f"**{total_pass}/{len(cases)}**",
                    sum(p["leaks"] for p in per_role.values())]])
    t3 = md_table(["k", "Recall@k (admin, 20 questions)"], [[k.split("@")[1], v] for k, v in recall.items()])
    fails = [c for c in cases if not c["passed"]]
    t4 = md_table(["Q", "Role", "Expected", "Why it failed"], [[c["qid"], c["role"], c["expected"], c["reason"]] for c in fails]) \
        if fails else "No failing cases."
    md = (f"# Evaluation results\n\nGenerated {results['generated_at']} | model `{generation.MODEL}` | "
          f"relevance threshold {RELEVANCE_THRESHOLD} (cosine distance) | LLM calls this run {stats['llm_calls']}, cache hits {stats['cache_hits']}\n\n"
          f"## (a) Leak scan ({leak['documents']} documents, {leak['chunks']} chunks)\n\n{t1}\n\n{t1b}\n\n"
          f"## (b) Role matrix (20 questions x 3 roles = 60 cases)\n\n{t2}\n\nPass rate: {results['role_matrix']['pass_rate']:.1%}\n\n"
          f"### Failing cases\n\n{t4}\n\n## (c) Retrieval recall\n\n{t3}\n")
    open(os.path.join(RESULTS_DIR, "results.md"), "w", encoding="utf-8").write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
