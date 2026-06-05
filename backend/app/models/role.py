"""Role model — DATA-001."""

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    # Relationships
    users: Mapped[list["User"]] = relationship(back_populates="role")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
