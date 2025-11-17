# nodesk/users/models.py

from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship
from typing import List, Optional

table_registry = registry()


@table_registry.mapped_as_dataclass(kw_only=True)
class Role:
    __tablename__ = "roles"
    # __table_args__ = (UniqueConstraint("role_name"),) # O autogenerate vai pegar isso

    id: Mapped[int] = mapped_column("role_id", Integer, primary_key=True, init=False, autoincrement=True)
    name: Mapped[str] = mapped_column("role_name", String(50), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship("User", back_populates="role", default_factory=list, init=False)


@table_registry.mapped_as_dataclass(kw_only=True)
class User:
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    email: Mapped[str] = mapped_column(String(255), index=True, unique=True, nullable=False)
    encrypted_password: Mapped[str] = mapped_column(String(255), nullable=False)
    cpf: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    phone: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    vip: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    created_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        remote_side=lambda: [User.id],
        default=None,
        init=False,
    )
    updated_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[updated_by_id],
        remote_side=lambda: [User.id],
        default=None,
        init=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )
    role_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("roles.role_id"), nullable=True, default=None)
    role: Mapped[Optional["Role"]] = relationship("Role", back_populates="users", init=False, lazy="joined")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        init=False,
    )


@table_registry.mapped_as_dataclass(kw_only=True)
class UserKey:
    __tablename__ = "user_keys"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    aes_key: Mapped[str] = mapped_column(String(512), nullable=False)
    iv: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(50), default="AES-256-CBC", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        init=False,
    )


class TermType(str, Enum):
    REQUIRED = "required"  # termos obrigatórios para uso da plataforma
    OPTIONAL = "optional"  # termos opcionais, como marketing


@table_registry.mapped_as_dataclass(kw_only=True)
class TermsOfUse:
    __tablename__ = "terms_of_use"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[TermType] = mapped_column(String(20), nullable=False, default=TermType.REQUIRED)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, init=False
    )

    acceptances: Mapped[List["TermsAcceptance"]] = relationship(
        "TermsAcceptance",
        back_populates="terms",
        cascade="all, delete-orphan",
        default_factory=list,
        init=False,
    )


@table_registry.mapped_as_dataclass(kw_only=True)
class TermsAcceptance:
    __tablename__ = "terms_acceptance"
    __table_args__ = (UniqueConstraint("user_id", "terms_id", name="uix_user_terms"),)  # evita aceite duplicado

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    terms_id: Mapped[int] = mapped_column(ForeignKey("terms_of_use.id"), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        init=False,
    )

    user: Mapped[Optional["User"]] = relationship("User", init=False)
    terms: Mapped[Optional["TermsOfUse"]] = relationship("TermsOfUse", back_populates="acceptances", init=False)
