# NexusMind — Enterprise Agentic AI on Microsoft/Azure

**A governed agentic-AI reference platform for turning fragmented enterprise knowledge and trusted tools into auditable workflows.**

NexusMind is designed around a customer-delivery problem:

> **How do you move from an ambiguous business request to retrieved evidence, bounded tool use, human-governed execution and measurable outcomes without giving the model uncontrolled authority?**

The project demonstrates the Microsoft/Azure path for that problem using Microsoft Foundry, Azure OpenAI, Azure AI Search, multi-agent orchestration, governed tool calling, memory, evaluation, APIs, CI/CD and containers.

> **Scope:** this is a portfolio/reference architecture with a reproducible local fallback. It does not claim a live enterprise deployment.

---

## Executive view

| Enterprise need | NexusMind response |
|---|---|
| Make internal knowledge usable | RAG with Azure AI Search production path and local Chroma fallback |
| Support complex requests | agent orchestration and multi-agent workflows |
| Connect AI to enterprise systems | allowlisted REST tool surface |
| Prevent unconstrained authority | governance layer, tenant boundaries, bounded memory and approval-oriented design |
| Evaluate behavior | bilingual RAG regression harness and human feedback |
| Fit Microsoft environments | Foundry, Azure OpenAI, Azure AI Search, Semantic Kernel, Copilot Studio-compatible OpenAPI |

See the [customer delivery case](docs/CUSTOMER_DELIVERY_CASE.md) for the discovery → architecture → rollout → KPI → failure-mode story.

---

## Business value

NexusMind is aimed at enterprise workflows where users currently:

- search across fragmented knowledge sources;
- move manually between systems;
- repeat low-value coordination steps;
- depend on experts to interpret internal information;
- need stronger traceability when AI participates in a process.

The architecture is designed to test a **copilot-first** operating model: retrieve and reason with approved context, invoke only bounded tools, capture feedback and evidence, then expand automation only when governance and business KPIs support it.

In a real engagement I would measure:

- task completion time;
- retrieval/grounding quality;
- escalation rate;
- tool success/failure rate;
- user adoption;
- manual steps removed;
- control exceptions;
- total cost per completed workflow.

---

## Architecture

```text
User / Copilot Studio
        ↓
      FastAPI
        ↓
 Governance layer
        ↓
 Agent orchestrator
   ┌────┼─────────┐
   ↓    ↓         ↓
 RAG   web    allowlisted
search search   REST tools
   └────┼─────────┘
        ↓
Azure OpenAI / Microsoft Foundry
        ↓
bounded memory + audit + evaluation + feedback
```

### Microsoft production path

- **Microsoft Foundry** — Foundry-native agent execution
- **Azure OpenAI** — LLM and embeddings provider
- **Azure AI Search** — hybrid/vector retrieval with filterable tenant/role fields
- **Microsoft Agent Framework** — primary production-oriented orchestration path
- **Semantic Kernel** — Microsoft interoperability adapter
- **AutoGen** — compatibility multi-agent implementation
- **Copilot Studio** — OpenAPI-compatible action/connector surface through FastAPI

---

## Verified engineering evidence

**Reference CI:** NexusMind CI run #20  
**Date:** 14 September 2026  
**Conclusion:** success

The workflow ran the same governance/memory/enterprise-API regression set on:

- Python 3.10 — **6/6 tests passed**
- Python 3.12 — **6/6 tests passed**

The CI evidence demonstrates that the tested governance, bounded-memory and enterprise-API contracts remain reproducible across both supported Python versions.

The RAG evaluation harness reports observed metrics from the seeded fictional corpus rather than hard-coding performance claims.

---

## Governance principles

### 1. Tool access is not model authority
The model can select from approved capabilities, but enterprise tools remain allowlisted and bounded by the application layer.

### 2. Retrieval scope cannot be escalated by the model
User/tenant authorization context is resolved outside model-selected content.

### 3. Memory is bounded
Session memory supports continuity without pretending that indefinite, uncontrolled memory is safe by default.

### 4. Production claims stay separate from architecture claims
Azure paths are implemented as reference integrations, while local fallbacks keep the system reproducible.

---

## Capability map

| Capability | Evidence |
|---|---|
| Enterprise GenAI | provider-agnostic chat orchestration with Azure OpenAI support |
| RAG | Chroma fallback + Azure AI Search production path |
| Embeddings/vector search | Azure OpenAI embeddings + Azure AI Search |
| Agents | Microsoft Agent Framework, Semantic Kernel and AutoGen adapters |
| Multi-agent workflows | business-analyst + solution-architect workflow |
| Tool calling | web, governed RAG and enterprise REST connector |
| Memory | session-scoped bounded conversation memory |
| Security/governance | tenant boundary, redaction, prompt-injection checks, hash-chained audit |
| Evaluation | Arabic/English RAG regression harness |
| APIs | FastAPI, SSE streaming, generated OpenAPI |
| Delivery | Docker, Docker Compose, GitHub Actions |

---

## Run locally

```bash
cp .env.example .env
# Local fallback example:
# LLM_PROVIDER=groq
# RAG_PROVIDER=chroma

pip install -r requirements.txt
python main.py
```

For the Microsoft-specific stack:

```bash
pip install -r requirements-microsoft.txt
```

Or with containers:

```bash
docker compose up --build
```

---

## Key API surfaces

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | provider/runtime capability report |
| POST | `/chat` | streamed agent chat |
| POST | `/ingest` | knowledge ingestion |
| POST | `/feedback` | human feedback capture |
| POST | `/memory/clear` | explicit memory reset |
| POST | `/agents/foundry` | Microsoft Foundry agent path |
| POST | `/agents/semantic-kernel` | Semantic Kernel path |
| POST | `/agents/autogen-team` | multi-agent workflow |
| GET | `/openapi.json` | Copilot Studio/custom connector contract |

---

## What I would change for a real enterprise

Production hardening would include:

- Microsoft Entra ID / managed identity;
- API Management;
- private networking where required;
- managed secrets;
- DLP/content-safety controls;
- document lifecycle and ownership;
- production observability;
- larger representative evaluation sets;
- explicit approval for write-capable actions;
- SLOs, incident response and cost monitoring.

NexusMind is best read as evidence of **forward-deployed AI architecture and governed Microsoft-enterprise integration**, not a claim that an autonomous production agent has already been deployed.
