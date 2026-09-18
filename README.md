# HR Policy KnowledgeMate

HR Policy KnowledgeMate is a retrieval-augmented HR assistant for NovaCare
(Pvt) Ltd. It answers employee questions using the organization's policy
documents and can consult external sources when additional context is useful.

## System Structure

```mermaid
flowchart TD
	A[Policy PDFs in data/] --> B[rag.load_documents]
	B --> C[PDF text extraction]
	C --> D[Semantic chunking with all-MiniLM-L6-v2]
	D --> E[384-dimensional embeddings]
	E --> F[(PostgreSQL + pgvector)]

	U[User] --> S[Streamlit UI\napp/main.py]
	S --> API[FastAPI API\napi/main.py]
	API --> R[LangGraph\ncreate_react_agent]
	R --> T[Internal retriever]
	R --> W[Wikipedia tool]
	R --> V[Tavily tool]
	T --> F
	R --> L[OpenAI chat model]
	L --> R
	R --> API
	API --> S
	S --> U
```

## Main Components

- `app/main.py`: Streamlit interface for submitting questions and displaying conversation history.
- `api/main.py`: FastAPI service with `/`, `/health`, and `/chat` endpoints.
- `agent.py`: LangGraph ReAct agent created with `create_react_agent()`.
- `rag/load_documents.py`: Extracts, semantically chunks, embeds, and loads policy documents.
- `rag/retriever.py`: Performs pgvector similarity search over stored policy chunks.
- `app/models.py`: SQLAlchemy document-chunk model with 384-dimensional embeddings.
- `docker-compose.yml`: Runs PostgreSQL with the pgvector extension on port `5433`.
- `data/`: Current NovaCare policy PDFs.

## Requirements

- Python 3.13 or compatible Python version
- Docker Desktop
- OpenAI API key for agent responses
- Optional Tavily API key for current web search

Install Python dependencies from the project root:

```powershell
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
```

Create a `.env` file with:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/knowledgemate
API_URL=http://localhost:8000/chat
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini
TAVILY_API_KEY=your-tavily-key
```

## Ingest Policy Documents

Start PostgreSQL and load the current files in `data/`:

```powershell
docker compose up -d db
& ".\venv\Scripts\python.exe" -m rag.load_documents
```

The loader supports PDF, TXT, and Markdown files. It stores each chunk with
the document name, file type, hash, page number, chunk index, character count,
embedding, and load timestamp. Re-running the loader skips unchanged files,
replaces changed files, and removes database chunks for source files deleted
from `data/`.

Ingestion logs are written to `logs/ingestion.log`.

## Run the System

Start the API in one terminal:

```powershell
& ".\venv\Scripts\python.exe" -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Start the Streamlit UI in another terminal:

```powershell
& ".\venv\Scripts\python.exe" -m streamlit run app\main.py --server.address 127.0.0.1 --server.port 8501
```

Open the interface at <http://127.0.0.1:8501>. The API health check is
available at <http://127.0.0.1:8000/health>.

## Agent Behavior

The LangGraph agent receives the user's question and can select from three
tools:

1. The internal pgvector retriever for NovaCare policy evidence.
2. Wikipedia for general HR background.
3. Tavily for current web information when `TAVILY_API_KEY` is configured.

The application rejects questions unrelated to HR and workplace topics before
invoking the agent. Internal evidence should be cited with its source filename,
page number, and chunk number.