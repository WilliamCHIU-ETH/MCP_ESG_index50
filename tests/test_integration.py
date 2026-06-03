from __future__ import annotations

from pathlib import Path
import os
import shutil

import pytest

from claude_esg_mcp.config import RetrievalSettings
from claude_esg_mcp.server import build_default_retrieval_service


pytestmark = [pytest.mark.integration, pytest.mark.smoke]


def _require_live_env() -> Path:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is required for live smoke tests")

    configured_path = os.environ.get("CLAUDE_ESG_INDEX_PATH")
    if not configured_path:
        pytest.skip("CLAUDE_ESG_INDEX_PATH is required for live smoke tests")

    source_path = Path(configured_path)
    if not source_path.exists():
        pytest.skip(f"Real ESG index path is missing: {source_path}")

    return source_path


def test_real_query_returns_citation_ready_evidence_from_a_temp_index_copy(
    tmp_path: Path,
) -> None:
    source_path = _require_live_env()
    writable_index_path = tmp_path / "esg_50_vector_db"
    shutil.copytree(source_path, writable_index_path)

    settings = RetrievalSettings(
        index_path=str(writable_index_path),
        collection_name="esg_reports_50",
        embedding_model="text-embedding-3-small",
        max_top_k=3,
        max_content_chars=300,
    )

    service = build_default_retrieval_service(settings=settings)
    payload = service.search_esg_reports(
        query="台積電的碳中和目標是什麼",
        company="台積電",
        top_k=3,
    )

    assert payload["strategy"] == "vector"
    assert payload["results"], "Expected at least one retrieved evidence chunk"

    first_result = payload["results"][0]
    assert first_result["company"] == "台積電"
    assert set(first_result) >= {
        "company",
        "source_file",
        "page",
        "chunk_id",
        "content",
        "score",
        "citation",
    }
    assert len(first_result["content"]) <= settings.max_content_chars
