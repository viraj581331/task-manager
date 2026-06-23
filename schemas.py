from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

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
