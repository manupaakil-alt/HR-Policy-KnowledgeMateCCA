"""Vector retrieval for ingested HR policy chunks."""

from dataclasses import dataclass
from functools import lru_cache

from app.db import SessionLocal
from app.models import Document


@dataclass
class RetrievedChunk:
    document_name: str
    page_number: int
    chunk_index: int
    content: str
    score: float

    @property
    def citation(self) -> str:
        return f"{self.document_name}, page {self.page_number}, chunk {self.chunk_index}"


@lru_cache(maxsize=2)
def _embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def retrieve_chunks(
    question: str,
    top_k: int = 5,
    model_name: str = "all-MiniLM-L6-v2",
) -> list[RetrievedChunk]:
    """Return the nearest stored policy chunks for a question."""
    if not question or not question.strip():
        return []
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    query_embedding = _embedding_model(model_name).encode(
        [question], normalize_embeddings=True, show_progress_bar=False
    )[0].tolist()
    distance = Document.embedding.cosine_distance(query_embedding)

    with SessionLocal() as session:
        rows = session.query(Document, distance.label("distance")).filter(
            Document.embedding.is_not(None)
        ).order_by(distance).limit(top_k).all()

    return [
        RetrievedChunk(
            document_name=document.document_name,
            page_number=document.page_number,
            chunk_index=document.chunk_index,
            content=document.content,
            score=1.0 - float(row_distance),
        )
        for document, row_distance in rows
    ]


def retriever_tool(question: str, top_k: int = 5) -> str:
    """Format retrieved chunks for use by an agent."""
    chunks = retrieve_chunks(question, top_k=top_k)
    if not chunks:
        return "No matching internal HR policy chunks were found."
    return "\n\n".join(
        f"[{chunk.citation}; relevance={chunk.score:.3f}]\n{chunk.content}"
        for chunk in chunks
    )
