from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.di import provider_for
from ..users.models import User
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
        stmt = select(User).where(User.email == email)
        res = await self.session.execute(stmt)
        user = res.scalars().first()
        if not user or not user.active:
            return None
        if not self.hasher.verify(password, user.encrypted_password):
            return None
        return self.token_issuer.issue(
            subject=user.id,
            claims={"email": user.email},
        )
