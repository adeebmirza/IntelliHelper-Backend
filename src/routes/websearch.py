from fastapi import FastAPI, Query, APIRouter
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.groq import Groq  
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Initialize router
web_search_router = APIRouter(tags=["Web Search"])

# Set API Key
Groq.api_key = os.getenv("GROQ_API_KEY")

# Initialize the Web Search Agent using Groq's LLaMA 3 model
web_search_agent = Agent(
    name="Web Search Agent",
    role="Search the web for information",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGoTools()],
    instructions=["Always include sources"],
    show_tool_calls=True,
    markdown=True
)

@web_search_router.get("/search")
async def search_web(query: str = Query(..., description="Search query for web information")):
    try:
        # Use `.run()` to get the response
        response = web_search_agent.run(input=query, tool_calls=True, max_tokens=1000, temperature=0.5)
        

        # Extract the response text
        response_content = response.output if hasattr(response, "output") else str(response)

        # Extract the tool call details (if available)
        tool_call = response.tool_calls if hasattr(response, "tool_calls") else None

        # Format the response
        formatted_response = {
            "response": response_content,
            "tool_calls": tool_call
        }
        return formatted_response

    except Exception as e:
        return {"error": str(e)}

# Include router in FastAPI app
app.include_router(web_search_router)
