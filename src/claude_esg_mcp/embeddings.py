"""Embedding provider interfaces and implementations."""

from __future__ import annotations

import os
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Interface for query embedding generation."""

    def embed_query(self, query: str, model: str) -> list[float]:
        """Return an embedding vector for the given query."""


class OpenAIEmbeddingProvider:
    """OpenAI-backed embedding provider for query-time vectors."""

    def __init__(self, client: object | None = None, api_key: str | None = None) -> None:
        self._client = client
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def embed_query(self, query: str, model: str) -> list[float]:
        if self._client is None:
            if not self._api_key:
                raise ValueError("OPENAI_API_KEY is required for query embeddings")
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)

        response = self._client.embeddings.create(model=model, input=query)
        return list(response.data[0].embedding)
