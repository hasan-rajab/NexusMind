# NexusMind deployment

Status: deployment configuration prepared; no live deployment has been verified.

Deploy the `codex/data-analytics-evidence-2026-10-05` branch using the root
Dockerfile and `railway.json`. One Uvicorn worker serves the original frontend,
streaming chat, retrieval and governed agent endpoints.

## Required service settings

| Variable | Value or purpose |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `REQUIRE_API_KEY` | `true` |
| `NEXUSMIND_API_KEY` | Generated random secret, at least 32 characters |
| `LLM_PROVIDER` | `groq` or `azure_openai` |
| `GROQ_API_KEY` | Real provider key for the Groq profile |
| `ALLOWED_ORIGINS` | Exact deployed HTTPS origin |
| `RAG_PROVIDER` | `chroma` or `azure_search` |
| `CHROMA_PERSIST` | `/app/data/nexusmind_chroma` for Chroma |
| `AUDIT_LOG_PATH` | `/app/data/audit.jsonl` |
| `NEXUSMIND_LOG_DIR` | `/app/data/logs` |
| `RAILWAY_RUN_UID` | `0` for volume initialization; the entrypoint then drops to UID 10001 |

For Azure OpenAI, provide `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` and
`AZURE_OPENAI_DEPLOYMENT` instead of a Groq key. Azure Search also requires
`AZURE_SEARCH_ENDPOINT` and `AZURE_SEARCH_API_KEY`.

Store keys in the host's secret settings. The frontend's **Access key** button
accepts the application key in page memory only. Provider keys remain on the
server. Chat, feedback, ingestion, memory, agent endpoints and statistics
require the application key. Health and readiness disclose no credentials.

Attach a volume at `/app/data` for Chroma, audit logs, feedback and optional
telemetry. Session conversation memory remains bounded and process-local;
it resets on restart. Keep one worker and one replica for this profile.

Optional real telemetry uses `NEXUS_ANALYTICS_DB=/app/data/analytics.sqlite`
and a separate generated `NEXUS_ANALYTICS_KEY` of at least 32 characters.
The browser supplies a page session ID. Telemetry stores pseudonymous event
identifiers; it does not store prompts in the analytics database. Application
interaction logs do contain conversation content and remain behind the key.
The committed A/B dashboard remains a labelled synthetic experiment; it is
not evidence of production uplift or a live treatment assignment.

## Readiness and validation

Production startup rejects missing application authentication, missing provider
settings, invalid origins and incomplete telemetry settings. Chroma initializes
at startup for that profile; Azure-only imports do not initialize Chroma.
`/ready` returns HTTP 503 until initialization succeeds. This check establishes
local initialization, not that a remote provider key is valid.

Verify `/ready`, unauthorized HTTP 401 responses, then an authenticated
streaming chat and document ingestion/retrieval. Verify restart persistence of
the mounted data. Record the actual image commit and enabled provider before
claiming a live deployment. The real provider key is still required.
