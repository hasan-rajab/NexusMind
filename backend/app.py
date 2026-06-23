"""
NexusMind FastAPI Backend — Phase 2
─────────────────────────────────────
Routes:
  GET  /           → chat UI
  POST /chat       → SSE streaming chat (logs every turn)
  POST /feedback   → flag a turn as weak, store ideal response
  POST /ingest     → add text to personal RAG store
  GET  /stats      → combined RAG + log stats
  GET  /weaknesses → list all flagged turns (for dataset review)
  GET  /health     → health check
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

import orchestrator
from tools.rag import ingest, get_stats as rag_stats
from logger import log_interaction, flag_weakness, get_stats as log_stats, load_weaknesses

app = FastAPI(title="NexusMind", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = Path(__file__).parent.parent / "frontend" / "index.html"


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(FRONTEND_PATH.read_text())


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/stats")
async def stats():
    return {"rag": rag_stats(), "logs": log_stats()}


@app.get("/weaknesses")
async def weaknesses():
    return {"weaknesses": load_weaknesses()}


@app.post("/chat")
async def chat(request: Request):
    body    = await request.json()
    query   = body.get("query", "").strip()
    role    = body.get("role", "assistant")
    history = body.get("history", [])

    if not query:
        return {"error": "query is required"}

    async def event_stream():
        full_response = []
        turn_id       = None
        tools_used    = []

        try:
            async for item in orchestrator.stream(query, role, history):
                if "turn_id" in item:
                    turn_id = item["turn_id"]
                    yield f"data: {json.dumps({'turn_id': turn_id})}\n\n"

                elif "tools_used" in item:
                    tools_used = item["tools_used"]
                    yield f"data: {json.dumps({'tools_used': tools_used})}\n\n"

                elif "chunk" in item:
                    full_response.append(item["chunk"])
                    yield f"data: {json.dumps({'chunk': item['chunk']})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            # Log the completed turn
            if turn_id:
                log_interaction(
                    turn_id=turn_id,
                    role=role,
                    user_query=query,
                    assistant_response="".join(full_response),
                    tools_used=tools_used,
                )
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/feedback")
async def feedback(request: Request):
    """
    Flag a bad response for fine-tuning dataset curation.
    Body:
      turn_id        : str   — from the /chat SSE stream
      role           : str
      user_query     : str
      bad_response   : str
      ideal_response : str   — what the model SHOULD have said
      weakness_type  : str   — no_clarification | wrong_tone | skipped_tool |
                               hallucination | off_persona | other
      notes          : str   (optional)
    """
    body = await request.json()

    required = ["turn_id", "role", "user_query", "bad_response", "ideal_response", "weakness_type"]
    missing  = [k for k in required if not body.get(k)]
    if missing:
        return {"error": f"Missing fields: {missing}"}

    flag_weakness(
        turn_id=body["turn_id"],
        role=body["role"],
        user_query=body["user_query"],
        bad_response=body["bad_response"],
        ideal_response=body["ideal_response"],
        weakness_type=body["weakness_type"],
        notes=body.get("notes", ""),
    )
    return {"status": "flagged", "turn_id": body["turn_id"]}


@app.post("/ingest")
async def ingest_data(request: Request):
    body     = await request.json()
    text     = body.get("text", "").strip()
    metadata = body.get("metadata", {})
    if not text:
        return {"error": "text is required"}
    doc_id = ingest(text, metadata)
    return {"status": "ok", "id": doc_id}
