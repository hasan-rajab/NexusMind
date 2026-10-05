"""Fail closed when the deployed service lacks required production settings."""
from __future__ import annotations

import os
from collections.abc import Mapping
from urllib.parse import urlparse


def validate_production(env: Mapping[str, str] | None = None) -> None:
    env = os.environ if env is None else env
    if env.get("ENVIRONMENT", "development").lower() != "production":
        return
    errors = []
    if env.get("REQUIRE_API_KEY", "false").lower() not in {"true", "1", "yes", "on"}:
        errors.append("REQUIRE_API_KEY=true is required")
    key = env.get("NEXUSMIND_API_KEY", "")
    if len(key) < 32 or key.lower().startswith("change-me"):
        errors.append("NEXUSMIND_API_KEY must be a generated secret of at least 32 characters")
    provider = env.get("LLM_PROVIDER", "groq").lower()
    required = {"groq": ("GROQ_API_KEY",), "azure_openai": (
        "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT")}
    if provider not in required:
        errors.append("LLM_PROVIDER must be groq or azure_openai")
    else:
        errors.extend(f"{name} is required" for name in required[provider] if not env.get(name))
    rag = env.get("RAG_PROVIDER", "chroma").lower()
    if rag == "azure_search":
        errors.extend(f"{name} is required" for name in ("AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_API_KEY") if not env.get(name))
    elif rag != "chroma":
        errors.append("RAG_PROVIDER must be chroma or azure_search")
    origins = [s.strip() for s in env.get("ALLOWED_ORIGINS", "").split(",") if s.strip()]
    if not origins or any(urlparse(origin).scheme != "https" or not urlparse(origin).hostname for origin in origins):
        errors.append("ALLOWED_ORIGINS must contain explicit HTTPS origins")
    if env.get("NEXUS_ANALYTICS_DB") and len(env.get("NEXUS_ANALYTICS_KEY", "")) < 32:
        errors.append("NEXUS_ANALYTICS_KEY must contain at least 32 characters when telemetry is enabled")
    if errors:
        raise RuntimeError("Production configuration rejected: " + "; ".join(errors))
