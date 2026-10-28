"""Export the esg_reports_50 Chroma backup to Vectorize NDJSON without chromadb.

Vectors come from the HNSW segment (data_level0.bin + id_to_label pickle) plus
any rows still in embeddings_queue; metadata and documents come from sqlite.
Each 1536-d vector is truncated to 256 dims and L2-normalized.

Usage: python scripts/export_to_vectorize.py <db_dir> <out.ndjson> [<full1536.npz>]
"""

import io
import json
import pickle
import sqlite3
import struct
import sys
from pathlib import Path

import numpy as np

DIMS = 256
CONTENT_CHARS = 1200
META_LIMIT = 10 * 1024


class _DataOnly(pickle.Unpickler):
    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"refusing global {module}.{name}")


def load_hnsw(seg: Path) -> dict[str, np.ndarray]:
    h = (seg / "header.bin").read_bytes()
    _, _, count, per_elem, label_off, data_off = struct.unpack_from(
        "<6Q", h, 4
    )  # 4-byte version prefix in chroma's hnswlib
    dim = (label_off - data_off) // 4
    raw = np.fromfile(seg / "data_level0.bin", dtype=np.uint8)[: count * per_elem].reshape(
        count, per_elem
    )
    vecs = raw[:, data_off:label_off].copy().view(np.float32).reshape(count, dim)
    labels = raw[:, label_off : label_off + 8].copy().view(np.uint64).ravel()
    meta = _DataOnly(io.BytesIO((seg / "index_metadata.pickle").read_bytes())).load()
    label_to_id = {v: k for k, v in meta["id_to_label"].items()}
    return {
        label_to_id[int(lab)]: vecs[i] for i, lab in enumerate(labels) if int(lab) in label_to_id
    }


def main(db_dir: str, out: str, full_out: str | None = None) -> None:
    db = Path(db_dir)
    con = sqlite3.connect(f"file:{db / 'chroma.sqlite3'}?mode=ro", uri=True)
    seg_id = con.execute("select id from segments where scope='VECTOR'").fetchone()[0]
    vectors = load_hnsw(db / seg_id)
    for qid, blob in con.execute(
        "select id, vector from embeddings_queue where operation=0 order by seq_id"
    ):
        vectors[qid] = np.frombuffer(blob, dtype=np.float32)

    rows = {}
    q = """select e.embedding_id, m.key, m.string_value, m.int_value, m.float_value
           from embeddings e join embedding_metadata m on m.id = e.id"""
    for eid, key, s, i, f in con.execute(q):
        rows.setdefault(eid, {})[key] = s if s is not None else (i if i is not None else f)

    missing = [eid for eid in rows if eid not in vectors]
    if missing:
        sys.exit(f"{len(missing)} ids have no vector, e.g. {missing[:3]}")

    max_meta = 0
    ids, full = [], []
    with open(out, "w", encoding="utf-8") as fh:
        for eid in sorted(rows):
            r = rows[eid]
            v = vectors[eid].astype(np.float64)
            t = v[:DIMS] / np.linalg.norm(v[:DIMS])
            meta = {
                "company": r["company"],
                "source_file": r["source_file"],
                "page": int(r["page"]),
                "chunk_id": r["chunk_id"],
                "content": (r.get("chroma:document") or "")[:CONTENT_CHARS],
            }
            size = len(json.dumps(meta, ensure_ascii=False).encode())
            max_meta = max(max_meta, size)
            if size >= META_LIMIT:
                sys.exit(f"metadata too large for {eid}: {size} bytes")
            fh.write(
                json.dumps(
                    {"id": eid, "values": [round(x, 7) for x in t], "metadata": meta},
                    ensure_ascii=False,
                )
                + "\n"
            )
            ids.append(eid)
            full.append(v.astype(np.float32))

    if full_out:
        np.savez_compressed(full_out, ids=np.array(ids), vecs=np.stack(full))
    print(
        f"wrote {len(ids)} vectors, max metadata {max_meta} bytes, companies {len({rows[i]['company'] for i in ids})}"
    )


if __name__ == "__main__":
    main(*sys.argv[1:])
