"""Acceptance tests: scenáre SC-002-01 … SC-002-05 zo spec/stories/features/US-002.feature."""
from datetime import timedelta

from pytest_bdd import given, parsers, scenarios, then, when

from conftest import WS
from pod.core.auth import SESSION_COOKIE, LoginSession
from pod.core.db import utcnow
from pod.customer_portal import service as portal

scenarios("US-002.feature")

AUTH = "/api/customer_portal"


def _account(world, account_id: str, login: str, password: str, role: str, nickname: str | None = None):
    with world.session() as s:
        portal.create_account(s, account_id, login, password, role, nickname)


@given(parsers.parse('zákazník má účet s loginom "{login}" a heslom "{password}"'))
def customer_account(world, login, password):
    _account(world, "customer-anna", login, password, "customer")
    world.new_order("VAR-1", "customer-anna")


@given(parsers.parse('3D modelár má účet s loginom "{login}" a heslom "{password}"'))
def modeler_account(world, login, password):
    _account(world, "emp-17", login, password, "modeler", "jan.m")


@given("zákazník je prihlásený")
def customer_logged_in(world):
    customer_account(world, "anna", "Anna-heslo-1")
    log_in(world, "anna", "Anna-heslo-1")
    assert world.last.status_code == 201
    world.data.token = world.api.client.cookies.get(SESSION_COOKIE)


@when(parsers.parse('zákazník sa prihlási loginom "{login}" a heslom "{password}"'))
@when(parsers.parse('3D modelár sa prihlási loginom "{login}" a heslom "{password}"'))
def log_in(world, login, password):
    world.last = world.api.post(f"{AUTH}/sessions", json={"login": login, "password": password})


@when("zákazník sa odhlási")
def log_out(world):
    assert world.api.delete(f"{AUTH}/sessions/current").status_code == 204


@when("uplynie viac ako 8 hodín od prihlásenia")
def eight_hours_pass(world):
    with world.session() as s:
        for login in s.query(LoginSession).all():
            login.expires_at = utcnow() - timedelta(minutes=1)


@then("prehliadač dostane reláciu v HttpOnly cookie")
def http_only_cookie(world):
    assert world.last.status_code == 201
    header = world.last.headers["set-cookie"]
    assert header.startswith(f"{SESSION_COOKIE}=")
    assert "HttpOnly" in header and "SameSite=strict" in header and "Max-Age=28800" in header


@then("zákazník vidí stav svojej objednávky bez zadávania tokenu")
def sees_own_order(world):
    assert world.api.get(f"{WS}/orders/{world.order_id}/model_approvals").status_code == 200


@then("prihlásenie sa nepodarí so všeobecnou chybou")
def generic_error(world):
    assert world.last.status_code == 401
    assert world.last.json()["type"] == "urn:problem:invalid_credentials"
    assert world.last.json()["detail"] == "Nesprávny login alebo heslo."


@then("prehliadač nedostane reláciu")
def no_session(world):
    assert world.api.client.cookies.get(SESSION_COOKIE) is None


@then("jeho ďalšia požiadavka na objednávku je odmietnutá ako neprihlásená")
def rejected_as_anonymous(world):
    url = f"{WS}/orders/{world.order_id}/model_approvals"
    assert world.api.get(url).status_code == 401
    world.api.client.cookies.set(SESSION_COOKIE, world.data.token)
    assert world.api.get(url).status_code == 401


@then(parsers.parse('relácia patrí roli "{role}" s prezývkou "{nickname}"'))
def session_role(world, role, nickname):
    assert world.last.status_code == 201
    current = world.api.get(f"{AUTH}/sessions/current").json()
    assert current["role"] == role and current["nickname"] == nickname
