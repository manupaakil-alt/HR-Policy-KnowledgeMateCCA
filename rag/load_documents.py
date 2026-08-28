"""Load local PDF, TXT, and Markdown policy documents into the document table."""

import argparse
import hashlib
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader
from sqlalchemy import delete, select, text

from app.db import Base, SessionLocal, engine
from app.models import Document


load_dotenv()

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".markdown"}
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "ingestion.log"), logging.StreamHandler()],
)
logger = logging.getLogger("knowledge-mate.ingestion")


def clean_text(text: str) -> str:
    """Normalize document whitespace while preserving paragraph breaks."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_units(document_path: Path) -> list[tuple[int, str]]:
    """Return (page number, text) units for a supported local document."""
    suffix = document_path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(document_path))
        return [
            (page_number, clean_text(page.extract_text() or ""))
            for page_number, page in enumerate(reader.pages, start=1)
        ]
    if suffix in {".txt", ".md", ".markdown"}:
        return [(1, clean_text(document_path.read_text(encoding="utf-8", errors="replace")))]
    raise ValueError(f"Unsupported document format: {document_path.suffix}")


def split_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")

    chunks = []
    start = 0
    while start < len(text):
        proposed_end = min(start + chunk_size, len(text))
        end = proposed_end
        if proposed_end < len(text):
            boundary_start = start + chunk_size // 2
            paragraph_boundary = text.rfind("\n\n", boundary_start, proposed_end)
            word_boundary = text.rfind(" ", boundary_start, proposed_end)
            if paragraph_boundary > start:
                end = paragraph_boundary + 2
            elif word_boundary > start:
                end = word_boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        overlap_start = max(end - overlap, start + 1)
        boundary = max(
            text.rfind(" ", start + 1, overlap_start + 1),
            text.rfind("\n", start + 1, overlap_start + 1),
        )
        if boundary > start:
            start = boundary + 1
        else:
            start = overlap_start
            while start < len(text) and not text[start].isspace():
                start += 1
            while start < len(text) and text[start].isspace():
                start += 1
    return chunks


def ensure_document_schema() -> None:
    """Add loader metadata columns to databases created by the first schema."""
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS document_name TEXT NOT NULL DEFAULT 'legacy'
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS page_number INTEGER NOT NULL DEFAULT 1
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS chunk_index INTEGER NOT NULL DEFAULT 0
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS file_type TEXT NOT NULL DEFAULT 'unknown'
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS document_hash TEXT NOT NULL DEFAULT 'legacy'
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS chunk_char_count INTEGER NOT NULL DEFAULT 0
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE documents
                ADD COLUMN IF NOT EXISTS loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                """
            )
        )


def load_documents(data_dir: Path, chunk_size: int = 1000, overlap: int = 150) -> int:
    document_paths = sorted(
        path for path in data_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not document_paths:
        raise FileNotFoundError(f"No PDF, TXT, or Markdown documents found in {data_dir}")

    logger.info("Starting ingestion: %d document(s) found in %s", len(document_paths), data_dir)
    Base.metadata.create_all(bind=engine)
    ensure_document_schema()
    inserted = 0
    skipped = 0
    with SessionLocal() as session:
        for document_path in document_paths:
            document_hash = hashlib.sha256(document_path.read_bytes()).hexdigest()
            existing_hash = session.scalar(
                select(Document.document_hash)
                .where(Document.document_name == document_path.name)
                .limit(1)
            )
            if existing_hash == document_hash:
                skipped += 1
                logger.info("Skipped %s: unchanged document", document_path.name)
                continue

            session.execute(delete(Document).where(Document.document_name == document_path.name))
            document_chunks = 0
            for page_number, document_text in extract_text_units(document_path):
                for chunk_index, content in enumerate(split_text(document_text, chunk_size, overlap)):
                    session.add(
                        Document(
                            document_name=document_path.name,
                            file_type=document_path.suffix.lower().lstrip("."),
                            document_hash=document_hash,
                            page_number=page_number,
                            chunk_index=chunk_index,
                            chunk_char_count=len(content),
                            content=content,
                        )
                    )
                    inserted += 1
                    document_chunks += 1
            logger.info(
                "Processed %s (%s): %d chunk(s)",
                document_path.name,
                document_path.suffix.lower().lstrip("."),
                document_chunks,
            )
        session.commit()
    logger.info(
        "Ingestion complete: %d chunk(s) stored, %d unchanged document(s) skipped",
        inserted,
        skipped,
    )
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Load local HR policy PDFs into PostgreSQL")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=150)
    args = parser.parse_args()
    count = load_documents(args.data_dir, args.chunk_size, args.overlap)
    print(f"Loaded {count} document chunks from {args.data_dir}")


if __name__ == "__main__":
    main()