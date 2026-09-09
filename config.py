import os

def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}

# ── Runtime / provider selection ─────────────────────────────────────────────
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq").strip().lower()
RAG_PROVIDER = os.environ.get("RAG_PROVIDER", "chroma").strip().lower()
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
REQUIRE_API_KEY = _bool("REQUIRE_API_KEY", False)
NEXUSMIND_API_KEY = os.environ.get("NEXUSMIND_API_KEY", "")

# ── Groq fallback / local-development provider ────────────────────────────────
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ── Microsoft Azure OpenAI ────────────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_MODEL = os.environ.get("AZURE_OPENAI_MODEL", AZURE_OPENAI_DEPLOYMENT or "gpt-4o")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")

# ── Microsoft Foundry / Agent Framework ──────────────────────────────────────
FOUNDRY_PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
FOUNDRY_MODEL = os.environ.get("FOUNDRY_MODEL", AZURE_OPENAI_MODEL)

# ── Azure AI Search ───────────────────────────────────────────────────────────
AZURE_SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_API_KEY = os.environ.get("AZURE_SEARCH_API_KEY", "")
AZURE_SEARCH_INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME", "nexusmind-enterprise")
AZURE_SEARCH_SEMANTIC_CONFIG = os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIG", "")
AZURE_SEARCH_VECTOR_FIELD = os.environ.get("AZURE_SEARCH_VECTOR_FIELD", "content_vector")
AZURE_SEARCH_CONTENT_FIELD = os.environ.get("AZURE_SEARCH_CONTENT_FIELD", "content")
AZURE_SEARCH_ID_FIELD = os.environ.get("AZURE_SEARCH_ID_FIELD", "id")

# ── Web Search ────────────────────────────────────────────────────────────────
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TAVILY_SEARCH_DEPTH = os.environ.get("TAVILY_SEARCH_DEPTH", "basic")
TAVILY_MAX_RESULTS = int(os.environ.get("TAVILY_MAX_RESULTS", "5"))

# ── Local RAG fallback ────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHROMA_PERSIST = os.environ.get("CHROMA_PERSIST", "./data/nexusmind_chroma")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "5"))

# ── Agent memory / safety / governance ───────────────────────────────────────
MEMORY_MAX_TURNS = int(os.environ.get("MEMORY_MAX_TURNS", "12"))
REQUEST_MAX_CHARS = int(os.environ.get("REQUEST_MAX_CHARS", "12000"))
AUDIT_LOG_PATH = os.environ.get("AUDIT_LOG_PATH", "./data/audit.jsonl")
ENTERPRISE_API_ALLOWLIST = [
    item.strip().lower()
    for item in os.environ.get("ENTERPRISE_API_ALLOWLIST", "").split(",")
    if item.strip()
]

# ── Roles ────────────────────────────────────────────────────────────────────
SUPPORTED_ROLES = [
    "assistant",
    "trainer",
    "researcher",
    "consultant",
    "business_analyst",
    "solution_architect",
]
DEFAULT_ROLE = "assistant"

# ── Server ───────────────────────────────────────────────────────────────────
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
ALLOWED_ORIGINS = [
    item.strip()
    for item in os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
    if item.strip()
]
