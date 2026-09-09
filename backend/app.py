"""NexusMind enterprise FastAPI service."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

import orchestrator
from config import ALLOWED_ORIGINS, ENVIRONMENT, LLM_PROVIDER, RAG_PROVIDER, REQUIRE_API_KEY
from governance import audit_event, validate_user_input, verify_api_key
from logger import flag_weakness, get_stats as log_stats, load_weaknesses, log_interaction
from memory import clear_memory, stats as memory_stats
from tools.rag import get_stats as rag_stats, ingest

app = FastAPI(title="NexusMind Enterprise Agentic AI", version="1.0.0", description="Governed enterprise RAG and agentic AI service with Microsoft Foundry, Azure OpenAI, Azure AI Search, multi-agent orchestration and evaluation.")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Tenant-ID"])
FRONTEND_PATH = Path(__file__).parent.parent / "frontend" / "index.html"


def _authorize(api_key: str | None) -> None:
    if REQUIRE_API_KEY and not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="invalid API key")


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(FRONTEND_PATH.read_text())


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "environment": ENVIRONMENT, "llm_provider": LLM_PROVIDER, "rag_provider": RAG_PROVIDER, "capabilities": ["rag", "tool_calling", "session_memory", "multi_agent", "evaluation", "audit_logging"]}


@app.get("/stats")
async def stats():
    return {"rag": rag_stats() if RAG_PROVIDER == "chroma" else {"provider": RAG_PROVIDER}, "logs": log_stats(), "memory": memory_stats()}


@app.get("/weaknesses")
async def weaknesses(x_api_key: str | None = Header(default=None)):
    _authorize(x_api_key)
    return {"weaknesses": load_weaknesses()}


@app.post("/chat")
async def chat(request: Request, x_api_key: str | None = Header(default=None), x_tenant_id: str = Header(default="default")):
    _authorize(x_api_key)
    body = await request.json()
    query = body.get("query", "").strip()
    role = body.get("role", "assistant")
    history = body.get("history", [])
    session_id = body.get("session_id")
    ok, reason = validate_user_input(query)
    if not ok:
        audit_event("request_blocked", {"reason": reason, "tenant_id": x_tenant_id})
        raise HTTPException(status_code=400, detail=reason)

    async def event_stream():
        full_response: list[str] = []
        turn_id = None
        tools_used: list[str] = []
        try:
            async for item in orchestrator.stream(query, role, history, session_id=session_id, tenant_id=x_tenant_id):
                if "turn_id" in item:
                    turn_id = item["turn_id"]
                    yield f"data: {json.dumps(item)}\n\n"
                elif "tools_used" in item:
                    tools_used = item["tools_used"]
                    yield f"data: {json.dumps(item)}\n\n"
                elif "chunk" in item:
                    full_response.append(item["chunk"])
                    yield f"data: {json.dumps(item)}\n\n"
        except Exception:
            audit_event("agent_turn_failed", {"turn_id": turn_id or "unknown", "tenant_id": x_tenant_id})
            yield f"data: {json.dumps({'error': 'agent request failed'})}\n\n"
        finally:
            if turn_id:
                log_interaction(turn_id=turn_id, role=role, user_query=query, assistant_response="".join(full_response), tools_used=tools_used)
            yield "data: [DONE]\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/memory/clear")
async def clear_session_memory(request: Request, x_api_key: str | None = Header(default=None)):
    _authorize(x_api_key)
    body = await request.json()
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    clear_memory(session_id)
    audit_event("memory_cleared", {"session_id": session_id})
    return {"status": "cleared", "session_id": session_id}


@app.post("/feedback")
async def feedback(request: Request, x_api_key: str | None = Header(default=None)):
    _authorize(x_api_key)
    body = await request.json()
    required = ["turn_id", "role", "user_query", "bad_response", "ideal_response", "weakness_type"]
    missing = [key for key in required if not body.get(key)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing fields: {missing}")
    flag_weakness(turn_id=body["turn_id"], role=body["role"], user_query=body["user_query"], bad_response=body["bad_response"], ideal_response=body["ideal_response"], weakness_type=body["weakness_type"], notes=body.get("notes", ""))
    audit_event("human_feedback_recorded", {"turn_id": body["turn_id"], "weakness_type": body["weakness_type"]})
    return {"status": "flagged", "turn_id": body["turn_id"]}


@app.post("/ingest")
async def ingest_data(request: Request, x_api_key: str | None = Header(default=None), x_tenant_id: str = Header(default="default")):
    _authorize(x_api_key)
    body = await request.json()
    text = body.get("text", "").strip()
    metadata = body.get("metadata", {})
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    metadata["tenant_id"] = x_tenant_id
    if RAG_PROVIDER == "azure_search":
        from tools.azure_search import upsert_document
        doc_id = upsert_document(text, metadata)
    else:
        doc_id = ingest(text, metadata)
    audit_event("knowledge_ingested", {"id": doc_id, "tenant_id": x_tenant_id, "source": metadata.get("source", "")})
    return {"status": "ok", "id": doc_id, "provider": RAG_PROVIDER}


@app.post("/agents/foundry")
async def foundry_agent(request: Request, x_api_key: str | None = Header(default=None)):
    _authorize(x_api_key)
    from agents.foundry_agent import run_foundry_agent
    task = (await request.json()).get("task", "").strip()
    ok, reason = validate_user_input(task)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return {"framework": "microsoft-agent-framework", "result": await run_foundry_agent(task)}


@app.post("/agents/autogen-team")
async def autogen_team(request: Request, x_api_key: str | None = Header(default=None)):
    _authorize(x_api_key)
    from agents.autogen_team import run_autogen_team
    task = (await request.json()).get("task", "").strip()
    ok, reason = validate_user_input(task)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return {"framework": "autogen", "result": await run_autogen_team(task)}


@app.post("/agents/semantic-kernel")
async def semantic_kernel_agent(request: Request, x_api_key: str | None = Header(default=None)):
    _authorize(x_api_key)
    from agents.semantic_kernel_agent import run_semantic_kernel_agent
    task = (await request.json()).get("task", "").strip()
    ok, reason = validate_user_input(task)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    return {"framework": "semantic-kernel", "result": await run_semantic_kernel_agent(task)}
