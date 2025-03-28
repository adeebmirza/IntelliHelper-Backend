from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage,AIMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from src.profile.form import ChatRequest,ModelListResponse
from dotenv import load_dotenv
from src.database import chats_collection
from src.Chatbot.prompt import CUSTOM_PROMPT

AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "deepseek-r1-distill-qwen-32b",
    "gemma2-9b-it"
]
memory_dict: Dict[str, MemorySaver] = {}
graphs: Dict[str, StateGraph] = {}

load_dotenv()
# Groq API Key from environment variable
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("Missing GROQ_API_KEY environment variable!")

prompt_template = ChatPromptTemplate.from_template(CUSTOM_PROMPT)
# Function to create a new AI graph session
def create_graph(model_name: str, thread_id: str):
    workflow = StateGraph(state_schema=MessagesState)
    
    model = ChatGroq(
        api_key=api_key,
        model=model_name,
        temperature=0,
        max_tokens=None,
        timeout=10,
        max_retries=2,
    )

    def call_model(state: MessagesState):
        # Build conversation history from state
        history = ""
        for msg in state["messages"][:-1]:  # Exclude the current message
            if isinstance(msg, HumanMessage):
                history += f"User: {msg.content}\n"
            elif isinstance(msg, AIMessage):
                history += f"IntelliHelper: {msg.content}\n"
        
        # Get the current user message
        current_message = state["messages"][-1].content
        
        # Format the prompt with history, context (empty for now), and question
        formatted_prompt = prompt_template.format_messages(
            history=history if history else "No previous conversation.",
            context="",  # Add custom context here if needed
            question=current_message
        )
        
        # Invoke the model with the formatted prompt
        response = model.invoke(formatted_prompt)
        return {"messages": response}

    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)
    
    # Initialize memory
    memory = MemorySaver()
    memory_dict[thread_id] = memory
    
    return workflow.compile(checkpointer=memory)
