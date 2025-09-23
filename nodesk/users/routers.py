import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from ..core.di import provider_for
from .models import User
from .protocols import PasswordHasherProtocol
from .schemas import CreateUserRequest, UpdateUserRequest, UserResponse

# Dependencies
PasswordHasher = Annotated[PasswordHasherProtocol, Depends(provider_for(PasswordHasherProtocol))]
Session = Annotated[AsyncSession, Depends(provider_for(AsyncSession))]


users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: CreateUserRequest,
    session: Session,
    hasher: PasswordHasher,
) -> UserResponse:
    email = payload.email.strip().lower()
    cpf_digits = re.sub(r"\D", "", payload.cpf)

    user = User(
        email=email,
        encrypted_password=hasher.hash(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        cpf=cpf_digits,
        vip=payload.vip,
        active=True,
        created_by_id=None,
        updated_by_id=None,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="E-mail or CPF already exists",
        ) from e

    await session.refresh(user)
    return UserResponse.model_validate(user, from_attributes=True)


@users_router.get("/", response_model=list[UserResponse])
async def list_users(
    session: Session,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[UserResponse]:
    stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    res = await session.execute(stmt)
    items = res.scalars().all()
    return [UserResponse.model_validate(u, from_attributes=True) for u in items]


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: Session,
) -> UserResponse:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user, from_attributes=True)


@users_router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    session: Session,
) -> UserResponse:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return UserResponse.model_validate(user, from_attributes=True)

    # Normalize
    if "email" in data and data["email"] is not None:
        data["email"] = data["email"].strip().lower()

    if "cpf" in data and data["cpf"] is not None:
        digits = re.sub(r"\D", "", data["cpf"])
        if len(digits) != 11:
            raise HTTPException(
                status_code=422,
                detail="CPF must contain 11 digits",
            )
        data["cpf"] = digits

    # Early unique checks for clearer 409s
    if "email" in data and data["email"] != user.email:
        exists = await session.scalar(
            select(User.id).where(
                User.email == data["email"],
                User.id != user_id,
            )
        )
        if exists:
            raise HTTPException(
                status_code=409,
                detail="E-mail already exists",
            )

    if "cpf" in data and data["cpf"] != user.cpf:
        exists = await session.scalar(
            select(User.id).where(
                User.cpf == data["cpf"],
                User.id != user_id,
            )
        )
        if exists:
            raise HTTPException(
                status_code=409,
                detail="CPF already exists",
            )

    # Apply changes
    for field, value in data.items():
        setattr(user, field, value)

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        # Fallback for race conditions, etc.
        raise HTTPException(
            status_code=409,
            detail="E-mail or CPF already exists",
        ) from e

    await session.refresh(user)
    return UserResponse.model_validate(user, from_attributes=True)


@users_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    session: Session,
) -> Response:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
