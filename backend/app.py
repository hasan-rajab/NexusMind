"""
NexusMind FastAPI Backend
─────────────────────────
Routes:
  GET  /           → serves chat UI
  POST /chat       → SSE streaming chat endpoint
  POST /ingest     → add text to the personal RAG store
  GET  /stats      → RAG store statistics
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
from tools.rag import ingest, get_stats

app = FastAPI(title="NexusMind", version="0.1.0")

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
    return {"status": "ok", "model": "llama-3.1-8b-instant"}


@app.get("/stats")
async def stats():
    return get_stats()


@app.post("/chat")
async def chat(request: Request):
    body    = await request.json()
    query   = body.get("query", "").strip()
    role    = body.get("role", "assistant")
    history = body.get("history", [])

    if not query:
        return {"error": "query is required"}

    async def event_stream():
        try:
            async for chunk in orchestrator.stream(query, role, history):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/ingest")
async def ingest_data(request: Request):
    body     = await request.json()
    text     = body.get("text", "").strip()
    metadata = body.get("metadata", {})

    if not text:
        return {"error": "text is required"}

    doc_id = ingest(text, metadata)
    return {"status": "ok", "id": doc_id}
