import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from pod.core.auth import Principal, current_principal
from pod.core.db import get_session
from pod.model_validator import service

router = APIRouter()


class ModelValidationIn(BaseModel):
    order_id: uuid.UUID
    model_id: uuid.UUID
    model_version: int = Field(ge=1)
    print_type: str
    path: Literal["VAR-1", "VAR-2"]


class ValidationError(BaseModel):
    code: str
    message: str


class ModelValidationOut(BaseModel):
    model_validation_id: uuid.UUID
    order_id: uuid.UUID
    model_id: uuid.UUID
    model_version: int
    print_type: str
    path: Literal["VAR-1", "VAR-2"]
    result: Literal["passed", "failed"]
    errors: list[ValidationError]
    fits_printer: bool
    splittable: bool | None
    validated_at: datetime


@router.post("/model_validations", operation_id="create_model_validation", status_code=201,
             response_model=ModelValidationOut)
def create_model_validation(body: ModelValidationIn, principal: Principal = Depends(current_principal),
                            session: Session = Depends(get_session), x_correlation_id: str | None = Header(None)):
    return service.create_validation(session, principal, body.order_id, body.model_id, body.model_version,
                                     body.print_type, body.path)


@router.get("/model_validations/{model_validation_id}", operation_id="get_model_validation",
            response_model=ModelValidationOut)
def get_model_validation(model_validation_id: uuid.UUID, principal: Principal = Depends(current_principal),
                         session: Session = Depends(get_session), x_correlation_id: str | None = Header(None)):
    return service.get_validation(session, principal, model_validation_id)
