"""RAG layer. Local keyword retrieval by default; Qdrant hooks included.

PromptHub grounds prompt execution with the synthetic Contoso ~M365~
documents (emails, Teams, Word, Excel, datasets). `rag_mode=local` performs
plain TF-based matching so no embedding stack is required for the demo.
"""

from __future__ import annotations

import re
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Document, DocumentChunk


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]{3,}", text.lower())


def _score_chunk(chunk: str, query_tokens: Counter, query_len: int) -> float:
    chunk_tokens = Counter(_tokens(chunk))
    overlap = sum(chunk_tokens[q] for q in query_tokens)
    if query_len == 0:
        return 0.0
    return overlap / query_len


class LocalRetriever:
    def __init__(self, db: Session) -> None:
        self.db = db

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 4,
        document_ids: list[int] | None = None,
        departments: list[str] | None = None,
    ) -> list[dict]:
        """Return scored snippets: [{document_id, name, doc_type, snippet, score}]."""
        stmt = select(Document)
        if document_ids:
            stmt = stmt.where(Document.id.in_(document_ids))
        if departments:
            stmt = stmt.where(Document.department.in_(departments))
        docs = self.db.scalars(stmt).all()

        query_tokens = Counter(_tokens(query))
        query_len = sum(query_tokens.values()) or 1

        hits: list[dict] = []
        for doc in docs:
            chunks = doc.chunks or [
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=0,
                    content=doc.content,
                    char_start=0,
                    char_end=len(doc.content),
                )
            ]
            for chunk in chunks:
                score = _score_chunk(chunk.content, query_tokens, query_len)
                if score > 0:
                    hits.append(
                        {
                            "document_id": doc.id,
                            "name": doc.name,
                            "doc_type": doc.doc_type,
                            "department": doc.department,
                            "snippet": self._snippet(chunk.content, 160),
                            "score": round(min(score, 1.0) * 100, 1),
                            "source": [doc.name],
                        }
                    )
        hits.sort(key=lambda h: h["score"], reverse=True)
        return hits[:top_k]

    def list_documents(self) -> list[dict]:
        docs = self.db.scalars(select(Document).order_by(Document.department, Document.name)).all()
        return [
            {
                "id": d.id,
                "doc_id": d.doc_id,
                "name": d.name,
                "doc_type": d.doc_type,
                "source_app": d.source_app,
                "department": d.department,
                "author": d.author,
                "summary": d.summary,
                "snippet": d.content[:220],
            }
            for d in docs
        ]

    @staticmethod
    def _snippet(text: str, width: int) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return text[:width] + ("…" if len(text) > width else "")


def get_retriever(db: Session) -> LocalRetriever:
    return LocalRetriever(db)
