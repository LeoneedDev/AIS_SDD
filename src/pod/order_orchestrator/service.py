import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from pod.core.auth import Principal
from pod.core.problems import forbidden, not_found
from pod.order_orchestrator.models import ModelingTask, Order

NOT_READY = "not_ready"
READY_FOR_PRINT = "ready_for_print"
CANNOT_BE_FULFILLED = "cannot_be_fulfilled"
PRINTING = "printing"


def create_order(session: Session, customer_id: str, path: str, description: str = "",
                 sharing_allowed: bool = False) -> Order:
    order = Order(customer_id=customer_id, path=path, description=description, sharing_allowed=sharing_allowed)
    session.add(order)
    session.flush()
    return order


def get_order(session: Session, order_id: uuid.UUID, *, for_update: bool = False) -> Order:
    stmt = select(Order).where(Order.order_id == order_id)
    if for_update:
        stmt = stmt.with_for_update()
    order = session.scalars(stmt).first()
    if order is None:
        raise not_found("Objednávka")
    return order


def get_order_for(session: Session, order_id: uuid.UUID, principal: Principal, *, for_update: bool = False) -> Order:
    order = get_order(session, order_id, for_update=for_update)
    if principal.role == "customer" and order.customer_id != principal.subject_id:
        raise forbidden("Objednávka nepatrí zákazníkovi.")
    return order


def set_sharing(session: Session, order_id: uuid.UUID, allowed: bool) -> None:
    get_order(session, order_id).sharing_allowed = allowed


def add_task(session: Session, order_id: uuid.UUID, kind: str, note: str = "") -> ModelingTask:
    task = ModelingTask(order_id=order_id, kind=kind, note=note)
    session.add(task)
    session.flush()
    return task


def open_tasks(session: Session, order_id: uuid.UUID) -> list[ModelingTask]:
    return list(session.scalars(select(ModelingTask).where(
        ModelingTask.order_id == order_id, ModelingTask.status == "open").order_by(ModelingTask.created_at)))


def set_print_status(session: Session, order_id: uuid.UUID, status: str, *, split: bool | None = None) -> None:
    order = get_order(session, order_id)
    if order.print_status == PRINTING:
        return
    order.print_status = status
    if split is not None:
        order.split_into_parts = split
