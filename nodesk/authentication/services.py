from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.di import provider_for
from ..users.service import get_user_by_email
from ..users.service_encrypt import EncryptionService
from ..users.models import UserKey
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

    async def authenticate(self, email: str, password: str) -> dict[str, str | int] | None:
        user = await get_user_by_email(self.session, email)
        if not user:
            return None

        if not user.active:
            return None

        if not self.hasher.verify(password, user.encrypted_password):
            return None

        # Get decrypted email for token claims
        from sqlalchemy import select

        stmt_key = select(UserKey).where(UserKey.user_id == user.id)
        user_key = (await self.session.execute(stmt_key)).scalar_one_or_none()
        if not user_key:
            return None

        user_id = user.id
        decrypted_name = (
            EncryptionService.decrypt(user.full_name, user_key.aes_key, user_key.iv) if user.full_name else ""
        )
        decrypted_email = EncryptionService.decrypt(user.email, user_key.aes_key, user_key.iv)

        token = self.token_issuer.issue(
            subject=user.id,
            claims={"id": user_id, "name": decrypted_name, "email": decrypted_email},
        )

        return {
            "access_token": token,
            "user_id": user_id,
            "name": decrypted_name,
            "email": decrypted_email,
        }
