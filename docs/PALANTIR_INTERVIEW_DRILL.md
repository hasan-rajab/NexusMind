# Palantir FDSE Interview Drill — NexusMind

Use NexusMind to demonstrate enterprise AI delivery, bounded agent design and customer/problem decomposition. Do not oversell the demo access model as production identity.

## 30-second pitch

NexusMind is a production-oriented enterprise agentic-AI reference architecture. It combines governed RAG, tool calling, bounded memory, multiple agent frameworks, FastAPI/OpenAPI integration, evaluation and auditability. The forward-deployed point is not “I built a chatbot”; it is that I start from an enterprise knowledge problem, define trust and approval boundaries, make retrieval measurable, keep critical controls deterministic, and design a rollout that can be tested with a small customer cohort before expanding.

## Hostile questions and defensible answers

### Why agents at all?
Only where task decomposition or tool specialization adds value. Retrieval, authorization and approval semantics should remain deterministic. If one model call plus a retrieval/tool step is enough, a multi-agent graph is unnecessary complexity.

### Can the model escalate its own retrieval role?
No. The retrieval tool schema exposes only the query, and `_execute_tool` always applies the server-selected active role. Model-generated tool arguments cannot choose a broader role. This is covered by a regression test.

### Is the current tenant header a production authentication boundary?
No. In the portfolio service, `X-Tenant-ID` is a demo routing/scoping input unless a trusted identity layer binds that value. A production deployment must derive tenant and authorization claims from authenticated identity—e.g. Entra ID/JWT/IAP/API gateway claims—not trust a caller-controlled header. NEXUS demonstrates a stricter authorization model; NexusMind focuses on Microsoft/agent interoperability and delivery architecture.

### Isn't your prompt-injection filter trivial?
Yes if treated as the security boundary, which it is not. The string heuristic catches obvious requests but cannot prove prompt-injection safety. The important controls are deterministic tool allowlists, server-selected retrieval scope, restricted outbound API access, bounded memory and human approval for risky actions. A production evaluation suite should include adversarial prompt-injection cases.

### Why both Azure AI Search and Chroma?
Azure AI Search represents the managed production path and supports enterprise retrieval infrastructure. Chroma is a reproducible local fallback so the repository can be exercised without cloud spend. Provider abstraction keeps retrieval behavior testable while making the scope difference explicit.

### Why multiple agent frameworks?
They are interoperability evidence, not a claim that every deployment should run all frameworks simultaneously. The production choice should be based on customer platform constraints, supportability and observability. The core orchestration/security contracts matter more than framework count.

### Why an allowlisted enterprise API connector?
An agent with arbitrary outbound URL access becomes an SSRF/data-exfiltration risk. The connector constrains where reads can go. Production would additionally use workload identity, per-tool authorization, egress controls, request schemas, rate limits and audit policy.

### What should happen if retrieval evidence is weak?
The assistant should abstain or escalate rather than fill the gap with model fluency. Success metrics therefore include retrieval relevance, grounded-answer rate, citation/evidence quality and abstention correctness—not just whether the response sounds helpful.

### How would you roll this out to a customer?
Start with one high-value document domain and a small user cohort; define a golden evaluation set and access policy; validate retrieval/grounding before tool actions; observe failures; iterate on citations/latency; then add side effects behind explicit approval and expand data sources only after measurable quality gates.

### What breaks at enterprise scale?
Process-local memory, simple file audit logging, caller-supplied demo tenant context, synchronous provider calls and local Chroma are not scale/identity solutions. At scale I would externalize session state, use authenticated identity claims, centralize audit/telemetry, add rate limits/circuit breakers, use managed search/data stores, trace model/retrieval/tool stages and define SLOs.

### Why not just use NEXUS instead?
The projects prove different things. NEXUS is the stronger governed-RAG/security architecture with retrieval-time authorization and approval-gated actions. NexusMind is the Microsoft/agentic interoperability and customer-delivery system: Foundry, Azure OpenAI/Search, Semantic Kernel/Agent Framework/AutoGen adapters, OpenAPI integration and bounded orchestration. In an interview, lead with whichever problem the discussion needs rather than presenting them as duplicates.

### What is the hardest design tradeoff?
Keeping enough flexibility for agent/tool workflows while ensuring the model never becomes the authorization layer. The design intentionally separates probabilistic reasoning from deterministic policy decisions.

## Code anchors

- `orchestrator.py` — tool execution and server-selected retrieval scope
- `governance.py` — input heuristics, redaction, API-key comparison and audit hash chain
- `tools/azure_search.py` — managed hybrid/vector retrieval path
- `tools/enterprise_api.py` — outbound allowlist boundary
- `backend/app.py` — API surface and auth hooks
- `tests/test_retrieval_scope.py` — role-escalation regression
- `docs/CUSTOMER_DELIVERY_CASE.md` — discovery, rollout, success measures and scale/failure reasoning

## Claims boundary

Do not claim production Entra/IAM integration, unbreakable prompt-injection defense, real enterprise deployment, or that caller-supplied tenant headers are authenticated identity. Claim a production-oriented reference architecture with explicit trust boundaries, server-controlled tool scope, measurable rollout design and Microsoft AI interoperability.
