import tools.enterprise_api as enterprise_api


def test_blocks_non_https(monkeypatch):
    monkeypatch.setattr(enterprise_api, "ENTERPRISE_API_ALLOWLIST", ["example.com"])
    assert enterprise_api._allowed("http://example.com/data") is False


def test_enforces_hostname_allowlist(monkeypatch):
    monkeypatch.setattr(enterprise_api, "ENTERPRISE_API_ALLOWLIST", ["example.com"])
    assert enterprise_api._allowed("https://api.example.com/data") is True
    assert enterprise_api._allowed("https://example.com.evil.test/data") is False
