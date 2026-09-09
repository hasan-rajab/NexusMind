# NexusMind Enterprise Architecture

## Objective
Translate an enterprise or government requirement into a governed, production-oriented GenAI solution that can run locally for development or on Microsoft Azure for deployment.

## Microsoft production path
Client / Copilot Studio → FastAPI API → governance + tenant boundary → agent orchestration → Microsoft Foundry / Azure OpenAI → tool calling → Azure AI Search / allowlisted enterprise REST APIs / web search → bounded session memory → streamed response → audit chain + evaluation + human feedback.

## Agent frameworks
- **Microsoft Agent Framework**: preferred Foundry-native production path.
- **Semantic Kernel**: Azure OpenAI agent interoperability adapter.
- **AutoGen**: compatibility multi-agent workflow because enterprise roles still request it; Microsoft Agent Framework is the forward production path.

## Security and responsible AI
- optional API-key gate
- tenant header propagation
- role-scoped retrieval
- common direct prompt-injection blocking
- allowlisted HTTPS-only enterprise API connector
- secrets redaction in audit events
- hash-chained audit log
- explicit abstention instruction for missing evidence
- human feedback / weakness capture
- bounded memory rather than unbounded conversation retention

## Evaluation
`evaluation/rag_eval.py` contains eight bilingual Arabic/English regression cases covering grounded answer terms, source behavior, unauthorized-data refusal, unknown-answer abstention and latency. No benchmark number is stored as a claim; metrics are produced from the running system.
