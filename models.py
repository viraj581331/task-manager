from sqlalchemy import Column, Integer, String, TEXT, DATETIME, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    # Establishes a relationship link to the Task model (cascades deletions)
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    # task_id INT PRIMARY KEY AUTO_INCREMENT
    task_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # title VARCHAR(255) NOT NULL
    title = Column(String(255), nullable=False)
    
    # description TEXT NULL
    description = Column(TEXT, nullable=True)
    
    # status VARCHAR(50) DEFAULT 'pending'
    status = Column(String(50), nullable=False, server_default="pending")
    
    # due_date DATETIME NULL
    due_date = Column(DATETIME, nullable=True)
    
    # created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    
    # updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    updated_at = Column(
        TIMESTAMP, 
        nullable=False, 
        server_default=text("CURRENT_TIMESTAMP"), 
        server_onupdate=text("CURRENT_TIMESTAMP")
    )
    
    # user_id INT FOREIGN KEY NOT NULL (WITH CASCADE ON DELETE)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    # Establishes a relationship link back to the User model
    owner = relationship("User", back_populates="tasks")
