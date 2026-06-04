from pydantic import BaseModel, EmailStr, Field
from typing import Any, Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

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


class HistoryItem(BaseModel):
    id: int
    title: str
    preview: str
    summary: str
    date: str


class ExportRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    ref_text: Optional[str] = None
    result: Optional[dict[str, Any]] = None