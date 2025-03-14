from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta,timezone
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends,Security
from src.database import get_user

ALGORITHM = "HS256"
REFRESH_SECRET_KEY = "your_refresh_secret_key"
ACCESS_TOKEN_EXPIRE_DAYS = 20  # Token expires in 20 days
RESET_TOKEN_EXPIRE_MINUTES = 15
SECRET_KEY = "your_secret_key"
REFRESH_TOKEN_EXPIRE_DAYS = 7 


# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")  


# Helper function: Create JWT token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Dependency: Get current user from token
async def get_current_user(token: str = Security(oauth2_scheme)):  
    """Extracts user from the token and verifies their existence."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        exp = payload.get("exp")

        if not username or not exp or datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        user = await get_user(username=username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    

# Helper function: Create Password Reset Token
def generate_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": email, "exp": expire}
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

# Helper function: Verify Password Reset Token
def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        return email
    except JWTError:
        return None

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

# Verify Token
def verify_token(token: str, secret_key: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")