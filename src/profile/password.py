from passlib.context import CryptContext

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper function: Hash password
def get_password_hash(password: str):
    return pwd_context.hash(password)


# Helper function: Verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)