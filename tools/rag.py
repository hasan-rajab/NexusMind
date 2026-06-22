import os
import uuid
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_PERSIST, EMBEDDING_MODEL, RAG_TOP_K

# ── Embedding function ────────────────────────────────────────────────────────
_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)

# ── ChromaDB client ───────────────────────────────────────────────────────────
_chroma: Optional[chromadb.PersistentClient] = None
_collection = None


def _get_collection():
    global _chroma, _collection
    if _collection is None:
        os.makedirs(CHROMA_PERSIST, exist_ok=True)
        _chroma = chromadb.PersistentClient(path=CHROMA_PERSIST)
        _collection = _chroma.get_or_create_collection(
            name="nexusmind_user_data",
            embedding_function=_ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# ── Public API ────────────────────────────────────────────────────────────────

def ingest(text: str, metadata: dict = None) -> str:
    """
    Add a text chunk to the vector store.
    metadata can include: role, source, date — used for role-scoped retrieval.
    """
    col = _get_collection()
    doc_id = str(uuid.uuid4())
    col.add(
        documents=[text],
        metadatas=[metadata or {}],
        ids=[doc_id],
    )
    return doc_id


def retrieve_user_data(query: str, role: str = None, top_k: int = RAG_TOP_K) -> str:
    """
    Retrieve the most relevant chunks from the user's personal knowledge base.
    Optionally scoped to a specific role.
    """
    col = _get_collection()

    if col.count() == 0:
        return "No personal data has been stored yet."

    where = {"role": role} if role else None

    try:
        results = col.query(
            query_texts=[query],
            n_results=min(top_k, col.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # If role filter returns nothing, fall back to unfiltered
        results = col.query(
            query_texts=[query],
            n_results=min(top_k, col.count()),
            include=["documents", "metadatas", "distances"],
        )

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    if not docs:
        return "No relevant personal data found."

    lines = []
    for i, (doc, meta) in enumerate(zip(docs, metas), 1):
        source = meta.get("source", "user note")
        lines.append(f"[{i}] ({source})\n{doc[:600]}")

    return "\n\n".join(lines)


def get_stats() -> dict:
    col = _get_collection()
    return {"total_documents": col.count()}
