from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.di import provider_for
from .schemas import LoginRequest, TokenResponse
from .services import AuthenticationService

# Dependenciesz
Service = Annotated[AuthenticationService, Depends(provider_for(AuthenticationService))]


authentication_router = APIRouter(prefix="/auth", tags=["auth"])


@authentication_router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    service: Service,
) -> TokenResponse:
    result = await service.authenticate(
        email=payload.email.strip().lower(),
        password=payload.password,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return TokenResponse(
        access_token=result["access_token"],
        user_id=result["user_id"],
        name=result["name"],
        email=result["email"],
    )
