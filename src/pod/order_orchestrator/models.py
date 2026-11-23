import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from pod.core.db import Base, utcnow


class Order(Base):
    """DO-Order (owner AC-OrderOrchestrator). Jedna objednávka = jeden model."""

    __tablename__ = "orders"

    order_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[str] = mapped_column(String(64), index=True)
    path: Mapped[str] = mapped_column(String(8))
    description: Mapped[str] = mapped_column(String(4000), default="")
    sharing_allowed: Mapped[bool] = mapped_column(default=False)
    print_started: Mapped[bool] = mapped_column(default=False)
    print_status: Mapped[str] = mapped_column(String(32), default="not_ready")
    split_into_parts: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ModelingTask(Base):
    """DO-ModelingTask (owner AC-OrderOrchestrator)."""

    __tablename__ = "modeling_tasks"

    modeling_task_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(index=True)
    kind: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="open")
    note: Mapped[str] = mapped_column(String(4000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
