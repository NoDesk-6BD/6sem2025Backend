from datetime import UTC, datetime, timedelta
from typing import Any

import jwt


class JWTTokenIssuer:
    def __init__(self, secret: str, algorithm: str = "HS256") -> None:
        self.secret = secret
        self.algorithm = algorithm

    def issue(
        self,
        subject: str | int,
        claims: dict[str, Any] | None = None,
        expires_in: int = 3600,
    ) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": str(subject),
            "iat": int(now.timestamp()),
        }
        if expires_in:
            payload["exp"] = int((now + timedelta(seconds=expires_in)).timestamp())
        if claims:
            payload.update(claims)
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
