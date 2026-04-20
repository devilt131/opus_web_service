from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
import re

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email")
    password: str = Field(..., min_length=6, max_length=100, description="Пароль")
    
    @field_validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Имя пользователя может содержать только буквы, цифры и _')
        return v

class UserLogin(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    password: str = Field(..., description="Пароль")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str
    
    class Config:
        from_attributes = True