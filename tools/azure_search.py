"""Azure AI Search enterprise RAG adapter with hybrid vector + keyword search."""
from __future__ import annotations

import uuid

from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_ENDPOINT, AZURE_SEARCH_API_KEY, AZURE_SEARCH_CONTENT_FIELD, AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_ID_FIELD, AZURE_SEARCH_INDEX_NAME, AZURE_SEARCH_SEMANTIC_CONFIG, AZURE_SEARCH_VECTOR_FIELD, RAG_TOP_K


def _search_client():
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
    if not (AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY):
        raise RuntimeError("Azure AI Search endpoint/key are not configured")
    return SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=AZURE_SEARCH_INDEX_NAME, credential=AzureKeyCredential(AZURE_SEARCH_API_KEY))


def _embedding(text: str) -> list[float]:
    if not (AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY and AZURE_OPENAI_EMBEDDING_DEPLOYMENT):
        raise RuntimeError("Azure OpenAI embedding deployment is not configured")
    from openai import AzureOpenAI
    client = AzureOpenAI(azure_endpoint=AZURE_OPENAI_ENDPOINT, api_key=AZURE_OPENAI_API_KEY, api_version=AZURE_OPENAI_API_VERSION)
    response = client.embeddings.create(model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT, input=text)
    return response.data[0].embedding


def upsert_document(text: str, metadata: dict | None = None) -> str:
    metadata = metadata or {}
    doc_id = metadata.get("id") or str(uuid.uuid4())
    document = {AZURE_SEARCH_ID_FIELD: doc_id, AZURE_SEARCH_CONTENT_FIELD: text, AZURE_SEARCH_VECTOR_FIELD: _embedding(text), "source": metadata.get("source", "enterprise"), "role": metadata.get("role", ""), "tenant_id": metadata.get("tenant_id", "default")}
    _search_client().merge_or_upload_documents([document])
    return doc_id


def retrieve(query: str, role: str | None = None, tenant_id: str = "default", top_k: int = RAG_TOP_K) -> str:
    from azure.search.documents.models import VectorizedQuery
    safe_tenant = tenant_id.replace("'", "''")
    filters = [f"tenant_id eq '{safe_tenant}'"]
    if role:
        safe_role = role.replace("'", "''")
        filters.append(f"role eq '{safe_role}'")
    vector_query = VectorizedQuery(vector=_embedding(query), k_nearest_neighbors=top_k, fields=AZURE_SEARCH_VECTOR_FIELD)
    kwargs = {"search_text": query, "vector_queries": [vector_query], "filter": " and ".join(filters), "top": top_k, "select": [AZURE_SEARCH_ID_FIELD, AZURE_SEARCH_CONTENT_FIELD, "source", "role", "tenant_id"]}
    if AZURE_SEARCH_SEMANTIC_CONFIG:
        kwargs.update({"query_type": "semantic", "semantic_configuration_name": AZURE_SEARCH_SEMANTIC_CONFIG})
    results = list(_search_client().search(**kwargs))
    if not results:
        return "No authorized enterprise knowledge matched the query."
    return "\n\n".join(f"[{i}] ({result.get('source', 'enterprise')})\n{result.get(AZURE_SEARCH_CONTENT_FIELD, '')[:1200]}" for i, result in enumerate(results, 1))
