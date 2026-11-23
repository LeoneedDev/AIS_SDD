import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from pod.core.auth import STAFF, Principal, require
from pod.core.db import utcnow
from pod.core.problems import Problem, not_found
from pod.model_repository import service as repository
from pod.model_validator.models import ModelValidation
from pod.modeling_workspace.models import ApprovalHistoryEntry, CustomerConsent, ModelApproval
from pod.notifier import service as notifier
from pod.order_orchestrator import service as orders

FREE_REVISIONS = 2
ACTIVE_STATES = ("waiting_for_review", "in_review", "rejected")


def _invalid(approval: ModelApproval, detail: str) -> Problem:
    return Problem(409, "urn:problem:invalid_state_transition", detail, current_state=approval.state)


def _history(session: Session, approval: ModelApproval, principal: Principal | None, event: str,
             comment: str | None = None) -> None:
    role = principal.role if principal else "modeler"
    staff = principal is not None and principal.is_staff
    session.add(ApprovalHistoryEntry(
        model_approval_id=approval.model_approval_id, event=event, actor_role=role,
        employee_id=principal.subject_id if staff else None,
        employee_nickname=(principal.nickname or principal.subject_id) if staff else None,
        model_version=approval.model_version, comment=comment))
    approval.updated_at = utcnow()
    session.flush()
    session.refresh(approval, ["history"])


def approval_out(approval: ModelApproval) -> dict:
    return {
        "model_approval_id": approval.model_approval_id, "order_id": approval.order_id,
        "model_id": approval.model_id, "model_version": approval.model_version,
        "model_origin": approval.model_origin, "state": approval.state,
        "revision_count": approval.revision_count,
        "free_revisions_remaining": max(FREE_REVISIONS - approval.revision_count, 0),
        "history": [{
            "event": h.event, "occurred_at": h.occurred_at, "actor_role": h.actor_role,
            "employee": {"employee_id": h.employee_id, "nickname": h.employee_nickname} if h.employee_id else None,
            "model_version": h.model_version, "comment": h.comment,
        } for h in approval.history],
        "created_at": approval.created_at, "updated_at": approval.updated_at,
    }


# --- model approvals ---------------------------------------------------------

def create_approval(session: Session, principal: Principal, order_id: uuid.UUID, model_version: int,
                    model_origin: str, note: str | None) -> dict:
    require(principal, *STAFF)
    order = orders.get_order_for(session, order_id, principal, for_update=True)
    model = repository.model_for_order(session, order_id)
    if model is None:
        raise not_found("Model objednávky")
    repository.get_version(session, model.model_id, model_version)
    active = session.scalars(select(ModelApproval).where(
        ModelApproval.order_id == order_id, ModelApproval.state.in_(ACTIVE_STATES))).first()
    if active is not None:
        raise Problem(409, "urn:problem:active_approval_exists",
                      "K objednávke už existuje aktívny záznam schválenia.", current_state=active.state)
    approval = ModelApproval(order_id=order_id, model_id=model.model_id, model_version=model_version,
                             model_origin=model_origin, state="waiting_for_review")
    session.add(approval)
    session.flush()
    _history(session, approval, principal, "sent_for_approval", note)
    notifier.notify(session, order_id, order.customer_id, "approval_requested",
                    "Model je pripravený na vaše schválenie.")
    return approval_out(approval)


def list_approvals(session: Session, principal: Principal, order_id: uuid.UUID) -> list[dict]:
    orders.get_order_for(session, order_id, principal)
    rows = session.scalars(select(ModelApproval).where(ModelApproval.order_id == order_id)
                           .order_by(ModelApproval.created_at.desc()))
    return [approval_out(a) for a in rows]


def _load(session: Session, principal: Principal, order_id: uuid.UUID, approval_id: uuid.UUID,
          *, for_update: bool = False) -> ModelApproval:
    orders.get_order_for(session, order_id, principal)
    stmt = select(ModelApproval).where(ModelApproval.model_approval_id == approval_id,
                                       ModelApproval.order_id == order_id)
    if for_update:
        stmt = stmt.with_for_update()
    approval = session.scalars(stmt).first()
    if approval is None:
        raise not_found("Záznam schválenia")
    return approval


def get_approval(session: Session, principal: Principal, order_id: uuid.UUID, approval_id: uuid.UUID) -> dict:
    return approval_out(_load(session, principal, order_id, approval_id))


