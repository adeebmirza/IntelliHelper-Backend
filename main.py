from fastapi import FastAPI
from src.routes.profile import profile_router
from src.routes.auth import auth_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

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






