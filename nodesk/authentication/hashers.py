from argon2 import PasswordHasher as _A2
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError
from argon2.low_level import Type


class Argon2PasswordHasher:
    def __init__(
        self,
        time_cost: int = 3,
        memory_cost: int = 65536,  # KiB (64 MiB)
        parallelism: int = 2,
        hash_len: int = 32,
        salt_len: int = 16,
    ) -> None:
        self._ph = _A2(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=hash_len,
            salt_len=salt_len,
            type=Type.ID,
        )

    def hash(self, password: str) -> str:
        return self._ph.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return self._ph.verify(hashed, password)
        except (VerifyMismatchError, InvalidHash, VerificationError):
            return False
