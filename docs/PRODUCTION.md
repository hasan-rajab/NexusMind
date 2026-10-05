# NexusMind deployment

Status: live on Railway. Authenticated streaming chat, real document retrieval
and persistence across redeployment have been verified.

Application: https://nexusmind-production-3da9.up.railway.app

The verified runtime is deployed at commit
`144892922af516cb42357b3da938fcb51d4d1731`, using Groq
`openai/gpt-oss-20b` and local Chroma storage. The earlier default Llama model
was not available to the hosting account's key; the explicit `GROQ_MODEL`
setting selects the verified replacement. Select a model available to your
own provider account when deploying elsewhere.

To use the application, retrieve `NEXUSMIND_API_KEY` from the Railway
`nexusmind` service variables and enter it through the frontend's **Access
key** button. This is the application access key; the Groq provider key
remains on the server.

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
| `GROQ_MODEL` | `openai/gpt-oss-20b` in the verified hosted profile |
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
claiming a live deployment.

Live verification on 5 October 2026 confirmed HTTPS frontend, health and
readiness responses of 200, unauthorized chat/statistics responses of 401,
authenticated ingestion and completed provider-backed streaming chat. The
retrieval test used a clearly labelled synthetic fixture in an isolated QA
tenant: the model called enterprise retrieval, returned the stored assessment
code and cited its source. The same fixture remained retrievable after
redeployment with the persistent volume mounted.

The verified profile covers Groq chat and Chroma retrieval. Other provider
and agent integrations need their own documented credentials. The separate
committed A/B dashboard remains a synthetic analytics demonstration.

Railway deployments currently pin a tested commit explicitly; automatic
GitHub push triggers are not configured. Keep the PR unmerged until reviewed.
