from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

# Define strict, acceptable choices for task status
class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

# Shared properties for creating a user or returning user info
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

# What we require when someone registers (needs a raw password)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# What we return to the client (we never return the password!)
class UserResponse(UserBase):
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Shared base properties for tasks
class TaskBase(BaseModel):
    # Ensure title cannot be empty spaces
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    # Strictly validate status against our Enum options
    status: TaskStatus = TaskStatus.pending
    due_date: datetime | None = None

# Fields required to create a new task
class TaskCreate(TaskBase):
    pass

# Fields allowed when modifying an existing task (all optional)
class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus | None = None  # Validates choices during updates
    due_date: datetime | None = None

# Structure of the response returned to the client
class TaskResponse(TaskBase):
    task_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


