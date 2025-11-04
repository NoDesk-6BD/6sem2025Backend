from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nodesk.users.service_encrypt import EncryptionService

from ..core.di import provider_for
from ..users.models import User, UserKey
from .protocols import PasswordHasherProtocol, TokenIssuerProtocol

# Dependencies
Session = Annotated[AsyncSession, Depends(provider_for(AsyncSession))]
PasswordHasher = Annotated[PasswordHasherProtocol, Depends(provider_for(PasswordHasherProtocol))]
TokenIssuer = Annotated[TokenIssuerProtocol, Depends(provider_for(TokenIssuerProtocol))]


class AuthenticationService:
    def __init__(
        self,
        session: Session,
        hasher: PasswordHasher,
        token_issuer: TokenIssuer,
    ) -> None:
        self.session = session
        self.hasher = hasher
        self.token_issuer = token_issuer

    async def authenticate(self, email: str, password: str) -> str | None:
        stmt = select(User).join(UserKey)
        res = await self.session.execute(stmt)
        users = res.scalars().all()

        for user in users:
            stmt_key = select(UserKey).where(UserKey.user_id == user.id)
            user_key = (await self.session.execute(stmt_key)).scalars().first()
            if not user_key:
                continue

            key, iv = user_key.aes_key, user_key.iv
            decrypted_email = EncryptionService.decrypt(user.email, key, iv)

            if decrypted_email.lower() == email.lower():
                if not user.active:
                    return None
                if not self.hasher.verify(password, user.encrypted_password):
                    return None
                return self.token_issuer.issue(
                    subject=user.id,
                    claims={"email": decrypted_email},
                )

        return None
