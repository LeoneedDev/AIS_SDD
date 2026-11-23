import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from pod.notifier.models import Notification


def notify(session: Session, order_id: uuid.UUID, customer_id: str, kind: str, message: str) -> Notification:
    notification = Notification(order_id=order_id, customer_id=customer_id, kind=kind, message=message)
    session.add(notification)
    session.flush()
    return notification


def for_order(session: Session, order_id: uuid.UUID) -> list[Notification]:
    return list(session.scalars(
        select(Notification).where(Notification.order_id == order_id).order_by(Notification.created_at)))
