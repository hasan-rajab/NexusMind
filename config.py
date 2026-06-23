import os

# ── LLM ──────────────────────────────────────────────────────────────────────
GROQ_MODEL       = "llama-3.1-8b-instant"
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")

# ── Search ────────────────────────────────────────────────────────────────────
TAVILY_API_KEY      = os.environ.get("TAVILY_API_KEY", "")
TAVILY_SEARCH_DEPTH = "basic"
TAVILY_MAX_RESULTS  = 5

# ── RAG ───────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"
CHROMA_PERSIST    = "/kaggle/working/nexusmind_chroma"
RAG_TOP_K         = 5

# ── Roles ─────────────────────────────────────────────────────────────────────
SUPPORTED_ROLES = ["assistant", "trainer", "researcher", "consultant"]
DEFAULT_ROLE    = "assistant"

# ── Server ────────────────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000
