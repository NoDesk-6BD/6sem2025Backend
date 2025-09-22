from typing import Any, Protocol


class PasswordHasherProtocol(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, hashed: str) -> bool: ...


class TokenIssuerProtocol(Protocol):
    def issue(
        self,
        subject: str | int,
        claims: dict[str, Any] | None = None,
        expires_in: int = 3600,
    ) -> str: ...
