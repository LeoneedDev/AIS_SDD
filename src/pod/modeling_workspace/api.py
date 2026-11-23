import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Body, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from pod.core.auth import Principal, current_principal
from pod.core.db import get_session
from pod.modeling_workspace import service

router = APIRouter()

ApprovalState = Literal["waiting_for_review", "in_review", "approved", "rejected", "closed_new_development"]
ModelOrigin = Literal["new_model", "reused_model", "fixed_customer_model"]
ConsentType = Literal["model_fix", "model_split"]


class ModelApprovalCreate(BaseModel):
    model_version: int = Field(ge=1)
    model_origin: ModelOrigin
    note: str | None = Field(None, max_length=2000)


class EmployeeRef(BaseModel):
    employee_id: str
    nickname: str


class HistoryEntry(BaseModel):
    event: Literal["sent_for_approval", "review_started", "approved", "rejected",
                   "revision_submitted", "closed_new_development"]
    occurred_at: datetime
    actor_role: Literal["customer", "modeler", "manager"]
    employee: EmployeeRef | None = None
    model_version: int | None = None
    comment: str | None = None


class ModelApprovalOut(BaseModel):
    model_approval_id: uuid.UUID
    order_id: uuid.UUID
    model_id: uuid.UUID
    model_version: int
    model_origin: ModelOrigin
    state: ApprovalState
    revision_count: int
    free_revisions_remaining: int
    history: list[HistoryEntry]
    created_at: datetime
    updated_at: datetime


class RejectionIn(BaseModel):
    comment: str = Field(min_length=1, max_length=4000)


class RejectionOut(ModelApprovalOut):
    new_paid_development_required: bool


class RevisionIn(BaseModel):
    model_version: int = Field(ge=1)
    note: str | None = Field(None, max_length=2000)


class CustomerConsentIn(BaseModel):
    consent_type: ConsentType
    decision: Literal["granted", "refused"]


class CustomerConsentOut(CustomerConsentIn):
    customer_consent_id: uuid.UUID
    order_id: uuid.UUID
    model_id: uuid.UUID
    recorded_at: datetime
    order_can_be_fulfilled: bool


Auth = Depends(current_principal)
Db = Depends(get_session)
APPROVAL = "/orders/{order_id}/model_approvals/{model_approval_id}"


@router.post("/orders/{order_id}/model_approvals", operation_id="create_model_approval",
             status_code=201, response_model=ModelApprovalOut, tags=["model_approvals"])
def create_model_approval(order_id: uuid.UUID, body: ModelApprovalCreate, principal: Principal = Auth,
                          session: Session = Db, x_correlation_id: str | None = Header(None)):
    return service.create_approval(session, principal, order_id, body.model_version, body.model_origin, body.note)


@router.get("/orders/{order_id}/model_approvals", operation_id="list_model_approvals",
            response_model=list[ModelApprovalOut], tags=["model_approvals"])
def list_model_approvals(order_id: uuid.UUID, principal: Principal = Auth, session: Session = Db,
                         x_correlation_id: str | None = Header(None)):
    return service.list_approvals(session, principal, order_id)


@router.get(APPROVAL, operation_id="get_model_approval", response_model=ModelApprovalOut, tags=["model_approvals"])
def get_model_approval(order_id: uuid.UUID, model_approval_id: uuid.UUID, principal: Principal = Auth,
                       session: Session = Db, x_correlation_id: str | None = Header(None)):
    return service.get_approval(session, principal, order_id, model_approval_id)


@router.post(APPROVAL + "/review_starts", operation_id="start_review", response_model=ModelApprovalOut,
             tags=["model_approvals"])
def start_review(order_id: uuid.UUID, model_approval_id: uuid.UUID, principal: Principal = Auth,
                 session: Session = Db, x_correlation_id: str | None = Header(None)):
    return service.start_review(session, principal, order_id, model_approval_id)


@router.post(APPROVAL + "/approvals", operation_id="approve_model", response_model=ModelApprovalOut,
             tags=["model_approvals"])
def approve_model(order_id: uuid.UUID, model_approval_id: uuid.UUID, principal: Principal = Auth,
                  session: Session = Db, x_correlation_id: str | None = Header(None)):
    return service.approve(session, principal, order_id, model_approval_id)


@router.post(APPROVAL + "/rejections", operation_id="reject_model", response_model=RejectionOut,
             tags=["model_approvals"])
def reject_model(order_id: uuid.UUID, model_approval_id: uuid.UUID, body: RejectionIn = Body(...),
                 principal: Principal = Auth, session: Session = Db, x_correlation_id: str | None = Header(None)):
    return service.reject(session, principal, order_id, model_approval_id, body.comment)


@router.post(APPROVAL + "/revisions", operation_id="submit_revision", response_model=ModelApprovalOut,
             tags=["model_approvals"])
def submit_revision(order_id: uuid.UUID, model_approval_id: uuid.UUID, body: RevisionIn = Body(...),
                    principal: Principal = Auth, session: Session = Db, x_correlation_id: str | None = Header(None)):
    return service.submit_revision(session, principal, order_id, model_approval_id, body.model_version, body.note)


@router.post("/orders/{order_id}/customer_consents", operation_id="record_customer_consent", status_code=201,
             response_model=CustomerConsentOut, tags=["customer_consents"])
def record_customer_consent(order_id: uuid.UUID, body: CustomerConsentIn, principal: Principal = Auth,
                            session: Session = Db, x_correlation_id: str | None = Header(None)):
    return service.record_consent(session, principal, order_id, body.consent_type, body.decision)


@router.get("/orders/{order_id}/customer_consents", operation_id="list_customer_consents",
            response_model=list[CustomerConsentOut], tags=["customer_consents"])
def list_customer_consents(order_id: uuid.UUID, principal: Principal = Auth, session: Session = Db,
                           x_correlation_id: str | None = Header(None)):
    return service.list_consents(session, principal, order_id)
