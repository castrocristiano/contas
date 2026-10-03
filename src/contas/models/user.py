import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class AuthProvider(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=150, nullable=False)
    email: str = Field(unique=True, index=True, max_length=255, nullable=False)
    username: str = Field(unique=True, index=True, max_length=100, nullable=False)
    password_hash: str | None = Field(default=None, max_length=255, nullable=True)
    auth_provider: str = Field(
        default=AuthProvider.LOCAL, max_length=20, nullable=False
    )
    google_id: str | None = Field(
        default=None, unique=True, index=True, max_length=255, nullable=True
    )
    avatar_url: str | None = Field(default=None, max_length=1000, nullable=True)
    is_active: bool = Field(default=True, nullable=False)
    is_approved: bool = Field(default=False, nullable=False)
    role: str = Field(default=UserRole.USER, max_length=20, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
