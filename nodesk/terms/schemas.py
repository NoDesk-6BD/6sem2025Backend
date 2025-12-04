from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel


class TermType(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class CreateTermsRequest(BaseModel):
    version: str
    content: str
    type: TermType = TermType.REQUIRED
    purposes: Optional[Dict[str, str]] = None  # {finalidade: descricao, ...}


class TermsResponse(BaseModel):
    id: int
    version: str
    content: str
    type: TermType
    created_at: datetime
    purposes: Optional[Dict[str, str]] = None  # {finalidade: descricao, ...}

    class Config:
        from_attributes = True


class AcceptTermsRequest(BaseModel):
    user_id: int
    terms_id: int
    accepted_purposes: Dict[str, bool]  # {finalidade: true/false, ...}


class TermsAcceptanceResponse(BaseModel):
    id: int
    user_id: int
    terms_id: int
    accepted_at: datetime
    ip_address: str | None
    accepted_purposes: Optional[Dict[str, bool]] = None  # {finalidade: true/false, ...}

    class Config:
        from_attributes = True


class TermsCheckResponse(BaseModel):
    accepted: bool
    latest_terms: TermsResponse
    accepted_purposes: Optional[Dict[str, bool]] = None  # {finalidade: true/false, ...}
