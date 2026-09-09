import os
import uuid
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

from config import CHROMA_PERSIST, EMBEDDING_MODEL, RAG_TOP_K

_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
_chroma: Optional[chromadb.PersistentClient] = None
_collection = None


def _get_collection():
    global _chroma, _collection
    if _collection is None:
        os.makedirs(CHROMA_PERSIST, exist_ok=True)
        _chroma = chromadb.PersistentClient(path=CHROMA_PERSIST)
        _collection = _chroma.get_or_create_collection(name="nexusmind_enterprise_knowledge", embedding_function=_ef, metadata={"hnsw:space": "cosine"})
    return _collection


def ingest(text: str, metadata: dict | None = None) -> str:
    col = _get_collection()
    doc_id = str(uuid.uuid4())
    metadata = dict(metadata or {})
    metadata.setdefault("tenant_id", "default")
    metadata.setdefault("role", "")
    metadata.setdefault("source", "enterprise")
    col.add(documents=[text], metadatas=[metadata], ids=[doc_id])
    return doc_id


def retrieve_user_data(query: str, role: str | None = None, tenant_id: str = "default", top_k: int = RAG_TOP_K) -> str:
    col = _get_collection()
    if col.count() == 0:
        return "No authorized enterprise knowledge has been stored yet."
    where = {"$and": [{"tenant_id": tenant_id}, {"role": role}]} if role else {"tenant_id": tenant_id}
    results = col.query(query_texts=[query], n_results=min(top_k, col.count()), where=where, include=["documents", "metadatas", "distances"])
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    if not docs:
        return "No authorized enterprise knowledge matched the query."
    return "\n\n".join(f"[{i}] ({meta.get('source', 'enterprise')})\n{doc[:1200]}" for i, (doc, meta) in enumerate(zip(docs, metas), 1))


def get_stats() -> dict:
    col = _get_collection()
    return {"provider": "chroma", "total_documents": col.count()}
