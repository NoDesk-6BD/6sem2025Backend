from passlib.context import CryptContext


class Argon2PasswordHasher:
    def __init__(
        self,
        time_cost: int = 3,
        memory_cost: int = 65536,  # KiB (~64 MiB)
        parallelism: int = 2,
    ) -> None:
        self._ctx = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
            argon2__type="ID",
            argon2__time_cost=time_cost,
            argon2__memory_cost=memory_cost,
            argon2__parallelism=parallelism,
        )

    def hash(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self._ctx.verify(password, hashed)
