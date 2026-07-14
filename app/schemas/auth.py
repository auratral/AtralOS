from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    username: str  # Staff email
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    department_id: Optional[str] = None
    name: str

class UserMeResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department_id: Optional[str] = None
    status: str
