"""Acceptance tests: scenáre SC-001-01 … SC-001-11 zo spec/stories/features/US-001.feature."""
from pytest_bdd import given, parsers, scenarios, then, when

from conftest import REPO, WS

scenarios("US-001.feature")

CLEAN = b"solid part\nendsolid part\n"


def _approved_var1(world, content: bytes):
    world.new_order("VAR-1")
    world.upload(world.modeler, content)
    world.send_for_approval()
    world.customer_open()
    world.customer_approve()


# --- VAR-1: schválenie a revízie ------------------------------------------------

@given("zákazník poslal zaplatenú objednávku s popisom dielu")
def paid_prompt_order(world):
    world.new_order("VAR-1")


@given("3D modelár vytvoril model a poslal ho zákazníkovi na schválenie")
def modeler_sends_model(world):
    world.upload(world.modeler, CLEAN)
    world.send_for_approval()


@given("zákazníkovi bol poslaný model na schválenie")
def model_sent(world):
    world.new_order("VAR-1")
    world.upload(world.modeler, CLEAN)
    world.send_for_approval()


@given("zákazník zatiaľ využil menej ako 2 bezplatné revízie")
def fewer_than_two_revisions(world):
    assert world.approval["revision_count"] < 2


@given("zákazník už využil 2 bezplatné revízie modelu")
def two_revisions_used(world):
    model_sent(world)
    for version in (2, 3):
        world.customer_open()
        world.customer_reject()
        world.upload(world.modeler, CLEAN + bytes([version]))
        world.submit_revision(version)
    assert world.approval["revision_count"] == 2


@when("zákazník model otvorí v portáli")
def customer_opens(world):
    r = world.api.get(f"{REPO}/models/{world.model_id}", world.customer)
    assert r.status_code == 200
    world.customer_open()


@when("zákazník v portáli potvrdí, že s modelom súhlasí")
def customer_approves(world):
    world.customer_approve()


@when("zákazník v portáli nesúhlasí s modelom a uvedie komentár")
def customer_rejects(world):
    world.customer_open()
    world.customer_reject("Otvory majú byť väčšie.")


@when("zákazník s modelom znova nesúhlasí")
def customer_rejects_again(world):
    world.customer_open()
    world.customer_reject("Stále to nie je ono.")


@then(parsers.parse('stav schválenia modelu je "{state}"'))
def approval_state(world, state):
    assert world.refresh_approval()["state"] == state


@then("model sa odovzdá ďalšiemu 3D modelárovi na kontrolu tlačiteľnosti")
def handed_to_printability_check(world):
    assert "printability_check" in world.task_kinds()


@then("model sa netlačí")
def not_printed(world):
    assert world.order().print_status != "ready_for_print"


@then("model upraví náš 3D modelár")
def modeler_reworks(world):
    assert "revision" in world.task_kinds()
    world.upload(world.modeler, CLEAN + b"v2")


@then("upravený model sa pošle zákazníkovi ako nová revízia na schválenie")
def revision_sent(world):
    world.submit_revision(2)
    assert world.approval["state"] == "waiting_for_review"
    assert world.approval["revision_count"] == 1
    assert world.approval["history"][-1]["employee"] == {"employee_id": "emp-17", "nickname": "jan.m"}


@then("zákazník dostane informáciu, že ďalšia úprava je nový platený vývoj modelu")
def informed_about_paid_development(world):
    assert world.last["new_paid_development_required"] is True
    assert world.notifications("new_paid_development")


@then("pre nový model sa vytvorí nový záznam schválenia")
def new_approval_record(world):
    old_id = world.approval["model_approval_id"]
    world.upload(world.modeler, CLEAN + b"new development")
    new = world.send_for_approval(version=4)
    assert new["model_approval_id"] != old_id and new["state"] == "waiting_for_review"
    listed = world.api.get(f"{WS}/orders/{world.order_id}/model_approvals", world.customer).json()
    assert len(listed) == 2


# --- VAR-1: opätovné použitie (BR-006) --------------------------------------------

@given("v repozitári existuje overený model zodpovedajúci popisu zákazníka")
def validated_model_exists(world):
    world.new_order("VAR-1", "customer-cyril", "Držiak na bicykel, 30×30 cm")
    world.upload(world.modeler, CLEAN + b"reusable")
    world.validate(1, "VAR-1")
    world.data.original_order = world.order_id
    world.data.original_model = world.model_id


@given("pôvodný zákazník povolil zdieľanie tohto modelu")
def sharing_allowed(world):
    from pod.order_orchestrator import service as orders
    with world.session() as s:
        orders.set_sharing(s, world.data.original_order, True)


@given("pôvodný zákazník nepovolil zdieľanie tohto modelu")
def sharing_not_allowed(world):
    from pod.order_orchestrator import service as orders
    with world.session() as s:
        orders.set_sharing(s, world.data.original_order, False)


@when("3D modelár spracúva novú objednávku s popisom")
def modeler_processes_new_order(world):
    world.new_order("VAR-1", "customer-anna", "Držiak na bicykel")
    world.model_id = None
    r = world.api.get(f"{REPO}/reusable_models", world.modeler, params={"query": "Držiak na bicykel"})
    assert r.status_code == 200
    world.data.found = [m["model_id"] for m in r.json()]


@then("existujúci model sa pošle zákazníkovi na schválenie bez nového modelovania")
def reused_model_sent(world):
    assert world.data.original_model in world.data.found
    detail = world.api.get(f"{REPO}/models/{world.data.original_model}", world.modeler).json()
    content = world.api.get(detail["file_url"]).content
    world.upload(world.modeler, content)
    approval = world.send_for_approval(origin="reused_model")
    assert approval["model_origin"] == "reused_model" and approval["state"] == "waiting_for_review"


