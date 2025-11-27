from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update, func
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
    TermsCheckResponse,
)

# Dependências
Session = Annotated[AsyncSession, Depends(provider_for(AsyncSession))]

terms_router = APIRouter(prefix="/terms", tags=["terms"])


@terms_router.post("/new", response_model=TermsResponse, status_code=status.HTTP_201_CREATED)
async def create_terms(payload: CreateTermsRequest, session: Session):
    new_terms = TermsOfUse(
        version=payload.version,
        content=payload.content,
        type=payload.type,
    )

    stmt = select(TermsOfUse).where(TermsOfUse.type == new_terms.type).order_by(TermsOfUse.created_at.desc()).limit(1)

    result = await session.execute(stmt)

    current_term = result.scalar_one_or_none()

    if current_term:
        await session.execute(update(TermsOfUse).where(TermsOfUse.id == current_term.id).values(expired_at=func.now()))

    # Adicionar novo termo
    session.add(new_terms)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="A version with this identifier already exists")
    await session.refresh(new_terms)
    return TermsResponse.model_validate(new_terms, from_attributes=True)


@terms_router.get("/latest", response_model=TermsResponse)
async def check_newer_term(session: Session):
    latest_term = await get_latest_terms_stmt(session)

    if not latest_term:
        raise HTTPException(status_code=404, detail="No terms found")

    return TermsResponse.model_validate(latest_term, from_attributes=True)


@terms_router.get("/required", response_model=TermsResponse)
async def check_required_term(session: Session):
    latest_term = await get_latest_required_terms_stmt(session)

    if not latest_term:
        raise HTTPException(status_code=404, detail="No required terms found")

    return TermsResponse.model_validate(latest_term, from_attributes=True)


@terms_router.get("/check_user_acceptance", response_model=TermsCheckResponse)
async def get_latest_terms(
    user_id: int,
    session: Session,
):
    # Último termo ativo
    latest_term = await get_latest_terms_stmt(session)

    if not latest_term:
        raise HTTPException(status_code=204, detail="No terms found")

    # Último termo aceito pelo usuário
    accepted_result = await get_user_accepted_terms(session, user_id)

    if not accepted_result:
        # Nunca aceitou nenhum termo
        return TermsCheckResponse(
            accepted=False,
            latest_terms=TermsResponse.model_validate(latest_term, from_attributes=True),
        )

    # Verifica se aceitou o termo atual
    has_accepted = accepted_result.terms_id == latest_term.id

    return TermsCheckResponse(
        accepted=has_accepted,
        latest_terms=TermsResponse.model_validate(latest_term, from_attributes=True),
    )


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


async def get_latest_terms_stmt(
    session: AsyncSession,
):
    latest_terms = (
        select(TermsOfUse).where(TermsOfUse.expired_at.is_(None)).order_by(TermsOfUse.created_at.desc()).limit(1)
    )

    result = await session.execute(latest_terms)
    return result.scalar_one_or_none()


async def get_latest_required_terms_stmt(
    session: AsyncSession,
):
    latest_terms = (
        select(TermsOfUse)
        .where(TermsOfUse.expired_at.is_(None), TermsOfUse.type == "required")
        .order_by(TermsOfUse.created_at.desc())
        .limit(1)
    )

    result = await session.execute(latest_terms)
    return result.scalar_one_or_none()


async def get_user_accepted_terms(session: AsyncSession, user_id: int):
    stmt = (
        select(TermsAcceptance)
        .where(TermsAcceptance.user_id == user_id)
        .order_by(TermsAcceptance.accepted_at.desc())
        .limit(1)
    )

    result = await session.execute(stmt)
    return result.scalar_one_or_none()
