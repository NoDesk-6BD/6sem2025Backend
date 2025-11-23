import re
from sqlalchemy import select
from nodesk.users.models import User, UserKey, Role
from nodesk.users.service_encrypt import EncryptionService
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user_secure(
    session: AsyncSession,
    email: str,
    cpf: str,
    full_name: str | None,
    phone: str | None,
    password_hash: str,
    role: "Role" = None,
    vip: bool = False,
) -> User:
    # 1️⃣ Gera chave + IV
    key_b64, iv_b64 = EncryptionService.generate_key_iv()

    # 2️⃣ Criptografa todos os campos sensíveis
    email_enc = EncryptionService.encrypt(email, key_b64, iv_b64)
    cpf_enc = EncryptionService.encrypt(cpf, key_b64, iv_b64)
    full_name_enc = EncryptionService.encrypt(full_name, key_b64, iv_b64) if full_name else None
    phone_enc = EncryptionService.encrypt(phone, key_b64, iv_b64) if phone else None

    # 3️⃣ Cria usuário com campos criptografados (mantendo nomes originais)
    user = User(
        email=email_enc,
        cpf=cpf_enc,
        full_name=full_name_enc,
        phone=phone_enc,
        encrypted_password=password_hash,
        role=role if role is not None else Role.VIEWER,
        vip=vip,
        active=True,
        created_by_id=None,
        updated_by_id=None,
    )
    session.add(user)
    await session.flush()  # garante que user.id existe

    # 4️⃣ Salva chave no UserKey
    user_key = UserKey(user_id=user.id, aes_key=key_b64, iv=iv_b64)
    session.add(user_key)

    await session.commit()
    await session.refresh(user)
    return user


async def get_user_decrypted(session: AsyncSession, user_id: int) -> dict | None:
    """Retorna dados descriptografados do usuário."""
    user = await session.get(User, user_id)
    if not user:
        return None

    stmt = select(UserKey).where(UserKey.user_id == user_id)
    res = await session.execute(stmt)
    user_key = res.scalar_one_or_none()
    if not user_key:
        return None

    key, iv = user_key.aes_key, user_key.iv

    return {
        "id": user.id,
        "email": EncryptionService.decrypt(user.email, key, iv),
        "cpf": EncryptionService.decrypt(user.cpf, key, iv),
        "full_name": EncryptionService.decrypt(user.full_name, key, iv) if user.full_name else None,
        "phone": EncryptionService.decrypt(user.phone, key, iv) if user.phone else None,
        "role": user.role.value if isinstance(user.role, Role) else user.role,
        "vip": user.vip,
        "active": user.active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


async def anonymize_user(session: AsyncSession, user_id: int):
    """Remove a chave de descriptografia — tornando os dados irrecuperáveis."""
    key_entry = await session.execute(select(UserKey).where(UserKey.user_id == user_id))
    key_entry = key_entry.scalar_one_or_none()
    if key_entry:
        await session.delete(key_entry)
        await session.commit()


async def update_user_secure(session: AsyncSession, user_id: int, data: dict) -> User | None:
    """Atualiza um usuário criptografando campos sensíveis."""
    user = await session.get(User, user_id)
    if not user:
        return None

    # Busca chave do usuário
    stmt = select(UserKey).where(UserKey.user_id == user_id)
    res = await session.execute(stmt)
    user_key = res.scalar_one_or_none()
    if not user_key:
        return None

    key, iv = user_key.aes_key, user_key.iv

    # Criptografa apenas os campos alterados
    if "email" in data and data["email"]:
        data["email"] = EncryptionService.encrypt(data["email"].strip().lower(), key, iv)
    if "cpf" in data and data["cpf"]:
        data["cpf"] = EncryptionService.encrypt(re.sub(r"\D", "", data["cpf"]), key, iv)
    if "full_name" in data and data["full_name"]:
        data["full_name"] = EncryptionService.encrypt(data["full_name"], key, iv)
    if "phone" in data and data["phone"]:
        data["phone"] = EncryptionService.encrypt(data["phone"], key, iv)

    # Aplica mudanças
    for field, value in data.items():
        setattr(user, field, value)

    await session.commit()
    await session.refresh(user)
    return user


async def delete_user_secure(session: AsyncSession, user_id: int) -> bool:
    """Deleta o usuário e sua chave de criptografia."""
    user = await session.get(User, user_id)
    if not user:
        return False

    # Deleta a chave AES do usuário, se existir
    user_key = await session.get(UserKey, user_id)
    if user_key:
        await session.delete(user_key)

    # Deleta o usuário
    await session.delete(user)
    await session.commit()
    return True
