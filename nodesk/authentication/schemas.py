from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    access_token: str
    token_type: str = "bearer"
