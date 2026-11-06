import os
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from agent import answer_question
from rag.retriever import warm_embedding_model


LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, "api.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger("knowledge-mate.api")

app = FastAPI(
    title="HR Policy KnowledgeMate API"
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.on_event("startup")
def on_startup():
    logger.info("Starting HR Policy KnowledgeMate API")
    logger.info("Loading policy retrieval embedding model")
    warm_embedding_model()
    logger.info("Policy retrieval embedding model is ready")


@app.get("/")
def home():
    return {"message": "HR Policy KnowledgeMate API is running"}


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    logger.info("Received chat request")
    logger.debug("Question: %s", request.question)
    try:
        question = request.question
        if not question or not question.strip():
            logger.warning("Empty question received")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question must not be empty")

        answer_text = answer_question(question)
        logger.info("Returning agent answer for question")
        return ChatResponse(answer=answer_text)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled error in /chat endpoint")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")