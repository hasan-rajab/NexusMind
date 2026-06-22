# ⚡ NexusMind

Multi-role AI assistant — Personal Assistant · Fitness Trainer · Research Partner · Consultant.

## Stack
- **LLM**: Llama 3.1 8B via Groq API (free, fast)
- **Web Search**: Tavily API
- **RAG**: ChromaDB + sentence-transformers
- **Backend**: FastAPI + SSE streaming
- **Frontend**: Vanilla JS dark UI (served by FastAPI)

## Kaggle Setup
1. Add Kaggle Secrets: `GROQ_API_KEY`, `TAVILY_API_KEY`, `NGROK_TOKEN`
2. Follow cells in `kaggle_setup.py`
3. Open the ngrok URL printed in Cell 5

## Project Structure
```
nexusmind/
├── config.py           # All settings & API keys
├── orchestrator.py     # Agent loop (tool-calling + streaming)
├── main.py             # Uvicorn entry point
├── roles/
│   └── personas.py     # System prompts per role
├── tools/
│   ├── web_search.py   # Tavily integration
│   └── rag.py          # ChromaDB ingest + retrieval
├── backend/
│   └── app.py          # FastAPI routes
├── frontend/
│   └── index.html      # Chat UI
└── kaggle_setup.py     # Notebook runner guide
```

## API Endpoints
| Method | Route | Description |
|---|---|---|
| GET | `/` | Chat UI |
| POST | `/chat` | SSE streaming chat |
| POST | `/ingest` | Add text to RAG store |
| GET | `/stats` | RAG store stats |
| GET | `/health` | Health check |

## Ingest personal data
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "My fitness goal is to hit 100kg deadlift by December.", "metadata": {"role": "trainer", "source": "user_goals"}}'
```

## Phase Roadmap
- **Phase 1** (current): Agent shell — tools + RAG + role switching ✅
- **Phase 2**: Identify weaknesses through real usage
- **Phase 3**: Curate multi-role fine-tuning dataset
- **Phase 4**: QLoRA fine-tune on Kaggle GPU
- **Phase 5**: Swap fine-tuned model into serving layer
