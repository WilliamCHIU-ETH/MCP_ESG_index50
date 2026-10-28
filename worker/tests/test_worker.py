import asyncio
import json

from conftest import TOKEN, WORKERS, FakeUpstream, FakeVectorize, tool_call


def run(coro):
    return asyncio.run(coro)


def tool_text(body):
    return body["result"]["content"][0]["text"]


# --- access control and transport limits ---------------------------------


def test_wrong_or_missing_token_is_404_and_never_calls_openai(send):
    for path in ("/mcp", "/mcp/wrong", "/", f"/mcp/{TOKEN}x"):
        status, _ = run(send(tool_call({"query": "碳排"}), path=path))
        assert status == 404
    assert WORKERS.calls == []


def test_unset_token_secret_rejects_everything(send, env):
    env.MCP_PATH_TOKEN = ""
    status, _ = run(send(tool_call({"query": "碳排"}), path="/mcp/"))
    assert status == 404


def test_get_is_405(send):
    status, _ = run(send("", method="GET"))
    assert status == 405


def test_oversized_body_is_413(send):
    status, body = run(send(json.dumps({"pad": "a" * 20_000})))
    assert status == 413
    assert body["error"]["code"] == -32600


# --- JSON-RPC envelope ------------------------------------------------------


def test_parse_error(send):
    status, body = run(send("{bad"))
    assert status == 400
    assert body["error"]["code"] == -32700


def test_non_object_bodies_are_invalid_request(send):
    for raw in ("[1,2]", '"x"', "null", "1"):
        status, body = run(send(raw))
        assert status == 200
        assert body["error"]["code"] == -32600


def test_deep_nesting_does_not_crash(send):
    # CPython hits RecursionError (parse error); Pyodide may parse it (invalid request).
    status, body = run(send("[" * 3000 + "]" * 3000))
    assert body["error"]["code"] in (-32700, -32600)
    assert status in (200, 400)


def test_params_must_be_object(send):
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": [1]}
    _, body = run(send(msg))
    assert body["error"]["code"] == -32600


def test_unknown_method(send):
    _, body = run(send({"jsonrpc": "2.0", "id": 7, "method": "foo"}))
    assert body == {
        "jsonrpc": "2.0",
        "id": 7,
        "error": {"code": -32601, "message": "Method not found"},
    }


def test_unknown_tool(send):
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "nope"}}
    _, body = run(send(msg))
    assert body["error"]["code"] == -32602


# --- MCP 2026-07-28 header checks -------------------------------------------


