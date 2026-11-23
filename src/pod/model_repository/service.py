import uuid
from datetime import timedelta
from pathlib import Path, PurePosixPath

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pod.core.auth import Principal, require
from pod.core.db import utcnow
from pod.core.problems import Problem, forbidden, not_found
from pod.model_repository.models import Model3D, ModelVersion
from pod.order_orchestrator import service as orders

_storage_dir = Path("var/model_files")
_upload_limit = 10
_upload_period_days: int | None = None


def configure(storage_dir: str, upload_limit: int, upload_period_days: int | None) -> None:
    global _storage_dir, _upload_limit, _upload_period_days
    _storage_dir = Path(storage_dir)
    _upload_limit = upload_limit
    _upload_period_days = upload_period_days


def storage_dir() -> Path:
    return _storage_dir


def model_for_order(session: Session, order_id: uuid.UUID) -> Model3D | None:
    return session.scalars(select(Model3D).where(Model3D.order_id == order_id)).first()


def get_model(session: Session, model_id: uuid.UUID) -> Model3D:
    model = session.get(Model3D, model_id)
    if model is None:
        raise not_found("Model")
    return model


def get_version(session: Session, model_id: uuid.UUID, version: int) -> ModelVersion:
    found = session.scalars(select(ModelVersion).where(
        ModelVersion.model_id == model_id, ModelVersion.version == version)).first()
    if found is None:
        raise not_found("Verzia modelu")
    return found


def latest_version(session: Session, model_id: uuid.UUID) -> ModelVersion | None:
    return session.scalars(select(ModelVersion).where(ModelVersion.model_id == model_id)
                           .order_by(ModelVersion.version.desc())).first()


def read_file(version: ModelVersion) -> bytes:
    return (_storage_dir / version.file_path).read_bytes()


def file_url(version: ModelVersion) -> str:
    return f"/model_files/{version.file_path}"


def mark_validated(session: Session, model_id: uuid.UUID, version: int, result: str) -> None:
    get_version(session, model_id, version).validation_result = result


def _customer_uploads(session: Session, model: Model3D | None):
    if model is None:
        return 0, None
    stmt = select(func.count(), func.min(ModelVersion.uploaded_at)).where(
        ModelVersion.model_id == model.model_id, ModelVersion.uploaded_by_role == "customer")
    if _upload_period_days is not None:
        stmt = stmt.where(ModelVersion.uploaded_at >= utcnow() - timedelta(days=_upload_period_days))
    count, oldest = session.execute(stmt).one()
    period_ends_at = oldest + timedelta(days=_upload_period_days) if (oldest and _upload_period_days) else None
    return count, period_ends_at


def upload_version(session: Session, principal: Principal, order_id: uuid.UUID,
                   file_name: str, content: bytes, description: str | None) -> dict:
    require(principal, "customer", "modeler")
    order = orders.get_order_for(session, order_id, principal, for_update=True)
    if order.print_started:
        raise Problem(409, "urn:problem:print_already_started", "Tlač už začala, model nemožno meniť.")

    model = model_for_order(session, order_id)
    remaining = None
    if principal.role == "customer":
        count, period_ends_at = _customer_uploads(session, model)
        if count >= _upload_limit:
            raise Problem(429, "urn:problem:upload_limit_reached",
                          f"Limit {_upload_limit} vlastných nahraní je vyčerpaný; ďalšie overenie je za doplatok (BR-004).",
                          upload_limit=_upload_limit, uploads_in_period=count,
                          period_ends_at=period_ends_at.isoformat() if period_ends_at else None)
        remaining = _upload_limit - count - 1
    elif order.path == "VAR-2":
        from pod.modeling_workspace import service as workspace
        if not workspace.has_granted_consent(session, order_id, "model_fix"):
            raise forbidden("Model zákazníka možno upraviť iba s jeho súhlasom (BR-005).")

    if model is None:
        model = Model3D(order_id=order_id, description=description or order.description)
        session.add(model)
        session.flush()
    elif description:
        model.description = description

    last = latest_version(session, model.model_id)
    number = (last.version if last else 0) + 1
    safe_name = PurePosixPath(file_name or "model.stl").name
    relative = f"{model.model_id}/{number}/{safe_name}"
    target = _storage_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    version = ModelVersion(model_id=model.model_id, version=number, file_path=relative,
                           file_name=safe_name, uploaded_by_role=principal.role)
    session.add(version)
    session.flush()
    return {
        "model_id": model.model_id, "order_id": order_id, "version": number,
        "uploaded_by_role": principal.role, "uploaded_at": version.uploaded_at,
        "customer_uploads_remaining": remaining,
    }


def search_reusable(session: Session, principal: Principal, query: str, limit: int) -> list[dict]:
    require(principal, "modeler", "manager")
    from pod.order_orchestrator.models import Order

    validated = select(ModelVersion.model_id).where(ModelVersion.validation_result == "passed")
    rows = session.scalars(
        select(Model3D).join(Order, Order.order_id == Model3D.order_id)
        .where(Order.sharing_allowed.is_(True), Model3D.model_id.in_(validated),
               Model3D.description.ilike(f"%{query}%"))
        .order_by(Model3D.created_at.desc()).limit(limit))
    return [_summary(session, m) for m in rows]


def _summary(session: Session, model: Model3D) -> dict:
    last = latest_version(session, model.model_id)
    return {"model_id": model.model_id, "latest_version": last.version if last else 1,
            "description": model.description}


def model_detail(session: Session, principal: Principal, model_id: uuid.UUID) -> dict:
    model = get_model(session, model_id)
    order = orders.get_order(session, model.order_id)
    if principal.role == "customer" and order.customer_id != principal.subject_id:
        raise forbidden("Model nepatrí zákazníkovi.")
    last = latest_version(session, model_id)
    if last is None:
        raise not_found("Verzia modelu")
    return {
        **_summary(session, model),
        "file_format": PurePosixPath(last.file_name).suffix.lstrip(".").lower() or "unknown",
        "file_url": file_url(last),
        "sharing_allowed": order.sharing_allowed,
        "metadata": {"validation_result": last.validation_result},
    }
