import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from pod.core.auth import STAFF, Principal, current_principal, require
from pod.core.db import get_session
from pod.core.problems import Problem
from pod.order_orchestrator import service
from pod.order_orchestrator.models import Order

router = APIRouter()

PrintStatus = Literal["not_ready", "ready_for_print", "printing", "cannot_be_fulfilled"]


class OrderCreate(BaseModel):
    path: Literal["VAR-1", "VAR-2"]
    description: str = Field(min_length=1, max_length=4000)
    sharing_allowed: bool = False


class OrderSummary(BaseModel):
    order_id: uuid.UUID
    path: Literal["VAR-1", "VAR-2"]
    description: str
    print_status: PrintStatus
    created_at: datetime


def _out(order: Order) -> dict:
    return {"order_id": order.order_id, "path": order.path, "description": order.description,
            "print_status": order.print_status, "created_at": order.created_at}


@router.get("/orders", operation_id="list_orders", response_model=list[OrderSummary])
def list_orders(limit: int = Query(50, ge=1, le=100), principal: Principal = Depends(current_principal),
                db: Session = Depends(get_session), x_correlation_id: str | None = Header(None)):
    stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
    if principal.role == "customer":
        stmt = stmt.where(Order.customer_id == principal.subject_id)
    return [_out(o) for o in db.scalars(stmt)]


@router.post("/orders", operation_id="create_order", status_code=201, response_model=OrderSummary)
def create_order(body: OrderCreate, principal: Principal = Depends(current_principal),
                 db: Session = Depends(get_session), x_correlation_id: str | None = Header(None)):
    require(principal, "customer")
    return _out(service.create_order(db, principal.subject_id, body.path, body.description, body.sharing_allowed))


@router.post("/orders/{order_id}/print_jobs", operation_id="start_print", response_model=OrderSummary)
def start_print(order_id: uuid.UUID, principal: Principal = Depends(current_principal),
                db: Session = Depends(get_session), x_correlation_id: str | None = Header(None)):
    require(principal, *STAFF)
    order = service.get_order(db, order_id, for_update=True)
    if order.print_status != service.READY_FOR_PRINT:
        raise Problem(409, "urn:problem:not_ready_for_print",
                      "Model ešte nemá súhlas zákazníka alebo neprešiel kontrolou tlačiteľnosti (BR-001).")
    order.print_status = service.PRINTING
    order.print_started = True
    return _out(order)