def start_review(session: Session, principal: Principal, order_id: uuid.UUID, approval_id: uuid.UUID) -> dict:
    require(principal, "customer")
    approval = _load(session, principal, order_id, approval_id, for_update=True)
    if approval.state != "waiting_for_review":
        raise _invalid(approval, "Model už bol otvorený alebo sa naň nečaká.")
    approval.state = "in_review"
    _history(session, approval, principal, "review_started")
    return approval_out(approval)


def approve(session: Session, principal: Principal, order_id: uuid.UUID, approval_id: uuid.UUID) -> dict:
    require(principal, "customer")
    approval = _load(session, principal, order_id, approval_id, for_update=True)
    if approval.state != "in_review":
        raise _invalid(approval, "Schváliť možno iba model, ktorý zákazník otvoril (in_review).")
    approval.state = "approved"
    _history(session, approval, principal, "approved")
    orders.add_task(session, order_id, "printability_check",
                    f"Skontrolovať tlačiteľnosť verzie {approval.model_version} (INT-005).")
    reevaluate_print(session, order_id)
    return approval_out(approval)


def reject(session: Session, principal: Principal, order_id: uuid.UUID, approval_id: uuid.UUID,
           comment: str) -> dict:
    require(principal, "customer")
    approval = _load(session, principal, order_id, approval_id, for_update=True)
    if approval.state != "in_review":
        raise _invalid(approval, "Nesúhlas možno vyjadriť iba k otvorenému modelu (in_review).")
    approval.state = "rejected"
    _history(session, approval, principal, "rejected", comment)
    paid = approval.revision_count >= FREE_REVISIONS
    order = orders.get_order(session, order_id)
    if paid:
        approval.state = "closed_new_development"
        _history(session, approval, None, "closed_new_development")
        notifier.notify(session, order_id, order.customer_id, "new_paid_development",
                        "Bezplatné revízie sú vyčerpané; ďalšia úprava je nový platený vývoj modelu (BR-002).")
    else:
        orders.add_task(session, order_id, "revision", comment)
    return {**approval_out(approval), "new_paid_development_required": paid}


def submit_revision(session: Session, principal: Principal, order_id: uuid.UUID, approval_id: uuid.UUID,
                    model_version: int, note: str | None) -> dict:
    require(principal, "modeler")
    approval = _load(session, principal, order_id, approval_id, for_update=True)
    if approval.state != "rejected" or approval.revision_count >= FREE_REVISIONS:
        raise _invalid(approval, "Revíziu možno poslať iba po nesúhlase zákazníka a v rámci 2 bezplatných revízií.")
    repository.get_version(session, approval.model_id, model_version)
    approval.revision_count += 1
    approval.model_version = model_version
    approval.state = "waiting_for_review"
    _history(session, approval, principal, "revision_submitted", note)
    order = orders.get_order(session, order_id)
    notifier.notify(session, order_id, order.customer_id, "approval_requested",
                    "Upravený model (nová revízia) je pripravený na vaše schválenie.")
    return approval_out(approval)


# --- customer consents ---------------------------------------------------------

def has_granted_consent(session: Session, order_id: uuid.UUID, consent_type: str) -> bool:
    return session.scalars(select(CustomerConsent).where(
        CustomerConsent.order_id == order_id, CustomerConsent.consent_type == consent_type,
        CustomerConsent.decision == "granted")).first() is not None


def _ask(session: Session, order_id: uuid.UUID, model_id: uuid.UUID, consent_type: str) -> None:
    open_question = session.scalars(select(CustomerConsent).where(
        CustomerConsent.order_id == order_id, CustomerConsent.consent_type == consent_type,
        CustomerConsent.decision.is_(None))).first()
    if open_question is None:
        session.add(CustomerConsent(order_id=order_id, model_id=model_id, consent_type=consent_type))
        session.flush()


def _consent_out(session: Session, c: CustomerConsent) -> dict:
    order = orders.get_order(session, c.order_id)
    return {"customer_consent_id": c.customer_consent_id, "order_id": c.order_id, "model_id": c.model_id,
            "consent_type": c.consent_type, "decision": c.decision, "recorded_at": c.recorded_at,
            "order_can_be_fulfilled": order.print_status != orders.CANNOT_BE_FULFILLED}


