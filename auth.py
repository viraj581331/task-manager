from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


# Tell passlib to use bcrypt for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# --- NEW: Token Generation Logic ---
def create_access_token(data: dict):
    to_encode = data.copy()
    
    # Calculate when the token should expire (e.g., 30 minutes from now)
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Securely sign and encode the token using our secret key
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Configures FastAPI to pull out the token from the "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decrypt the incoming JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    # Search for the user profile in MySQL using the extracted user_id
    user = db.query(models.User).filter(models.User.user_id == int(user_id)).first()
    if user is None:
        raise credentials_exception
        
    return user  # Returns the valid database user instance to the endpoint
