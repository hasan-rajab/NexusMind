# Microsoft Copilot Studio integration

NexusMind exposes a standards-based FastAPI OpenAPI document at `GET /openapi.json`. This allows the enterprise agent service to be registered as a custom connector/action surface for Microsoft Copilot Studio without duplicating business logic.

Recommended actions: `POST /chat`, `POST /ingest`, `POST /agents/foundry`, and `POST /agents/semantic-kernel`.

Production controls:
1. Enable `REQUIRE_API_KEY=true` or front the API with Microsoft Entra ID/API Management.
2. Restrict CORS and network access.
3. Propagate `X-Tenant-ID` per tenant.
4. Keep future write-capable enterprise actions behind human approval.
5. Import the generated `/openapi.json` into the Copilot Studio connector/action workflow.

The codebase uses Microsoft Agent Framework as the current Foundry-native production path while retaining Semantic Kernel and AutoGen adapters for interoperability and migration experience.
