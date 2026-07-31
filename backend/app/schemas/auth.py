from pydantic import BaseModel, EmailStr
from typing import Optional

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
    # Consent flags — required only when this verification creates a new
    # account, since /auth/verify-otp doubles as a registration path.
    accept_terms: bool = False
    accept_privacy: bool = False

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user_id: str
    name: str
    email: str
    avatar_url: Optional[str] = None
    is_new_user: bool
    role: Optional[str] = None
    permissions: Optional[list[str]] = []

class TokenRefresh(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    # Explicit consent flags — required at registration (Phase 3.2)
    accept_terms: bool = False
    accept_privacy: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class MFASetupResponse(BaseModel):
    secret: str
    uri: str

class MFAVerifyRequest(BaseModel):
    code: str
