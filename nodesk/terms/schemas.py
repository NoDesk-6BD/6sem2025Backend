from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class TermType(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class CreateTermsRequest(BaseModel):
    version: str
    content: str
    type: TermType = TermType.REQUIRED  # padrão para obrigatório


class TermsResponse(BaseModel):
    id: int
    version: str
    content: str
    type: TermType
    created_at: datetime


class AcceptTermsRequest(BaseModel):
    user_id: int
    terms_id: int


class TermsAcceptanceResponse(BaseModel):
    id: int
    user_id: int
    terms_id: int
    accepted_at: datetime
    ip_address: str | None
