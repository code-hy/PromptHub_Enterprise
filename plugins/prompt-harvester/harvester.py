"""Harvest a PromptCreate skeleton from the local RAG corpus."""

from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "backend")

from app.database import SessionLocal  # type: ignore  # noqa: E402
from app.rag.retriever import LocalRetriever  # type: ignore  # noqa: E402

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--query", required=True)
    p.add_argument("--top-k", type=int, default=5)
    a=p.parse_args()
    db=SessionLocal()
    hits=LocalRetriever(db).retrieve(a.query, top_k=a.top_k)
    payload={
        "name": f"Harvested: {a.query[:40]}",
        "business_function": "OPERATIONS",
        "task": "SUMMARISE",
        "goal": a.query,
        "context": " ".join(h["snippet"][:160] for h in hits)[:800],
        "source": ", ".join(h["name"] for h in hits),
        "expectations": "Return a grounded summary with sources.",
        "tags": ["harvested", "rag"],
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")

if __name__=="__main__":
    main()
