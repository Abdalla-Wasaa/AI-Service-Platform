"""Deterministic test environment configured before application imports."""

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator

import httpx
import pytest

os.environ["JWT_SECRET"] = "pytest-only-secret-with-at-least-32-characters"
os.environ["ACCESS_TOKEN_MINUTES"] = "30"
os.environ["AGENT_MODE"] = "offline"


@pytest.fixture(scope="session")
def api_url() -> Iterator[str]:
    """Run the real ASGI server because this FastAPI release deprecates TestClient."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "service.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        env=os.environ.copy(),
    )
    try:
        for _ in range(100):
            try:
                if httpx.get(f"{url}/health", timeout=0.25).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.05)
        else:
            raise RuntimeError("test API did not start")
        yield url
    finally:
        process.terminate()
        process.wait(timeout=5)
