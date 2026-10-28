"""Run worker.py under CPython by stubbing the Workers runtime modules.

`workers`, `js` and `pyodide.ffi` only exist inside Cloudflare's Pyodide runtime, so
the tests install tiny fakes before importing the worker. OpenAI and Vectorize are
faked per test; nothing touches the network.
"""

import json
import sys
import types
from pathlib import Path

import pytest

TOKEN = "test-token-123"


class FakeResponse:
    def __init__(self, body="", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}

    def json(self):
        return json.loads(self.body)


class FakeEntrypoint:
    def __init__(self, env):
        self.env = env


class FakeUpstream:
    """Stands in for the OpenAI embeddings response returned by workers.fetch."""

    def __init__(self, status=200, embedding=None):
        self.status = status
        self._embedding = embedding or [0.1] * 256

    async def json(self):
        return {"data": [{"embedding": self._embedding}]}


def _install_stubs():
    workers = types.ModuleType("workers")
    workers.Response = FakeResponse
    workers.WorkerEntrypoint = FakeEntrypoint
    workers.calls = []
    workers.next_upstream = FakeUpstream()

    async def fetch(url, **kwargs):
        workers.calls.append((url, kwargs))
        return workers.next_upstream

    workers.fetch = fetch
    js = types.ModuleType("js")
    js.Object = types.SimpleNamespace(fromEntries=None)
    pyodide = types.ModuleType("pyodide")
    ffi = types.ModuleType("pyodide.ffi")
    ffi.to_js = lambda value, **_: value
    pyodide.ffi = ffi
    sys.modules.update({"workers": workers, "js": js, "pyodide": pyodide, "pyodide.ffi": ffi})
    return workers


WORKERS = _install_stubs()
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import worker  # noqa: E402


class FakeVectorize:
    def __init__(self, matches=None, fail=False):
        self.matches = matches if matches is not None else []
        self.fail = fail
        self.queries = []

    async def query(self, vector, options):
        self.queries.append((vector, options))
        if self.fail:
            raise RuntimeError("vectorize down")
        return types.SimpleNamespace(matches=self.matches)


class FakeRequest:
    def __init__(self, path, body, method="POST", headers=None):
        self.url = f"https://esg-mcp.example.workers.dev{path}"
        self.method = method
        self._body = body
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}

    async def text(self):
        return self._body


SAMPLE_MATCH = {
    "id": "台積電_chunk_00456",
    "score": 0.8,
    "metadata": {
        "company": "台積電",
        "source_file": "1-台積電.pdf",
        "page": 210,
        "chunk_id": 456,
        "content": "範疇一排放量",
    },
}


@pytest.fixture
def env():
    WORKERS.calls.clear()
    WORKERS.next_upstream = FakeUpstream()
    return types.SimpleNamespace(
        OPENAI_API_KEY="sk-test", MCP_PATH_TOKEN=TOKEN, VECTORIZE=FakeVectorize([SAMPLE_MATCH])
    )


@pytest.fixture
def send(env):
    """POST a JSON-RPC message (dict or raw str) and return (status, parsed body)."""

    async def _send(
        message, *, path=f"/mcp/{TOKEN}", headers=None, method="POST", version="2026-07-28"
    ):
        body = message if isinstance(message, str) else json.dumps(message)
        hdrs = {"content-type": "application/json"}
        if version:
            hdrs["mcp-protocol-version"] = version
        if isinstance(message, dict) and version == "2026-07-28":
            hdrs["mcp-method"] = message.get("method", "")
            if message.get("method") == "tools/call":
                hdrs["mcp-name"] = (message.get("params") or {}).get("name", "")
        hdrs.update(headers or {})
        resp = await worker.Default(env).fetch(FakeRequest(path, body, method, hdrs))
        try:
            parsed = json.loads(resp.body) if resp.body else None
        except ValueError:
            parsed = resp.body
        return resp.status, parsed

    return _send


def tool_call(arguments, req_id=1):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": "tools/call",
        "params": {"name": "search_esg_reports", "arguments": arguments},
    }
