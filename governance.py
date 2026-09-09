"""Responsible-AI and enterprise-governance utilities."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import AUDIT_LOG_PATH, NEXUSMIND_API_KEY, REQUEST_MAX_CHARS

_SECRET_PATTERNS = [re.compile(r"(?i)(api[_-]?key|authorization|bearer|secret|password)\s*[:=]\s*([^\s,;]+)")]
_PROMPT_INJECTION_MARKERS = ("ignore previous instructions", "ignore all previous instructions", "reveal the system prompt", "show me your system prompt", "print your hidden instructions")


def validate_user_input(text: str) -> tuple[bool, str | None]:
    text = (text or "").strip()
    if not text:
        return False, "query is required"
    if len(text) > REQUEST_MAX_CHARS:
        return False, f"query exceeds {REQUEST_MAX_CHARS} characters"
    lowered = text.lower()
    if any(marker in lowered for marker in _PROMPT_INJECTION_MARKERS):
        return False, "request blocked by prompt-injection policy"
    return True, None


def redact_secrets(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]", redacted)
    return redacted


def verify_api_key(candidate: str | None) -> bool:
    if not NEXUSMIND_API_KEY:
        return True
    return bool(candidate) and hmac.compare_digest(candidate, NEXUSMIND_API_KEY)


def _last_hash(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return "GENESIS"
    try:
        last = path.read_text(encoding="utf-8").strip().splitlines()[-1]
        return json.loads(last).get("event_hash", "GENESIS")
    except Exception:
        return "GENESIS"


def audit_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    path = Path(AUDIT_LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": event_type, "payload": {k: redact_secrets(str(v)) if isinstance(v, str) else v for k, v in payload.items()}, "previous_hash": _last_hash(path)}
    canonical = json.dumps(event, sort_keys=True, ensure_ascii=False).encode("utf-8")
    event["event_hash"] = hashlib.sha256(canonical).hexdigest()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + os.linesep)
    return event
