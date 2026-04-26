from pydantic import BaseModel, EmailStr
from typing import Optional


class GoogleLoginRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    user_id: int
    google_sub: str
    full_name: str
    email: EmailStr
    profile_picture: Optional[str] = None
    auth_provider: str

    class Config:
        from_attributes = True


class GoogleLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse