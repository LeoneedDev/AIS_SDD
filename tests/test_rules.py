"""Negatívne prípady: oprávnenia, súbeh a stavové prechody (BR-003, BR-005, BR-007, DR-4)."""
from concurrent.futures import ThreadPoolExecutor

from conftest import REPO, WS

CLEAN = b"solid part\nendsolid part\n"


def _sent(world):
    world.new_order("VAR-1")
    world.upload(world.modeler, CLEAN)
    world.send_for_approval()


def test_missing_token_is_401(world):
    _sent(world)
    r = world.api.get(world.approval_url())
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")


def test_modeler_cannot_approve_for_customer(world):
    _sent(world)
    world.customer_open()
    assert world.api.post(world.approval_url("/approvals"), world.modeler).status_code == 403
    assert world.api.post(world.approval_url("/approvals"), world.manager).status_code == 403


def test_customer_cannot_see_foreign_order(world):
    _sent(world)
    stranger = world.customer_token("customer-zoe")
    assert world.api.get(world.approval_url(), stranger).status_code == 403
    assert world.api.get(f"{REPO}/models/{world.model_id}", stranger).status_code == 403


def test_customer_cannot_send_revision(world):
    _sent(world)
    world.customer_open()
    world.customer_reject()
    r = world.api.post(world.approval_url("/revisions"), world.customer, json={"model_version": 1})
    assert r.status_code == 403


def test_approve_before_opening_is_conflict(world):
    _sent(world)
    r = world.api.post(world.approval_url("/approvals"), world.customer)
    assert r.status_code == 409
    assert r.json()["current_state"] == "waiting_for_review"


def test_second_active_approval_is_conflict(world):
    _sent(world)
    r = world.api.post(f"{WS}/orders/{world.order_id}/model_approvals", world.modeler,
                       json={"model_version": 1, "model_origin": "new_model"})
    assert r.status_code == 409
    assert r.json()["type"] == "urn:problem:active_approval_exists"


def test_first_request_wins_when_concurrent(world):
    _sent(world)
    url = world.approval_url("/review_starts")
    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = sorted(pool.map(lambda _: world.api.post(url, world.customer).status_code, range(2)))
    assert codes == [200, 409]


def test_reject_requires_comment(world):
    _sent(world)
    world.customer_open()
    assert world.api.post(world.approval_url("/rejections"), world.customer, json={"comment": ""}).status_code == 400


def test_consent_without_open_question_is_conflict(world):
    _sent(world)
    r = world.api.post(f"{WS}/orders/{world.order_id}/customer_consents", world.customer,
                       json={"consent_type": "model_split", "decision": "granted"})
    assert r.status_code == 409


def test_fix_allowed_after_customer_consent(world):
    world.new_order("VAR-2", "customer-boris")
    world.upload(world.customer, b"STUB:ERROR")
    world.validate(1, "VAR-2")
    world.upload(world.modeler, CLEAN, expect=403)
    r = world.api.post(f"{WS}/orders/{world.order_id}/customer_consents", world.customer,
                       json={"consent_type": "model_fix", "decision": "granted"})
    assert r.status_code == 201
    world.upload(world.modeler, CLEAN, expect=201)
    world.validate(2, "VAR-2")
    assert world.order().print_status != "ready_for_print"
    world.send_for_approval(version=2, origin="fixed_customer_model")
    world.customer_open()
    world.customer_approve()
    assert world.order().print_status == "ready_for_print"


def test_upload_after_print_started_is_conflict(world):
    from pod.order_orchestrator import service as orders
    _sent(world)
    with world.session() as s:
        orders.get_order(s, world.order_id).print_started = True
    world.upload(world.customer, CLEAN, expect=409)


def test_customer_sees_employee_id_and_nickname_only(world):
    _sent(world)
    entry = world.refresh_approval()["history"][0]
    assert entry["employee"] == {"employee_id": "emp-17", "nickname": "jan.m"}
