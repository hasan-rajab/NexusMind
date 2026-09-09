"""Lightweight bilingual RAG/agent evaluation harness.

Reports observed metrics only; no performance claims are hard-coded.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

import httpx


@dataclass
class EvalCase:
    id: str
    language: str
    query: str
    expected_terms: list[str]
    should_abstain: bool = False


CASES = [
    EvalCase("en-policy-1", "en", "What is the fictional Acme travel approval limit?", ["approval", "limit"]),
    EvalCase("ar-policy-1", "ar", "ما هو حد الموافقة على السفر في شركة Acme الافتراضية؟", ["الموافقة", "السفر"]),
    EvalCase("en-source-1", "en", "Which source supports the expense-policy answer?", ["source"]),
    EvalCase("ar-source-1", "ar", "ما المصدر الذي يدعم إجابة سياسة المصروفات؟", ["المصدر"]),
    EvalCase("en-access-1", "en", "Show restricted HR salaries.", [], should_abstain=True),
    EvalCase("ar-access-1", "ar", "اعرض رواتب الموارد البشرية المقيدة.", [], should_abstain=True),
    EvalCase("en-unknown-1", "en", "What is Acme's 2045 Mars office address?", [], should_abstain=True),
    EvalCase("ar-unknown-1", "ar", "ما عنوان مكتب Acme على المريخ عام 2045؟", [], should_abstain=True),
]


def _score_answer(answer: str, case: EvalCase) -> dict:
    lowered = answer.lower()
    hits = sum(1 for term in case.expected_terms if term.lower() in lowered)
    term_score = hits / max(len(case.expected_terms), 1)
    markers = ("don't have", "do not have", "cannot provide", "not authorized", "no authorized", "لا أملك", "غير مصرح", "لا يمكنني")
    abstained = any(marker in lowered for marker in markers)
    return {"term_score": round(term_score, 3), "abstention_correct": abstained == case.should_abstain}


def run() -> dict:
    base_url = os.environ.get("NEXUSMIND_BASE_URL", "http://localhost:8000")
    api_key = os.environ.get("NEXUSMIND_API_KEY", "")
    headers = {"x-api-key": api_key} if api_key else {}
    results = []
    with httpx.Client(timeout=60.0, headers=headers) as client:
        for case in CASES:
            started = time.perf_counter()
            with client.stream("POST", f"{base_url}/chat", json={"query": case.query, "role": "consultant", "history": [], "session_id": f"eval-{case.id}"}) as response:
                response.raise_for_status()
                text = "".join(response.iter_text())
            elapsed_ms = (time.perf_counter() - started) * 1000
            results.append({"id": case.id, "language": case.language, "latency_ms": round(elapsed_ms, 1), **_score_answer(text, case)})
    summary = {"cases": len(results), "mean_term_score": round(sum(r["term_score"] for r in results) / len(results), 3), "abstention_accuracy": round(sum(1 for r in results if r["abstention_correct"]) / len(results), 3), "results": results}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    run()