@then("existujúci model sa novému zákazníkovi neponúkne")
def not_offered(world):
    assert world.data.original_model not in world.data.found


@then("3D modelár vytvorí nový model")
def modeler_creates_new(world):
    r = world.upload(world.modeler, CLEAN + b"brand new")
    assert r.json()["version"] == 1


# --- kontrola tlačiteľnosti (BR-005, INT-006) ---------------------------------------

@given("zákazník schválil model vytvorený nami")
def customer_approved_our_model(world):
    _approved_var1(world, b"STUB:ERROR")


@when("kontrola tlačiteľnosti nájde v modeli chybu")
def printability_check_fails(world):
    assert world.validate(1, "VAR-1")["result"] == "failed"


@then("model sa vráti 3D modelárovi na prepracovanie")
def returned_to_modeler(world):
    assert "rework" in world.task_kinds()


# --- VAR-2: model zákazníka (BR-008, BR-005) -----------------------------------------

@given("zákazník poslal zaplatenú objednávku s vlastným 3D modelom")
def paid_model_order(world):
    world.new_order("VAR-2", "customer-boris", "Vlastný model krytu")


@when("validátor pre zvolený typ tlače overí model")
def validator_checks(world):
    world.data.pending_validation = True


@when("model nemá žiadne chyby")
def model_has_no_errors(world):
    assert world.data.pending_validation
    world.upload(world.customer, CLEAN)
    assert world.validate(1, "VAR-2")["result"] == "passed"


@when("validátor pre zvolený typ tlače nájde v modeli chyby")
def validator_finds_errors(world):
    world.upload(world.customer, b"STUB:ERROR")
    assert world.validate(1, "VAR-2")["result"] == "failed"


@then("zákazník dostane notifikáciu, že model je v poriadku")
def notified_ok(world):
    assert world.notifications("validation_ok")


@then("model sa odovzdá do tlače bez ďalšieho potvrdenia zákazníkom")
def printed_without_confirmation(world):
    assert world.order().print_status == "ready_for_print"
    assert world.api.get(f"{WS}/orders/{world.order_id}/model_approvals", world.customer).json() == []


@then("zákazník dostane notifikáciu so zoznamom chýb")
def notified_errors(world):
    [n] = world.notifications("validation_failed")
    assert "chybu" in n.message


@then("zákazník je opýtaný, či chce, aby sme model opravili")
def asked_for_fix(world):
    assert len(world.open_consent_questions("model_fix")) == 1


@then("bez súhlasu zákazníka sa model neupravuje")
def no_fix_without_consent(world):
    world.upload(world.modeler, CLEAN, expect=403)
    assert world.version_count() == 1


# --- príliš veľký model (C-001, BR-009) ------------------------------------------------

@given("model je schválený a je príliš veľký na tlač v celku")
def approved_too_large(world):
    _approved_var1(world, b"STUB:TOO_LARGE")
    world.validate(1, "VAR-1")
    assert world.last["fits_printer"] is False


@given("slicer ho dokáže rozdeliť na časti")
def slicer_can_split(world):
    assert world.last["splittable"] is True


@when("zákazníka sa opýtame, či súhlasí s rozdelením modelu")
def asked_about_split(world):
    assert world.notifications("split_question")
    assert len(world.open_consent_questions("model_split")) == 1


@when("zákazník s rozdelením súhlasí")
def split_granted(world):
    r = world.api.post(f"{WS}/orders/{world.order_id}/customer_consents", world.customer,
                       json={"consent_type": "model_split", "decision": "granted"})
    assert r.status_code == 201
    world.last = r.json()


@when("zákazník s rozdelením nesúhlasí")
def split_refused(world):
    r = world.api.post(f"{WS}/orders/{world.order_id}/customer_consents", world.customer,
                       json={"consent_type": "model_split", "decision": "refused"})
    assert r.status_code == 201
    world.last = r.json()


@then("model sa rozdelí na časti a časti sa vytlačia samostatne")
def split_and_printed(world):
    order = world.order()
    assert world.last["order_can_be_fulfilled"] is True
    assert order.print_status == "ready_for_print" and order.split_into_parts is True


@then("model sa nerozdelí ani nevytlačí")
def not_split_not_printed(world):
    order = world.order()
    assert order.print_status == "cannot_be_fulfilled" and order.split_into_parts is False


@then("zákazník dostane informáciu, že model v celku nevieme vytlačiť a objednávku nevieme vykonať")
def informed_cannot_fulfill(world):
    assert world.last["order_can_be_fulfilled"] is False
    assert world.notifications("cannot_fulfill")


# --- limit vlastných nahraní (BR-004) ----------------------------------------------------

@given("zákazník v sledovanom období už 10-krát nahral nový vlastný model")
def ten_uploads(world):
    world.new_order("VAR-2", "customer-boris", "Vlastný model krytu")
    for i in range(10):
        r = world.upload(world.customer, CLEAN + bytes([i]))
    assert r.json()["customer_uploads_remaining"] == 0


@when("zákazník nahrá ďalší model")
def eleventh_upload(world):
    world.last = world.upload(world.customer, CLEAN + b"eleven", expect=429).json()


@then("model sa neoverí")
def not_validated(world):
    assert world.version_count() == 10


@then("zákazník dostane informáciu, že ďalšie overenie je za doplatok")
def informed_about_fee(world):
    assert world.last["type"] == "urn:problem:upload_limit_reached"
    assert "doplatok" in world.last["detail"]
