import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pod.core.db import Base, utcnow


class ModelApproval(Base):
    """DO-ModelApproval (owner AC-ModelingWorkspace, časť DO-Order)."""

    __tablename__ = "model_approvals"

    model_approval_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(index=True)
    model_id: Mapped[uuid.UUID]
    model_version: Mapped[int]
    model_origin: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(32))
    revision_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    history: Mapped[list["ApprovalHistoryEntry"]] = relationship(
        order_by="ApprovalHistoryEntry.occurred_at", lazy="selectin")


class ApprovalHistoryEntry(Base):
    __tablename__ = "model_approval_history"

    entry_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    model_approval_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_approvals.model_approval_id"), index=True)
    event: Mapped[str] = mapped_column(String(32))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    actor_role: Mapped[str] = mapped_column(String(16))
    employee_id: Mapped[str | None] = mapped_column(String(64))
    employee_nickname: Mapped[str | None] = mapped_column(String(64))
    model_version: Mapped[int | None]
    comment: Mapped[str | None] = mapped_column(String(4000))


class CustomerConsent(Base):
    """Otázka na zákazníka (decision = None) a jeho rozhodnutie (BR-005, BR-009)."""

    __tablename__ = "customer_consents"

    customer_consent_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(index=True)
    model_id: Mapped[uuid.UUID]
    consent_type: Mapped[str] = mapped_column(String(16))
    decision: Mapped[str | None] = mapped_column(String(16), default=None)
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
