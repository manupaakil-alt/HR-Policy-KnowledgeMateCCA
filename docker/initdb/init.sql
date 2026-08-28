-- Initialize pgvector extension and create the document chunk table
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  document_name TEXT NOT NULL,
  file_type TEXT NOT NULL,
  document_hash TEXT NOT NULL,
  page_number INTEGER NOT NULL,
  chunk_index INTEGER NOT NULL,
  chunk_char_count INTEGER NOT NULL,
  loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  content TEXT NOT NULL,
  embedding vector(1536)
);
