import re
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from nodesk.core.database.session import get_session
from nodesk.users.service import create_user_secure, get_user_decrypted
from nodesk.users.service_encrypt import EncryptionService  # função que implementamos antes


from ..core.di import provider_for
from .models import User, UserKey, Role
from .protocols import PasswordHasherProtocol
from .schemas import CreateUserRequest, UpdateUserRequest, UserResponse, RoleResponse

# Dependencies
PasswordHasher = Annotated[PasswordHasherProtocol, Depends(provider_for(PasswordHasherProtocol))]
Session = Annotated[AsyncSession, Depends(provider_for(AsyncSession))]


users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get(
    "/roles",
    response_model=List[RoleResponse],
    summary="List Roles",  # <--- Define o título no Swagger
)
async def list_roles(session: Session) -> List[RoleResponse]:
    """
    Lista todos os papéis (roles) disponíveis no sistema.
    (Executa: SELECT * FROM public.roles)
    """
    stmt = select(Role).order_by(Role.id)
    result = await session.execute(stmt)
    roles = result.scalars().all()

    return roles


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
            role_id=payload.role_id,
        )
    except IntegrityError as e:
        await session.rollback()
        # Verifica se o erro é de chave duplicada (Postgres error code 23505) ou similar
        raise HTTPException(status_code=409, detail="E-mail or CPF already exists") from e

    # Busca os dados descriptografados para responder
    user_data = await get_user_decrypted(session, user.id)

    # Validação extra de segurança: user_data nunca deve ser None logo após criar
    if not user_data:
        raise HTTPException(status_code=500, detail="Failed to retrieve created user data")

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
    session: AsyncSession = Depends(get_session),
) -> UserResponse:
    user_data = await get_user_decrypted(session, user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found or missing encryption key")

    user = await session.get(User, user_id)
    # Busca a chave para criptografar os novos dados
    user_key = await session.scalar(select(UserKey).where(UserKey.user_id == user_id))
    if not user_key:
        raise HTTPException(status_code=404, detail="Encryption key not found")
    key, iv = user_key.aes_key, user_key.iv

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return UserResponse.model_validate(user_data)

    # Normalizações
    if "email" in data and data["email"] is not None:
        data["email"] = data["email"].strip().lower()
    if "cpf" in data and data["cpf"] is not None:
        digits = re.sub(r"\D", "", data["cpf"])
        if len(digits) != 11:
            raise HTTPException(status_code=422, detail="CPF must contain 11 digits")
        data["cpf"] = digits

    # Verificações de unicidade (se mudou email ou cpf)
    if "email" in data and data["email"] != user_data["email"]:
        exists = await session.scalar(select(User.id).where(User.email == data["email"], User.id != user_id))
        if exists:
            raise HTTPException(status_code=409, detail="E-mail already exists")

    if "cpf" in data and data["cpf"] != user_data["cpf"]:
        exists = await session.scalar(select(User.id).where(User.cpf == data["cpf"], User.id != user_id))
        if exists:
            raise HTTPException(status_code=409, detail="CPF already exists")

    # Atualiza campos criptografados
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
    # Atualiza campos simples
    if "vip" in data:
        user.vip = data["vip"]
        user_data["vip"] = data["vip"]
    if "active" in data:
        user.active = data["active"]
        user_data["active"] = data["active"]
    if "role_id" in data:
        user.role_id = data["role_id"]
        user_data["role_id"] = data["role_id"]

    try:
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail="E-mail or CPF already exists") from e

    return UserResponse.model_validate(user_data)


@users_router.delete("/{user_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_key(
    user_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """
    Deleta a chave de criptografia do usuário.
    Isso aciona o TRIGGER no banco que define active=False e apaga os dados legíveis.
    """
    user_key = await session.get(UserKey, user_id)
    if not user_key:
        raise HTTPException(status_code=404, detail="Encryption key not found for user")

    await session.delete(user_key)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
