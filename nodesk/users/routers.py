import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)
from nodesk.users.service import create_user_secure, get_user_decrypted, delete_user_secure
from nodesk.users.service_encrypt import EncryptionService


from ..core.di import provider_for
from .models import User, UserKey
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
            vip=payload.vip,
        )
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail="E-mail or CPF already exists") from e

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

    user = await session.get(User, user_id)
    user_key = await session.scalar(select(UserKey).where(UserKey.user_id == user_id))
    key, iv = user_key.aes_key, user_key.iv

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return UserResponse.model_validate(user_data)

    if "email" in data and data["email"] is not None:
        data["email"] = data["email"].strip().lower()
    if "cpf" in data and data["cpf"] is not None:
        digits = re.sub(r"\D", "", data["cpf"])
        if len(digits) != 11:
            raise HTTPException(status_code=422, detail="CPF must contain 11 digits")
        data["cpf"] = digits

    if "email" in data and data["email"] != user_data["email"]:
        # Check for duplicate email by decrypting all users' emails
        stmt = select(User, UserKey).join(UserKey, User.id == UserKey.user_id).where(User.id != user_id)
        result = await session.execute(stmt)
        for other_user, other_key in result.all():
            decrypted_email = EncryptionService.decrypt(other_user.email, other_key.aes_key, other_key.iv)
            if decrypted_email.lower() == data["email"].lower():
                raise HTTPException(status_code=409, detail="E-mail already exists")

    if "cpf" in data and data["cpf"] != user_data["cpf"]:
        # Check for duplicate CPF by decrypting all users' CPFs
        stmt = select(User, UserKey).join(UserKey, User.id == UserKey.user_id).where(User.id != user_id)
        result = await session.execute(stmt)
        for other_user, other_key in result.all():
            decrypted_cpf = EncryptionService.decrypt(other_user.cpf, other_key.aes_key, other_key.iv)
            if decrypted_cpf == data["cpf"]:
                raise HTTPException(status_code=409, detail="CPF already exists")

    if "email" in data:
        user.email = EncryptionService.encrypt(data["email"], key, iv)
        user_data["email"] = data["email"]
    if "cpf" in data:
        user.cpf = EncryptionService.encrypt(data["cpf"], key, iv)
        user_data["cpf"] = data["cpf"]
    if "full_name" in data:
        user.full_name = EncryptionService.encrypt(data["full_name"], key, iv)
        user_data["full_name"] = data["full_name"]
    if "phone" in data:
        user.phone = EncryptionService.encrypt(data["phone"], key, iv)
        user_data["phone"] = data["phone"]

    if "vip" in data:
        user.vip = data["vip"]
        user_data["vip"] = data["vip"]
    if "active" in data:
        user.active = data["active"]
        user_data["active"] = data["active"]

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail="E-mail or CPF already exists") from e

    return UserResponse.model_validate(user_data)


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: Session,
) -> Response:
    deleted = await delete_user_secure(session, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
