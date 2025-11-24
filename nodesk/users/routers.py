import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from nodesk.users.service import create_user_secure, get_user_decrypted, delete_user_secure, update_user_secure


from ..core.di import provider_for
from .models import Role, User
from .protocols import PasswordHasherProtocol
from .schemas import CreateUserRequest, UpdateUserRequest, UserResponse

# Dependencies
PasswordHasher = Annotated[PasswordHasherProtocol, Depends(provider_for(PasswordHasherProtocol))]
Session = Annotated[AsyncSession, Depends(provider_for(AsyncSession))]


users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: CreateUserRequest, session: Session, hasher: PasswordHasher) -> UserResponse:
    email = payload.email.strip().lower()
    cpf_digits = re.sub(r"\D", "", payload.cpf)

    try:
        user = await create_user_secure(
            session=session,
            email=email,
            cpf=cpf_digits,
            full_name=payload.full_name,
            phone=payload.phone,
            password_hash=hasher.hash(payload.password),
            role=payload.role,
            vip=payload.vip,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    user_data = await get_user_decrypted(session, user.id)

    return UserResponse.model_validate(user_data)


@users_router.get("/", response_model=list[UserResponse])
async def list_users(session: Session, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    res = await session.execute(stmt)
    users = res.scalars().all()
    result = []
    for user in users:
        decrypted = await get_user_decrypted(session, user.id)
        if decrypted:
            result.append(decrypted)
    return result


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: Session,
) -> UserResponse:
    print(f"Vai entrar get_user_decrypted(user_id={user_id})")

    user_data = await get_user_decrypted(session, user_id)
    print(f"Saiu em get_user_decrypted(user_id={user_id})")

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found or missing encryption key")

    return UserResponse.model_validate(user_data)


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
    user_data = await get_user_decrypted(session, user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found or missing encryption key")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return UserResponse.model_validate(user_data)

    # Validate and normalize data
    if "email" in data and data["email"] is not None:
        data["email"] = data["email"].strip().lower()
    if "cpf" in data and data["cpf"] is not None:
        digits = re.sub(r"\D", "", data["cpf"])
        if len(digits) != 11:
            raise HTTPException(status_code=422, detail="CPF must contain 11 digits")
        data["cpf"] = digits
    if "role" in data:
        # Convert role string to Role enum for update_user_secure
        role_str = data["role"] if isinstance(data["role"], str) else data["role"].value
        data["role"] = Role(role_str)

    try:
        updated_user = await update_user_secure(session, user_id, data)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found or missing encryption key")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Get updated user data
    updated_user_data = await get_user_decrypted(session, user_id)
    return UserResponse.model_validate(updated_user_data)


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: Session,
) -> Response:
    deleted = await delete_user_secure(session, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
