from src.Chatbot.chat_def import create_graph, AVAILABLE_MODELS, ModelListResponse, ChatRequest, graphs
from langchain_core.messages import HumanMessage
from src.database import chats_collection
from datetime import datetime
import uuid
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from src.profile.token_jwt import get_current_user
from collections import OrderedDict
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

chat_router = APIRouter(tags=["Chatbot"])

# Manage active graphs with a size limit
graphs = OrderedDict()

# Define a Pydantic model for chat history items to handle ObjectId serialization
class ChatHistoryItem(BaseModel):
    thread_id: str
    message: str
    response: str
    model: str
    timestamp: datetime

    class Config:
        json_encoders = {ObjectId: str}

def create_graph_with_limit(model_name: str, thread_id: str):
    if len(graphs) > 100:  # Limit active graphs
        graphs.popitem(last=False)  # Remove oldest entry
    graphs[thread_id] = create_graph(model_name, thread_id)

@chat_router.get("/models", response_model=ModelListResponse)
async def get_models():
    return {"models": AVAILABLE_MODELS}

@chat_router.post("/chat")
async def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    """Chat endpoint - streams response, stores conversation, returns chat history."""
    thread_id = request.thread_id or str(uuid.uuid4())

    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model '{request.model}' is not available"
        )

    if thread_id not in graphs:
        graphs[thread_id] = create_graph(request.model, thread_id)

    graph = graphs[thread_id]
    input_message = HumanMessage(content=request.message)

    response_content = ""
    try:
        async for event in graph.astream(
            {"messages": [input_message]},
            {"configurable": {"thread_id": thread_id}},
            stream_mode="values"
        ):
            response_content = event["messages"][-1].content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing failed: {str(e)}"
        )

    try:
        await chats_collection.insert_one({
            "user_id": ObjectId(user["_id"]),
            "thread_id": thread_id,
            "message": request.message,
            "response": response_content,
            "model": request.model,
            "timestamp": datetime.utcnow()
        })

        # Fetch chat history and serialize ObjectId
        chat_history_cursor = chats_collection.find(
            {"user_id": ObjectId(user["_id"]), "thread_id": thread_id}
        ).sort("timestamp", 1)
        chat_history_raw = await chat_history_cursor.to_list(length=None)
        chat_history = [
            ChatHistoryItem(
                thread_id=item["thread_id"],
                message=item["message"],
                response=item["response"],
                model=item["model"],
                timestamp=item["timestamp"]
            )
            for item in chat_history_raw
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

    return {
        "thread_id": thread_id,
        "model": request.model,
        "chat_history": [item.dict() for item in chat_history] # Return as list of dictionaries
    }


@chat_router.get("/chats")
async def get_all_chats(user: dict = Depends(get_current_user)):
    try:
        chat_sessions = await chats_collection.distinct("thread_id", {"user_id": ObjectId(user["_id"])})
        return {"chats": chat_sessions}
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to fetch chats: {str(e)}"}, status_code=500)

@chat_router.get("/history/{thread_id}", response_model=List[ChatHistoryItem])
async def get_chat_history(thread_id: str, user: dict = Depends(get_current_user)):
    try:
        cursor = chats_collection.find(
            {"user_id": ObjectId(user["_id"]), "thread_id": thread_id}
        ).sort("timestamp", 1)
        chat_history_raw = await cursor.to_list(length=None)

        if not chat_history_raw:
            raise HTTPException(status_code=404, detail="No chat history found for this thread.")

        chat_history = [
            ChatHistoryItem(
                thread_id=item["thread_id"],
                message=item["message"],
                response=item["response"],
                model=item["model"],
                timestamp=item["timestamp"]
            )
            for item in chat_history_raw
        ]

        return chat_history
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to fetch history: {str(e)}"}, status_code=500)
    


@chat_router.delete("/chat/{thread_id}")
async def delete_chat(thread_id: str, user: dict = Depends(get_current_user)):
    """Delete a chat session."""
    try:
        result = await chats_collection.delete_many({"thread_id": thread_id, "user_id": ObjectId(user["_id"])})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="No chat session found to delete.")
        return {"message": "Chat session deleted successfully."}
    except Exception as e:
        return JSONResponse(content={"error": f"Failed to delete chat: {str(e)}"}, status_code=500)
    
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
        async for event in graph.astream({"messages": [input_message]}, {"configurable": {"thread_id": thread_id}}, stream_mode="values"):
            response_content = event["messages"][-1].content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI response failed: {str(e)}")

    return {
        "response": response_content,
        "thread_id": thread_id,
        "model": request.model,
        "chat_history": []
    }