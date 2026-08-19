"""Knowledge / documents API — synthetic M365 content browsing and RAG."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Document
from ..rag import LocalRetriever

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    retriever = LocalRetriever(db)
    return {"items": retriever.list_documents()}


@router.get("/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "doc_id": doc.doc_id,
        "name": doc.name,
        "doc_type": doc.doc_type,
        "source_app": doc.source_app,
        "department": doc.department,
        "author": doc.author,
        "summary": doc.summary,
        "content": doc.content,
        "metadata": doc.metadata_,
    }


@router.post("/search")
def search_documents(body: dict, db: Session = Depends(get_db)):
    query = body.get("query", "")
    top_k = body.get("top_k", 5)
    document_ids = body.get("document_ids") or None
    retriever = LocalRetriever(db)
    hits = retriever.retrieve(query, top_k=top_k, document_ids=document_ids)
    return {"query": query, "hits": hits}
