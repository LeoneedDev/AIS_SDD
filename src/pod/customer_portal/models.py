from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from pod.core.db import Base


class UserAccount(Base):
    """DO-UserAccount (owner AC-CustomerPortal). Heslo iba ako hash (QR-002)."""

    __tablename__ = "user_accounts"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    login: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(16))
    nickname: Mapped[str | None] = mapped_column(String(64))
