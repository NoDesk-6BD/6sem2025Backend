from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..core.di import provider_for
from ..users.models import User, TermsOfUse, TermsAcceptance

# from .models import TermsOfUse, TermsAcceptance
from .schemas import (
    CreateTermsRequest,
    TermsResponse,
    AcceptTermsRequest,
    TermsAcceptanceResponse,
)

# Dependências
Session = Annotated[AsyncSession, Depends(provider_for(AsyncSession))]

terms_router = APIRouter(prefix="/terms", tags=["terms"])


@terms_router.post("/", response_model=TermsResponse, status_code=status.HTTP_201_CREATED)
async def create_terms(payload: CreateTermsRequest, session: Session):
    new_terms = TermsOfUse(
        version=payload.version,
        content=payload.content,
        type=payload.type,
    )
    session.add(new_terms)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="A version with this identifier already exists")
    await session.refresh(new_terms)
    return TermsResponse.model_validate(new_terms, from_attributes=True)


@terms_router.get("/latest", response_model=TermsResponse)
async def get_latest_terms(
    user_id: int,
    session: Session,
):
    stmt = select(TermsOfUse).order_by(TermsOfUse.created_at.desc()).limit(1)
    result = await session.execute(stmt)
    latest_term = result.scalar_one_or_none()

    if not latest_term:
        raise HTTPException(status_code=404, detail="No terms found")

    # Checa se usuário já aceitou
    accepted_stmt = select(TermsAcceptance).where(
        TermsAcceptance.user_id == user_id,
        TermsAcceptance.terms_id == latest_term.id,
    )
    accepted_result = await session.execute(accepted_stmt)
    if accepted_result.scalar_one_or_none():
        raise HTTPException(status_code=204, detail="User already accepted latest terms")

    return TermsResponse.model_validate(latest_term, from_attributes=True)


@terms_router.post("/accept", response_model=TermsAcceptanceResponse)
async def accept_terms(
    payload: AcceptTermsRequest,
    session: Session,
    request: Request,  # injeta a requisição
):
    user_stmt = select(User).where(User.id == payload.user_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    term_stmt = select(TermsOfUse).where(TermsOfUse.id == payload.terms_id)
    term_result = await session.execute(term_stmt)
    term = term_result.scalar_one_or_none()
    if not term:
        raise HTTPException(status_code=404, detail="Terms not found")

    existing_stmt = select(TermsAcceptance).where(
        TermsAcceptance.user_id == payload.user_id,
        TermsAcceptance.terms_id == payload.terms_id,
    )
    existing_result = await session.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already accepted this terms version")

    # Pega o IP do cliente
    client_ip = request.client.host

    acceptance = TermsAcceptance(
        user_id=payload.user_id,
        terms_id=payload.terms_id,
        ip_address=client_ip,  # usa IP capturado
    )
    session.add(acceptance)
    await session.commit()
    await session.refresh(acceptance)
    return TermsAcceptanceResponse.model_validate(acceptance, from_attributes=True)