def test_missing_protocol_version_is_400(send):
    status, body = run(send({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, version=None))
    assert status == 400
    assert body["error"]["code"] == -32020


def test_mcp_method_header_mismatch_is_400(send):
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    status, _ = run(send(msg, headers={"mcp-method": "server/discover"}))
    assert status == 400


def test_mcp_name_header_mismatch_is_400(send):
    status, body = run(send(tool_call({"query": "x"}), headers={"mcp-name": "other"}))
    assert status == 400
    assert body["error"]["code"] == -32020


def test_discover_and_tools_list(send):
    _, body = run(send({"jsonrpc": "2.0", "id": 1, "method": "server/discover"}))
    assert body["result"]["supportedVersions"] == ["2026-07-28"]
    _, body = run(send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    tool = body["result"]["tools"][0]
    assert tool["name"] == "search_esg_reports"
    assert tool["annotations"]["readOnlyHint"] is True
    assert tool["inputSchema"]["properties"]["query"]["maxLength"] == 500


def test_legacy_initialize_without_new_headers(send):
    msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2025-11-25"},
    }
    _, body = run(send(msg, version=None))
    assert body["result"]["protocolVersion"] == "2025-11-25"
    msg["params"]["protocolVersion"] = ["bad"]
    _, body = run(send(msg, version=None))
    assert body["result"]["protocolVersion"] == "2025-11-25"
    status, _ = run(send({"jsonrpc": "2.0", "method": "notifications/initialized"}, version=None))
    assert status == 202


# --- search_esg_reports validation ------------------------------------------


def test_argument_validation_returns_tool_errors_without_upstream_calls(send):
    cases = [
        ("x", "arguments must be an object"),
        ({}, "query must be a non-empty string"),
        ({"query": "   "}, "query must be a non-empty string"),
        ({"query": 123}, "query must be a non-empty string"),
        ({"query": "碳" * 501}, "query too long"),
        ({"query": "x", "top_k": 0}, "top_k must be at least 1"),
        ({"query": "x", "top_k": -3}, "top_k must be at least 1"),
        ({"query": "x", "top_k": "3"}, "top_k must be an integer"),
        ({"query": "x", "top_k": True}, "top_k must be an integer"),
        ({"query": "x", "top_k": 2.5}, "top_k must be an integer"),
        ({"query": "x", "strategy": "bm25"}, "strategy must be one of: vector"),
        ({"query": "x", "company": "國泰金"}, "unknown company"),
        ({"query": "x", "company": {"$ne": "x"}}, "unknown company"),
    ]
    for arguments, expected in cases:
        _, body = run(send(tool_call(arguments)))
        assert body["result"]["isError"] is True, arguments
        assert expected in tool_text(body), arguments
    assert WORKERS.calls == []


def test_infinity_top_k_is_rejected(send):
    raw = json.dumps(tool_call({"query": "x"}))[:-3] + ', "top_k": Infinity}}}'
    _, body = run(send(raw, headers={"mcp-method": "tools/call", "mcp-name": "search_esg_reports"}))
    assert "top_k must be an integer" in tool_text(body)


def test_missing_openai_secret(send, env):
    env.OPENAI_API_KEY = None
    _, body = run(send(tool_call({"query": "x"})))
    assert "OPENAI_API_KEY secret is not set" in tool_text(body)


def test_upstream_failures_hide_details(send, env):
    WORKERS.next_upstream = FakeUpstream(status=401)
    _, body = run(send(tool_call({"query": "x"})))
    assert tool_text(body) == "embedding service unavailable, try again later"
    assert "sk-test" not in json.dumps(body)

    WORKERS.next_upstream = FakeUpstream()
    env.VECTORIZE = FakeVectorize(fail=True)
    _, body = run(send(tool_call({"query": "x"})))
    assert tool_text(body) == "search index unavailable, try again later"


# --- successful call ----------------------------------------------------------


def test_tools_call_output_matches_v1_format(send, env):
    _, body = run(send(tool_call({"query": " 範疇一 ", "company": "台積電", "top_k": 9})))
    result = body["result"]
    assert result["isError"] is False
    data = result["structuredContent"]
    assert json.loads(result["content"][0]["text"]) == data
    assert data["query"] == "範疇一"
    assert data["strategy"] == "vector"
    assert data["results"] == [
        {
            "company": "台積電",
            "source_file": "1-台積電.pdf",
            "page": 210,
            "chunk_id": "456",
            "content": "範疇一排放量",
            # cosine 0.8 -> squared L2 0.4 -> 1 / 1.4
            "score": 0.7143,
            "citation": "台積電 | 1-台積電.pdf | p.210 | 456",
        }
    ]

    url, kwargs = WORKERS.calls[0]
    assert url == "https://api.openai.com/v1/embeddings"
    assert kwargs["headers"]["authorization"] == "Bearer sk-test"
    assert json.loads(kwargs["body"]) == {
        "model": "text-embedding-3-small",
        "input": "範疇一",
        "dimensions": 256,
    }
    _, options = env.VECTORIZE.queries[0]
    assert options == {"topK": 5, "returnMetadata": "all", "filter": {"company": "台積電"}}


def test_no_company_means_no_filter(send, env):
    run(send(tool_call({"query": "淨零", "company": ""})))
    _, options = env.VECTORIZE.queries[0]
    assert "filter" not in options
