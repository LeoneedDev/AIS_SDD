import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from pod.core.auth import Principal, current_principal
from pod.core.db import get_session
from pod.model_repository import service

router = APIRouter()


class ModelVersionOut(BaseModel):
    model_id: uuid.UUID
    order_id: uuid.UUID
    version: int
    uploaded_by_role: Literal["customer", "modeler"]
    uploaded_at: datetime
    customer_uploads_remaining: int | None = None


class ModelSummaryOut(BaseModel):
    model_id: uuid.UUID
    latest_version: int
    description: str | None = None


class ModelOut(ModelSummaryOut):
    file_format: str
    file_url: str
    sharing_allowed: bool
    metadata: dict = {}


@router.post("/orders/{order_id}/model_versions", operation_id="upload_model_version",
             status_code=201, response_model=ModelVersionOut)
def upload_model_version(order_id: uuid.UUID, file: UploadFile = File(...), description: str | None = Form(None),
                         principal: Principal = Depends(current_principal), session: Session = Depends(get_session),
                         x_correlation_id: str | None = Header(None)):
    return service.upload_version(session, principal, order_id, file.filename or "model.stl",
                                  file.file.read(), description)


@router.get("/reusable_models", operation_id="search_reusable_models", response_model=list[ModelSummaryOut])
def search_reusable_models(query: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=100),
                           principal: Principal = Depends(current_principal), session: Session = Depends(get_session),
                           x_correlation_id: str | None = Header(None)):
    return service.search_reusable(session, principal, query, limit)


@router.get("/models/{model_id}", operation_id="get_model", response_model=ModelOut)
def get_model(model_id: uuid.UUID, principal: Principal = Depends(current_principal),
              session: Session = Depends(get_session), x_correlation_id: str | None = Header(None)):
    return service.model_detail(session, principal, model_id)
