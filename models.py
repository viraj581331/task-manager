from sqlalchemy import Column, Integer, String, TIMESTAMP, text
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # New column with TIMESTAMP and DEFAULT CURRENT_TIMESTAMP
    created_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=text("CURRENT_TIMESTAMP")
    )
