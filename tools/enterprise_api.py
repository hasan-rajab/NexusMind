"""Allowlisted enterprise REST connector for agent tool use."""
from urllib.parse import urlparse
import httpx
from config import ENTERPRISE_API_ALLOWLIST


def _allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    hostname = parsed.hostname.lower()
    return any(hostname == allowed or hostname.endswith("." + allowed) for allowed in ENTERPRISE_API_ALLOWLIST)


def enterprise_api_get(url: str) -> str:
    if not ENTERPRISE_API_ALLOWLIST:
        return "Enterprise API connector is disabled: no allowlist configured."
    if not _allowed(url):
        return "Blocked by enterprise API allowlist."
    response = httpx.get(url, timeout=10.0, follow_redirects=False)
    response.raise_for_status()
    return response.text[:8000]
