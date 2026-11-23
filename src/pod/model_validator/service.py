import uuid

from sqlalchemy.orm import Session

from pod.core.auth import STAFF, Principal, require
from pod.core.problems import not_found
from pod.model_validator import stub
from pod.model_validator.models import ModelValidation
from pod.modeling_workspace import service as workspace


def _out(v: ModelValidation) -> dict:
    return {
        "model_validation_id": v.model_validation_id, "order_id": v.order_id, "model_id": v.model_id,
        "model_version": v.model_version, "print_type": v.print_type, "path": v.path, "result": v.result,
        "errors": v.errors, "fits_printer": v.fits_printer, "splittable": v.splittable,
        "validated_at": v.validated_at,
    }


def create_validation(session: Session, principal: Principal, order_id: uuid.UUID, model_id: uuid.UUID,
                      model_version: int, print_type: str, path: str) -> dict:
    require(principal, *STAFF)
    content = workspace.model_file_for_validation(session, order_id, model_id, model_version)
    outcome = stub.validate(content, print_type)
    validation = ModelValidation(
        order_id=order_id, model_id=model_id, model_version=model_version, print_type=print_type, path=path,
        result=outcome.result, errors=outcome.errors, fits_printer=outcome.fits_printer,
        splittable=None if outcome.fits_printer else outcome.splittable)
    session.add(validation)
    session.flush()
    workspace.on_validation_completed(session, order_id, model_id, model_version, outcome.result,
                                      outcome.errors, outcome.fits_printer, outcome.splittable)
    return _out(validation)


def get_validation(session: Session, principal: Principal, model_validation_id: uuid.UUID) -> dict:
    require(principal, *STAFF)
    validation = session.get(ModelValidation, model_validation_id)
    if validation is None:
        raise not_found("Overenie")
    return _out(validation)
