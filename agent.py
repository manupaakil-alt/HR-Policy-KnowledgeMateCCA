"""LangGraph ReAct agent and external research tools."""

import os
import re

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from rag.retriever import retriever_tool

load_dotenv()


SYSTEM_PROMPT = """You are an HR policy assistant using a retrieval-augmented workflow.
Use the retriever first for questions about the organization's policies and documents.
Use Wikipedia and Tavily for general HR related theories and concepts.Do not answer questions which are not related to HR
For those questions, respond with "I am sorry, I can only answer questions related to HR "
Never present external information as company policy.
Clearly distinguish internal retrieved evidence from external sources.
Cite internal evidence as [filename, page N, chunk N] and include external source URLs.
Answer the user's question directly and say when the available evidence is insufficient.
"""

HR_TERMS = (
    "hr", "human resource", "employee", "employment", "workplace", "work",
    "leave", "vacation", "holiday", "attendance", "benefit", "payroll",
    "salary", "wage", "harassment", "discrimination", "remote", "hybrid",
    "parental", "maternity", "paternity", "sick", "policy", "handbook",
    "termination", "resign", "recruit", "onboarding", "performance",
    "disciplinary", "grievance", "safety", "training", "compensation",
    "contract", "confidentiality", "data protection",
)


def _is_hr_question(question: str) -> bool:
    normalized = question.casefold()
    return any(term in normalized for term in HR_TERMS)


@tool
def wikipedia_tool(query: str) -> str:
    """Search Wikipedia for general HR-related information."""
    response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": 3,
        },
        headers={"User-Agent": "HR-Policy-KnowledgeMate/1.0 (local research assistant)"},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("query", {}).get("search", [])
    if not results:
        return "Wikipedia found no results."
    return "\n\n".join(
        f"{item['title']}: {re.sub('<.*?>', '', item['snippet'])} "
        f"(https://en.wikipedia.org/?curid={item['pageid']})"
        for item in results
    )


@tool
def tavily_tool(query: str) -> str:
    """Search the current web using Tavily."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Tavily is unavailable because TAVILY_API_KEY is not configured."
    response = requests.post(
        "https://api.tavily.com/search",
        json={"api_key": api_key, "query": query, "search_depth": "advanced", "max_results": 5},
        timeout=15,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        return "Tavily found no results."
    return "\n\n".join(
        f"{result.get('title', 'Untitled')}: {result.get('content', '')} ({result.get('url', '')})"
        for result in results
    )


TOOLS = [retriever_tool, wikipedia_tool, tavily_tool]
model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0,
)
react_node = create_react_agent(model, TOOLS, prompt=SYSTEM_PROMPT)


def answer_question(question: str) -> str:
    """Run the LangGraph ReAct agent for a user question."""
    if not question or not question.strip():
        raise ValueError("Question must not be empty")
    if not _is_hr_question(question):
        return "I can only answer questions related to HR policies and workplace topics."

    result = react_node.invoke({"messages": [("user", question)]})
    final_message = result["messages"][-1]
    content = final_message.content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        ).strip()
    return str(content).strip()
