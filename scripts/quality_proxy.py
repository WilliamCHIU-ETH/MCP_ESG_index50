"""Key-free proxy for the 1536 vs 256 check: use stored chunk vectors as queries.

For 300 random chunks, compare exact top-5 neighbours (self excluded) in the full
1536-d space against the 256-d truncated + renormalized space, across all
companies and within the chunk's own company.
"""

import json
import sys

import numpy as np

K, N = 5, 300
d = np.load(sys.argv[1])
full = d["vecs"]
cut = full[:, :256] / np.linalg.norm(full[:, :256], axis=1, keepdims=True)
company = np.array(
    [json.loads(line)["metadata"]["company"] for line in open(sys.argv[2], encoding="utf-8")]
)
rng = np.random.default_rng(0)
picks = rng.choice(len(full), N, replace=False)


def top(m, i, mask):
    s = m @ m[i]
    s[i] = -np.inf
    if mask is not None:
        s = np.where(mask, s, -np.inf)
    return set(np.argsort(-s)[:K])


for label, use_mask in (("all companies", False), ("same company", True)):
    ov = [
        len(
            top(full, i, company == company[i] if use_mask else None)
            & top(cut, i, company == company[i] if use_mask else None)
        )
        / K
        for i in picks
    ]
    print(
        f"{label}: mean top-{K} overlap {np.mean(ov):.0%}, top-1 kept {np.mean([o > 0 for o in ov]):.0%}, min {min(ov):.0%}"
    )
