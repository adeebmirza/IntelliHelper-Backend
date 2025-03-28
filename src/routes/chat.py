from src.Chatbot.chat_def import create_graph, AVAILABLE_MODELS, ModelListResponse, ChatRequest, graphs
from langchain_core.messages import HumanMessage
from src.database import chats_collection
import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from src.profile.token_jwt import get_current_user
from collections import OrderedDict

chat_router = APIRouter(tags=["Chatbot"])

# Manage active graphs with a size limit
graphs = OrderedDict()

def create_graph_with_limit(model_name: str, thread_id: str):
    if len(graphs) > 100:  # Limit active graphs
        graphs.popitem(last=False)  # Remove oldest entry
    graphs[thread_id] = create_graph(model_name, thread_id)

@chat_router.get("/models", response_model=ModelListResponse)
async def get_models():
    return {"models": AVAILABLE_MODELS}

@chat_router.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Chat for authenticated users (Saves chat history)."""
    thread_id = request.thread_id or str(uuid.uuid4())
    user_id = current_user["user_id"]

    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Model {request.model} not available")

    if thread_id not in graphs:
        create_graph_with_limit(request.model, thread_id)

    graph = graphs[thread_id]
    input_message = HumanMessage(content=request.message)

    try:
        response_content = ""
        for event in graph.stream({"messages": [input_message]}, {"configurable": {"thread_id": thread_id}}, stream_mode="values"):
            response_content = event["messages"][-1].content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI response failed: {str(e)}")

    # Save to MongoDB
    try:
        chats_collection.insert_one({
            "user_id": user_id,
            "thread_id": thread_id,
            "message": request.message,
            "response": response_content,
            "model": request.model,
            "timestamp": datetime.datetime.utcnow()
        })
        chat_history = list(chats_collection.find(
            {"user_id": user_id, "thread_id": thread_id}, {"_id": 0}
        ).sort("timestamp", 1))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "response": response_content,
        "thread_id": thread_id,
        "model": request.model,
        "chat_history": chat_history
    }

@chat_router.post("/chat/test")
async def chat_test(request: ChatRequest):
    """Testing chat endpoint (No authentication, No chat saving)."""
    thread_id = str(uuid.uuid4())

    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Model {request.model} not available")

    if thread_id not in graphs:
        create_graph_with_limit(request.model, thread_id)

    graph = graphs[thread_id]
    input_message = HumanMessage(content=request.message)

    try:
        response_content = ""
        for event in graph.stream({"messages": [input_message]}, {"configurable": {"thread_id": thread_id}}, stream_mode="values"):
            response_content = event["messages"][-1].content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI response failed: {str(e)}")

    return {
        "response": response_content,
        "thread_id": thread_id,
        "model": request.model,
        "chat_history": []
    }

@chat_router.get("/chats")
async def get_all_chats(current_user: dict = Depends(get_current_user)):
    """Fetch all chat session IDs for authenticated users."""
    try:
        user_id = current_user["user_id"]
        chat_sessions = chats_collection.distinct("thread_id", {"user_id": user_id})
        return {"chats": chat_sessions}
    except Exception as e:
        return {"error": f"Failed to fetch chat sessions: {str(e)}"}

@chat_router.get("/history/{thread_id}")
async def get_chat_history(thread_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve chat history (only for the owner)."""
    try:
        user_id = current_user["user_id"]
        chat_history = list(chats_collection.find(
            {"thread_id": thread_id, "user_id": user_id}, {"_id": 0}
        ).sort("timestamp", 1))

        if not chat_history:
            return {"error": "No chat history found for this thread."}

        return {"thread_id": thread_id, "chat_history": chat_history}
    except Exception as e:
        return {"error": f"Failed to fetch chat history: {str(e)}"}
