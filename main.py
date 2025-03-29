from fastapi import FastAPI
from src.routes.profile import profile_router
from src.routes.auth import auth_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from src.routes.notes import notes_router
from src.routes.todo import todo_router
from src.routes.news import news_router
from src.routes.chat import chat_router
from src.routes.livebot import live_bot
from src.routes.websearch import web_search_router
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains (for testing)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(profile_router)
app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(todo_router)
app.include_router(news_router)
app.include_router(chat_router)
app.include_router(live_bot)
app.include_router(web_search_router)



