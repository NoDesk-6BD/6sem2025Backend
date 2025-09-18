from typing import Protocol


class PasswordHasherProtocol(Protocol):
    def hash(self, password: str) -> str: ...
