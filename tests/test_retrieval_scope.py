import orchestrator


def test_model_cannot_override_server_selected_retrieval_role(monkeypatch):
    captured = {}

    def fake_retrieve(query, role, tenant_id):
        captured.update(query=query, role=role, tenant_id=tenant_id)
        return "ok"

    monkeypatch.setattr(orchestrator, "_retrieve", fake_retrieve)

    result = orchestrator._execute_tool(
        "retrieve_enterprise_knowledge",
        {"query": "policy", "role": "knowledge_admin"},
        active_role="assistant",
        tenant_id="tenant-a",
    )

    assert result == "ok"
    assert captured == {
        "query": "policy",
        "role": "assistant",
        "tenant_id": "tenant-a",
    }


def test_retrieval_tool_schema_does_not_offer_role_escalation_parameter():
    tool = next(
        item for item in orchestrator.TOOLS
        if item["function"]["name"] == "retrieve_enterprise_knowledge"
    )
    assert set(tool["function"]["parameters"]["properties"]) == {"query"}
