"""Initialize the mounted data directory, drop privileges, and start one worker."""
from __future__ import annotations

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import validate_production


def main():
    validate_production()
    port = int(os.environ.get("PORT", "8000"))
    if not 1024 <= port <= 65535:
        sys.exit("PORT must be between 1024 and 65535")
    data = Path("/app/data")
    data.mkdir(parents=True, exist_ok=True)
    if os.geteuid() == 0:
        for base, dirs, files in os.walk(data):
            for path in [Path(base)] + [Path(base) / name for name in dirs + files]:
                if not path.is_symlink():
                    os.chown(path, 10001, 10001)
        os.setgroups([])
        os.setgid(10001)
        os.setuid(10001)
    os.execvp("uvicorn", ["uvicorn", "backend.app:app", "--host", "0.0.0.0",
                          "--port", str(port), "--workers", "1"])


if __name__ == "__main__":
    main()
