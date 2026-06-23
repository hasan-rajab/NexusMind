"""
NexusMind Phase 2 — Interaction Logger
───────────────────────────────────────
Logs every conversation turn to JSONL.
Flagged (thumbs-down) turns are saved separately as fine-tuning candidates.
"""

import json
import os
import uuid
from datetime import datetime

LOG_DIR          = os.environ.get("NEXUSMIND_LOG_DIR", "/kaggle/working/nexusmind_logs")
INTERACTIONS_LOG = os.path.join(LOG_DIR, "interactions.jsonl")
WEAKNESSES_LOG   = os.path.join(LOG_DIR, "weaknesses.jsonl")

os.makedirs(LOG_DIR, exist_ok=True)


def _write(path: str, record: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_interaction(
    turn_id: str,
    role: str,
    user_query: str,
    assistant_response: str,
    tools_used: list[str] = None,
) -> str:
    record = {
        "turn_id":   turn_id,
        "timestamp": datetime.utcnow().isoformat(),
        "role":      role,
        "user":      user_query,
        "assistant": assistant_response,
        "tools_used": tools_used or [],
        "flagged":   False,
    }
    _write(INTERACTIONS_LOG, record)
    return turn_id


def flag_weakness(
    turn_id: str,
    role: str,
    user_query: str,
    bad_response: str,
    ideal_response: str,
    weakness_type: str,  # e.g. "no_clarification", "wrong_tone", "skipped_tool", "hallucination"
    notes: str = "",
):
    record = {
        "turn_id":        turn_id,
        "timestamp":      datetime.utcnow().isoformat(),
        "role":           role,
        "user":           user_query,
        "bad_response":   bad_response,
        "ideal_response": ideal_response,
        "weakness_type":  weakness_type,
        "notes":          notes,
    }
    _write(WEAKNESSES_LOG, record)


def get_stats() -> dict:
    def count_lines(path):
        if not os.path.exists(path):
            return 0
        with open(path) as f:
            return sum(1 for _ in f)

    weakness_types = {}
    if os.path.exists(WEAKNESSES_LOG):
        with open(WEAKNESSES_LOG) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    t = r.get("weakness_type", "unknown")
                    weakness_types[t] = weakness_types.get(t, 0) + 1
                except Exception:
                    pass

    return {
        "total_interactions": count_lines(INTERACTIONS_LOG),
        "total_weaknesses":   count_lines(WEAKNESSES_LOG),
        "weakness_breakdown": weakness_types,
    }


def load_weaknesses() -> list[dict]:
    if not os.path.exists(WEAKNESSES_LOG):
        return []
    records = []
    with open(WEAKNESSES_LOG) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
    return records


def load_interactions(limit: int = 100) -> list[dict]:
    if not os.path.exists(INTERACTIONS_LOG):
        return []
    records = []
    with open(INTERACTIONS_LOG) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
    return records[-limit:]