def record_consent(session: Session, principal: Principal, order_id: uuid.UUID, consent_type: str,
                   decision: str) -> dict:
    require(principal, "customer")
    order = orders.get_order_for(session, order_id, principal, for_update=True)
    question = session.scalars(select(CustomerConsent).where(
        CustomerConsent.order_id == order_id, CustomerConsent.consent_type == consent_type,
        CustomerConsent.decision.is_(None)).with_for_update()).first()
    if question is None:
        raise Problem(409, "urn:problem:no_open_consent_question",
                      "K objednávke nie je otvorená otázka na tento typ súhlasu.")
    question.decision = decision
    question.recorded_at = utcnow()
    session.flush()
    if consent_type == "model_split":
        if decision == "refused":
            orders.set_print_status(session, order_id, orders.CANNOT_BE_FULFILLED)
            notifier.notify(session, order_id, order.customer_id, "cannot_fulfill",
                            "Model v celku nevieme vytlačiť, objednávku preto nevieme vykonať (BR-009).")
        else:
            reevaluate_print(session, order_id)
    elif decision == "granted":
        orders.add_task(session, order_id, "fix_model", "Zákazník súhlasí s opravou modelu (BR-005).")
    return _consent_out(session, question)


def list_consents(session: Session, principal: Principal, order_id: uuid.UUID) -> list[dict]:
    orders.get_order_for(session, order_id, principal)
    rows = session.scalars(select(CustomerConsent).where(
        CustomerConsent.order_id == order_id, CustomerConsent.decision.is_not(None))
        .order_by(CustomerConsent.recorded_at))
    return [_consent_out(session, c) for c in rows]


# --- spolupráca s Model Validator (INT-005 … INT-009) ------------------------------

def model_file_for_validation(session: Session, order_id: uuid.UUID, model_id: uuid.UUID, version: int) -> bytes:
    orders.get_order(session, order_id)
    model = repository.get_model(session, model_id)
    if model.order_id != order_id:
        raise not_found("Model objednávky")
    return repository.read_file(repository.get_version(session, model_id, version))


def on_validation_completed(session: Session, order_id: uuid.UUID, model_id: uuid.UUID, version: int,
                            result: str, errors: list[dict], fits_printer: bool, splittable: bool | None) -> None:
    repository.mark_validated(session, model_id, version, result)
    order = orders.get_order(session, order_id)
    customer_model = repository.get_version(session, model_id, version).uploaded_by_role == "customer"

    if result == "failed":
        orders.set_print_status(session, order_id, orders.NOT_READY)
        listing = "; ".join(e["message"] for e in errors)
        if customer_model:
            notifier.notify(session, order_id, order.customer_id, "validation_failed",
                            f"Model obsahuje chyby: {listing}. Chcete, aby sme ho opravili?")
            _ask(session, order_id, model_id, "model_fix")
        else:
            orders.add_task(session, order_id, "rework", f"Kontrola tlačiteľnosti neprešla: {listing} (INT-006).")
        return

    if not fits_printer:
        if splittable:
            orders.set_print_status(session, order_id, orders.NOT_READY)
            notifier.notify(session, order_id, order.customer_id, "split_question",
                            "Model je príliš veľký na tlač v celku. Súhlasíte s jeho rozdelením na časti?")
            _ask(session, order_id, model_id, "model_split")
        else:
            orders.set_print_status(session, order_id, orders.CANNOT_BE_FULFILLED)
            notifier.notify(session, order_id, order.customer_id, "cannot_fulfill",
                            "Model presahuje možnosti našich tlačiarní a nedá sa rozdeliť (C-001).")
        return

    if customer_model:
        notifier.notify(session, order_id, order.customer_id, "validation_ok", "Model je v poriadku.")
    reevaluate_print(session, order_id)


def reevaluate_print(session: Session, order_id: uuid.UUID) -> None:
    """BR-001: do tlače iba model so súhlasom zákazníka (VAR-1 approved, VAR-2 nezmenený model – BR-008)."""
    order = orders.get_order(session, order_id)
    if order.print_status == orders.CANNOT_BE_FULFILLED:
        return
    model = repository.model_for_order(session, order_id)
    latest = repository.latest_version(session, model.model_id) if model else None
    if latest is None or latest.validation_result != "passed":
        return
    validation = session.scalars(select(ModelValidation).where(
        ModelValidation.model_id == model.model_id, ModelValidation.model_version == latest.version)
        .order_by(ModelValidation.validated_at.desc())).first()
    split = validation is not None and not validation.fits_printer
    if split and not has_granted_consent(session, order_id, "model_split"):
        return
    consented = latest.uploaded_by_role == "customer" or session.scalars(select(ModelApproval).where(
        ModelApproval.order_id == order_id, ModelApproval.model_version == latest.version,
        ModelApproval.state == "approved")).first() is not None
    if consented:
        orders.set_print_status(session, order_id, orders.READY_FOR_PRINT, split=split)
