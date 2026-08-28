# HR Policy KnowledgeMate

## Project Description

HR Policy KnowledgeMate is an AI-powered knowledge assistant
that answers employee questions using HR policy documents.

## Objective

Reduce the time employees spend searching through HR documents.

## Current Progress

Week 1:

Week 3:
- PostgreSQL and pgvector database configured
- Local HR policy PDFs can be extracted and loaded as document chunks

## Load Local Documents

Start PostgreSQL with Docker, then run the loader from the project root:

```powershell
docker compose up -d db
& ".\venv\Scripts\python.exe" -m rag.load_documents
```

The loader reads every PDF, TXT, and Markdown file in `data/`, extracts its text, splits it into overlapping chunks, and stores each chunk with its source filename, file type, document hash, page number, chunk index, character count, and load timestamp. Re-running it replaces the previously loaded chunks for each source document.

Ingestion progress is printed to the console and written to `logs/ingestion.log`.

Embeddings and vector retrieval will be added in the RAG implementation phase.