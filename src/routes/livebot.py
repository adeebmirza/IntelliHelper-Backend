from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import subprocess
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import APIRouter

live_bot = APIRouter(tags=["LiveBot"])
# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
# Define request model
class ChatRequest(BaseModel):
    message: str

# Famous websites mapping
FAMOUS_WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://twitter.com",
    "instagram": "https://www.instagram.com",
    "github": "https://www.github.com",
    "linkedin": "https://www.linkedin.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "whatsapp": "https://web.whatsapp.com"
}

def open_url(url: str):
    """Opens a URL in the default web browser."""
    try:
        subprocess.run(["xdg-open", url], check=True)  # For Linux
    except FileNotFoundError:
        try:
            subprocess.run(["open", url], check=True)  # For macOS
        except FileNotFoundError:
            subprocess.run(["start", url], shell=True, check=True)  # For Windows

@live_bot.post("/livechat")
async def chat(request: ChatRequest):
    try:
        user_message = request.message.lower().strip()

        # Check if message contains any famous website name
        for site in FAMOUS_WEBSITES:
            if site in user_message:
                open_url(FAMOUS_WEBSITES[site])
                return {"message": f"Opening {site}..."}

        # Otherwise, use Gemini AI to respond
        response = model.generate_content(request.message)
        return {"message": response.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
