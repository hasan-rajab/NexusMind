import pytest

import governance
from runtime import validate_production


def settings():
    return dict(ENVIRONMENT="production", REQUIRE_API_KEY="true", NEXUSMIND_API_KEY="a"*64,
                GROQ_API_KEY="test-provider-key", ALLOWED_ORIGINS="https://nexus.example.com")


@pytest.mark.parametrize("update", [{"REQUIRE_API_KEY": "false"}, {"NEXUSMIND_API_KEY": ""},
    {"GROQ_API_KEY": ""}, {"LLM_PROVIDER": "unknown"}, {"ALLOWED_ORIGINS": "*"},
    {"NEXUS_ANALYTICS_DB": "/tmp/a.sqlite", "NEXUS_ANALYTICS_KEY": ""}])
def test_production_cannot_start_with_insecure_or_incomplete_configuration(update):
    with pytest.raises(RuntimeError, match="Production configuration rejected"):
        validate_production(dict(settings(), **update))


def test_configured_production_and_development_validate():
    validate_production(settings())
    validate_production({"ENVIRONMENT": "development"})


def test_authentication_rejects_an_unconfigured_key(monkeypatch):
    monkeypatch.setattr(governance, "NEXUSMIND_API_KEY", "")
    assert not governance.verify_api_key(None)
    assert not governance.verify_api_key("anything")
