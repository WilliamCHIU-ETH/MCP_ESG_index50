"""Compare top-5 retrieval: full 1536-d vectors vs 256-d truncated + renormalized.

Exact (brute-force) cosine search on both sides, so the difference is only the
dimension cut. Reads OPENAI_API_KEY from <repo>/.env.local and never prints it.

Usage: python quality_check.py <full1536.npz> <export.ndjson>
"""

import json
import sys
from pathlib import Path

import numpy as np
from openai import OpenAI

QUESTIONS = [
    ("台積電 2023 年範疇一與範疇二溫室氣體排放量是多少？", "台積電"),
    ("鴻海的再生能源使用比例與 RE100 目標", "鴻海"),
    ("國泰金控如何把氣候風險納入投融資決策？", "國泰金控"),
    ("哪些公司設定了 2050 淨零排放目標？", None),
    ("半導體業的水資源回收率與節水措施", None),
]
K = 5


def load_key() -> str:
    env = Path(__file__).resolve().parents[1] / ".env.local"
    for line in env.read_text().splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    sys.exit("OPENAI_API_KEY not found in .env.local")


def topk(matrix: np.ndarray, q: np.ndarray, mask: np.ndarray | None) -> list[int]:
    s = matrix @ q
    if mask is not None:
        s = np.where(mask, s, -np.inf)
    return list(np.argsort(-s)[:K])


def main(npz: str, ndjson: str) -> None:
    d = np.load(npz)
    ids, full = d["ids"], d["vecs"]
    cut = full[:, :256] / np.linalg.norm(full[:, :256], axis=1, keepdims=True)
    company = np.array(
        [json.loads(line)["metadata"]["company"] for line in open(ndjson, encoding="utf-8")]
    )

    client = OpenAI(api_key=load_key())
    overlaps = []
    for question, comp in QUESTIONS:
        q1536 = np.array(
            client.embeddings.create(model="text-embedding-3-small", input=question)
            .data[0]
            .embedding
        )
        q256 = np.array(
            client.embeddings.create(model="text-embedding-3-small", input=question, dimensions=256)
            .data[0]
            .embedding
        )
        mask = company == comp if comp else None
        a = topk(full, q1536, mask)
        b = topk(cut, q256, mask)
        common = len(set(a) & set(b))
        overlaps.append(common / K)
        print(f"\n[{common}/{K}] {question} (company={comp or 'all'})")
        print("  1536:", [str(ids[i]) for i in a])
        print("  256 :", [str(ids[i]) for i in b])
    print(f"\nmean top-{K} overlap: {np.mean(overlaps):.0%}")


if __name__ == "__main__":
    main(*sys.argv[1:])
