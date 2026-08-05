from fastapi import FastAPI

app = FastAPI(
    title="HR Policy KnowledgeMate API"
)


@app.get("/")
def home():
    return {
        "message": "HR Policy KnowledgeMate API is running"
    }