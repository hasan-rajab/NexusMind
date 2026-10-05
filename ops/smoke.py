"""CI-only startup and retrieval checks; never invokes a paid LLM provider."""
from __future__ import annotations

import json
import secrets
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    image = "nexusmind-production:ci"
    key = secrets.token_urlsafe(48)
    container = subprocess.check_output([
        "docker", "run", "-d", "-p", "127.0.0.1:18081:8000",
        "-e", "NEXUSMIND_API_KEY=" + key,
        "-e", "GROQ_API_KEY=ci-no-provider-call",
        "-e", "ALLOWED_ORIGINS=https://nexus.example.test", image], text=True).strip()
    origin = "http://127.0.0.1:18081"
    def request(path, *, data=None, authenticated=True):
        headers = {"X-API-Key": key} if authenticated else {}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(origin + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
        with urlopen(req, timeout=10) as response:
            return response.status, response.read()
    def wait_ready():
        deadline = time.monotonic() + 240
        while True:
            try:
                if request("/ready", authenticated=False)[0] == 200:
                    return
            except (HTTPError, URLError, TimeoutError, ConnectionError):
                pass
            if time.monotonic() > deadline:
                raise RuntimeError("NexusMind failed to initialize its retrieval provider")
            time.sleep(1)
    try:
        wait_ready()
        assert request("/")[0] == 200
        for path in ("/stats", "/weaknesses"):
            try:
                request(path, authenticated=False)
                raise AssertionError("Protected route accepted a missing application key")
            except HTTPError as exc:
                assert exc.code == 401
        request("/ingest", data={"text": "CI knowledge: capacity review occurs every Tuesday.",
                                 "metadata": {"role": "assistant", "source": "CI-only fixture"}})
        assert json.loads(request("/stats")[1])["rag"]["total_documents"] == 1
        subprocess.run(["docker", "exec", container, "python", "-c",
            "from tools.rag import retrieve_user_data; assert 'Tuesday' in retrieve_user_data('capacity review', role='assistant')"], check=True)
        subprocess.run(["docker", "restart", container], check=True, stdout=subprocess.DEVNULL)
        wait_ready()
        assert json.loads(request("/stats")[1])["rag"]["total_documents"] == 1
        print("Production image smoke passed: readiness, authentication, real embedding retrieval and restart persistence. No LLM provider call was made.")
    except BaseException:
        subprocess.run(["docker", "logs", container], check=False)
        raise
    finally:
        subprocess.run(["docker", "rm", "-f", container], check=False, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
