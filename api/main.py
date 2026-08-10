from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="HR Policy KnowledgeMate API"
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/")
def home():
    return {
        "message": "HR Policy KnowledgeMate API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/chat", response_model=ChatResponse)
def chat_placeholder(request: ChatRequest):
    return ChatResponse(answer="This is a chat placeholder response.")