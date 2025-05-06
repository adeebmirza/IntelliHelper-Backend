from fastapi import FastAPI, Query, APIRouter
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.groq import Groq  
from dotenv import load_dotenv
from pydantic import BaseModel
import os
from agno.tools.newspaper4k import Newspaper4kTools
from fastapi import APIRouter, Query,HTTPException, Request
from fastapi import Query
from typing import Dict, Any
from tavily import TavilyClient
# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize router
web_search_router = APIRouter(tags=["Web Search"])

# Set API Key
Groq.api_key = os.getenv("GROQ_API_KEY")

# Initialize the Web Search Agent using Groq's LLaMA 3 model
client = TavilyClient("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")

TAVILY_CONFIG = {
    "search_depth": "basic",
    "max_results": 5,
    "timeout": 5,  # example extra param
    "include_answer":"basic"
}

@web_search_router.get("/search")
async def search_tavily(query: str = Query(..., description="Search query")):
    response = client.search(
    query=query,
    **TAVILY_CONFIG
)
    return response


class SummaryRequest(BaseModel):
    url: str

# Initialize agent globally
agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[Newspaper4kTools()],
    debug_mode=False,
    show_tool_calls=False,
)

# FastAPI POST route
@web_search_router.post("/summarize")
async def summarize_article(request: SummaryRequest):
    try:
        response = agent.run(f"Summarize {request.url}")
        return {"summary": response.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))