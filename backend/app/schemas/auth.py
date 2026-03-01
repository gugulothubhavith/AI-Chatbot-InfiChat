from pydantic import BaseModel, EmailStr
from typing import Optional

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str
    avatar_url: Optional[str] = None
    is_new_user: bool

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
