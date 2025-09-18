from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None
    phone: str | None = None
    cpf: str = Field(min_length=11, max_length=14)
    vip: bool = False


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    full_name: str | None = None
    phone: str | None = None
    cpf: str | None = Field(default=None, min_length=11, max_length=14)
    vip: bool | None = None
    active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None
    phone: str | None
    cpf: str
    vip: bool
    active: bool
    created_at: datetime
    updated_at: datetime
