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
- `agent.py`: Uses the configured OpenAI model to classify whether a question is HR-related, then runs a LangGraph ReAct agent for related questions.
- `rag/load_documents.py`: Extracts, semantically chunks, embeds, and loads policy documents.
- `rag/retriever.py`: Embeds questions and performs pgvector similarity search over stored policy chunks.
- `app/models.py`: SQLAlchemy document-chunk model with 384-dimensional embeddings.
- `docker-compose.yml`: Runs PostgreSQL with the pgvector extension on port `5434`.
- `data/`: Current NovaCare policy PDFs.

## Requirements

- Python 3.13 or compatible Python version
- Docker Desktop
- OpenAI API key for HR-topic classification and agent responses
- Optional Tavily API key for current web search; Wikipedia search does not require an API key

Install Python dependencies from the project root:

```powershell
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
```

Create a `.env` file with:

```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5434/knowledgemate
API_URL=http://localhost:8000/chat
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini
# Optional: enable Tavily web search
TAVILY_API_KEY=your-tavily-key
```

The HR relevance check uses the configured OpenAI model and returns a
structured yes/no result before the assistant handles the question. A
classification or OpenAI error is surfaced; the application does not fall
back to keyword matching.

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

At startup, the API loads the local MiniLM embedding model used for policy
retrieval. The first startup can take longer while the model is downloaded and
initialized; wait for startup to complete before sending chat requests. Later
requests reuse the loaded model.

Start the Streamlit UI in another terminal:

```powershell
& ".\venv\Scripts\python.exe" -m streamlit run app\main.py --server.address 127.0.0.1 --server.port 8501
```

Open the interface at <http://127.0.0.1:8501>. The API health check is
available at <http://127.0.0.1:8000/health>.

## Agent Behavior

After the LLM-based HR relevance check accepts a question, the LangGraph agent
receives it and can select from three tools:

1. The internal pgvector retriever for NovaCare policy evidence.
2. Wikipedia for general HR background.
3. Tavily for current web information when `TAVILY_API_KEY` is configured.

The agent is instructed to use the internal retriever first for company-policy
questions. Wikipedia is available without a key; Tavily requires
`TAVILY_API_KEY`. The agent chooses whether external searches are useful.
External information is not company policy and should be distinguished from
internal evidence. Internal evidence should be cited with its source filename,
page number, and chunk number; external sources should include their URLs.