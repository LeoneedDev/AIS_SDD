import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from pod.core.db import Base, utcnow


class ModelValidation(Base):
    __tablename__ = "model_validations"

    model_validation_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(index=True)
    model_id: Mapped[uuid.UUID]
    model_version: Mapped[int]
    print_type: Mapped[str] = mapped_column(String(64))
    path: Mapped[str] = mapped_column(String(8))
    result: Mapped[str] = mapped_column(String(16))
    errors: Mapped[list] = mapped_column(JSON, default=list)
    fits_printer: Mapped[bool]
    splittable: Mapped[bool | None]
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
