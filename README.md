# NexusMind — Enterprise Agentic AI + Governed RAG

Production-oriented enterprise AI platform for turning fragmented internal knowledge and trusted tools into **governed, auditable workflows**. The core engineering problem is not “build a chatbot”; it is how to move from an ambiguous user need to retrieved evidence, bounded agent/tool execution, evaluation, approval, audit, and deployment **without giving the model uncontrolled authority**.

The reference implementation uses **Microsoft Foundry, Azure OpenAI, Azure AI Search, RAG, multi-agent orchestration, tool calling, memory, evaluation, security, governance, APIs, CI/CD and containers**, with a local-development fallback so the architecture remains reproducible without claiming a live enterprise deployment.

## What it demonstrates
**ambiguous requirement → data/retrieval → agent workflow → tool/API integration → evaluation → security/governance → deployment → user feedback**

The forward-deployed view is documented in [`docs/CUSTOMER_DELIVERY_CASE.md`](docs/CUSTOMER_DELIVERY_CASE.md): discovery questions, architecture, rollout, success measures, failure modes, and scale decisions for a fictional regional enterprise.

### Portfolio scope
NexusMind and **NEXUS** in [`Gulf-Policy-Assistant`](https://github.com/hasan-rajab/Gulf-Policy-Assistant) are complementary rather than duplicate implementations. **NexusMind** concentrates on Microsoft/Azure agent orchestration, enterprise tool integration, and the customer-delivery path. **NEXUS** concentrates on authorization-before-retrieval, approval-gated side effects, audit integrity, and a Google Cloud/BigQuery architecture. Keeping the two separate makes the different control and cloud-design trade-offs inspectable.

## Microsoft AI architecture
- **Microsoft Foundry**: Foundry-native agents through Microsoft Agent Framework
- **Azure OpenAI**: production LLM + embedding provider
- **Azure AI Search**: hybrid keyword/vector enterprise retrieval with tenant/role filters
- **Microsoft Agent Framework**: primary multi-agent/Foundry production path
- **Semantic Kernel**: Microsoft agent interoperability adapter
- **AutoGen**: compatibility multi-agent implementation
- **Microsoft Copilot Studio**: OpenAPI-compatible action/connector surface via FastAPI `/openapi.json`

> AutoGen is retained because enterprise roles still request it; new production orchestration is centered on Microsoft Agent Framework.

## Capability map
| Requirement | NexusMind evidence |
|---|---|
| Generative AI / LLM applications | Provider-agnostic chat orchestration with Azure OpenAI support |
| RAG | Chroma local fallback + Azure AI Search production path |
| Embeddings / vector search | Azure OpenAI embeddings + Azure AI Search vector queries |
| AI agents | Foundry Agent Framework, Semantic Kernel and AutoGen adapters |
| Multi-agent workflows | AutoGen business-analyst + solution-architect team |
| Tool calling | Web search, governed RAG and enterprise REST connector |
| Agent memory | Session-scoped bounded conversation memory |
| Enterprise data/APIs | Allowlisted HTTPS connector + tenant-aware retrieval |
| Responsible AI | prompt-injection checks, abstention policy, human feedback |
| Security / governance | API-key option, tenant boundary, redaction, hash-chained audit |
| Evaluation | bilingual Arabic/English RAG regression harness |
| APIs | FastAPI + SSE streaming + generated OpenAPI |
| CI/CD | GitHub Actions compile + unit-test matrix |
| Containers | Dockerfile + Docker Compose |
| Cloud-native deployment | environment-driven Azure/local provider switching |

## Architecture
See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

```text
Client / Copilot Studio
        |
        v
   FastAPI API
        |
  Governance layer
        |
        v
 Agent Orchestrator
   |      |       |
   |      |       +--> Allowlisted enterprise APIs
   |      +----------> Azure AI Search / Chroma RAG
   +-----------------> Web search
        |
        v
Azure OpenAI / Microsoft Foundry
        |
        v
Memory + Audit + Evaluation
```

## Run locally
```bash
cp .env.example .env
# For local fallback set LLM_PROVIDER=groq and RAG_PROVIDER=chroma.
pip install -r requirements.txt
python main.py
```

## Install Microsoft AI stack
Python 3.10+:
```bash
pip install -r requirements.txt
pip install -r requirements-microsoft.txt
```

## Docker
```bash
docker compose up --build
```

## Key endpoints
| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | Runtime/provider capability report |
| POST | `/chat` | SSE agent chat with tools + session memory |
| POST | `/ingest` | Chroma or Azure AI Search ingestion |
| POST | `/feedback` | Human feedback / weakness capture |
| POST | `/memory/clear` | Explicit session-memory reset |
| POST | `/agents/foundry` | Microsoft Agent Framework + Foundry |
| POST | `/agents/semantic-kernel` | Semantic Kernel agent |
| POST | `/agents/autogen-team` | Multi-agent AutoGen workflow |
| GET | `/openapi.json` | Copilot Studio/custom connector contract |

## Evaluation
Run a deployment, seed it with a fictional evaluation corpus, then:
```bash
python -m evaluation.rag_eval
```
The harness reports observed metrics only; it does not hard-code performance claims.

## Security notes
This is a portfolio/reference architecture, not a substitute for an enterprise security review. For production prefer Microsoft Entra ID / managed identity, API Management, private networking where required, filterable tenant/role fields in Azure AI Search, content-safety policies, and human approval for write-capable enterprise actions.

## Customer delivery case
For the forward-deployed/customer-engineering view of this system, see [`docs/CUSTOMER_DELIVERY_CASE.md`](docs/CUSTOMER_DELIVERY_CASE.md). It walks from ambiguous customer problem and discovery questions through architecture, rollout, measurable success criteria, failure modes, and scale decisions without claiming a fictional production customer deployment.
