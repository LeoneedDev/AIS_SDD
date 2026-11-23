"""Screenshoty portálu, prihlásenia, chatu a API docs do docs/screenshots/.

Server musí bežať na :8000. Spustenie:
  PYTHONPATH=src .venv/Scripts/python tools/screenshots.py
"""
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright
from sqlalchemy import select

from pod.core import auth
from pod.core.db import init_db
from pod.core.settings import Settings
from pod.customer_portal import service as portal
from pod.customer_portal.models import UserAccount
from pod.dev_seed import ACCOUNTS
from pod.order_orchestrator import service as orders

BASE = "http://127.0.0.1:8000"
OUT = Path("docs/screenshots")
WS, VAL, REPO = "/api/modeling_workspace", "/api/model_validator", "/api/model_repository"


def prepare():
    settings = Settings()
    db = init_db(settings.database_url)
    auth.configure(settings.jwt_secret)
    db.create_schema()
    with db.sessions.begin() as s:
        for account_id, login, password, role, nickname in ACCOUNTS:
            if s.scalars(select(UserAccount).where(UserAccount.login == login)).first() is None:
                portal.create_account(s, account_id, login, password, role, nickname)
        var1 = str(orders.create_order(s, "customer-anna", "VAR-1", "Držiak na bicykel, 30×30 cm", True).order_id)
        var2 = str(orders.create_order(s, "customer-boris", "VAR-2", "Vlastný model krytu").order_id)
    return var1, var2


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    var1, var2 = prepare()

    modeler = {"Authorization": "Bearer " + auth.issue_token("emp-17", "modeler", "jan.m")}
    boris = {"Authorization": "Bearer " + auth.issue_token("customer-boris", "customer")}
    api = httpx.Client(base_url=BASE, trust_env=False, timeout=10)

    api.post(f"{REPO}/orders/{var1}/model_versions", headers=modeler,
             files={"file": ("drziak_v1.stl", b"solid drziak\nendsolid drziak\n")})
    approval_id = api.post(f"{WS}/orders/{var1}/model_approvals", headers=modeler,
                           json={"model_version": 1, "model_origin": "new_model",
                                 "note": "Prvá verzia držiaka podľa vášho popisu"}).json()["model_approval_id"]
    model = api.post(f"{REPO}/orders/{var2}/model_versions", headers=boris,
                     files={"file": ("kryt.stl", b"STUB:ERROR kryt")}).json()
    api.post(f"{VAL}/model_validations", headers=modeler,
             json={"order_id": var2, "model_id": model["model_id"], "model_version": 1,
                   "print_type": "plast", "path": "VAR-2"})

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        def shot(name: str, target=None) -> None:
            target = target or page
            target.wait_for_timeout(300)
            target.screenshot(path=str(OUT / name), full_page=True)
            print("✓", name)

        def log_in(target, login: str, password: str) -> None:
            target.goto(f"{BASE}/portal/login.html")
            target.fill("#login", login)
            target.fill("#password", password)
            target.click("#submit")
            target.wait_for_url("**/portal/index.html")
            target.wait_for_timeout(400)

        def load_order(target, order_id: str) -> None:
            target.fill("#order", order_id)
            target.click("#load")
            target.wait_for_timeout(500)

        page.goto(f"{BASE}/portal/login.html")
        shot("01_login.png")

        page.fill("#login", "anna")
        page.fill("#password", "zle-heslo")
        page.click("#submit")
        page.wait_for_selector("#error:not([hidden])")
        shot("02_login_nespravne_heslo.png")

        log_in(page, "anna", "Anna-heslo-1")
        page.evaluate("localStorage.clear()")
        load_order(page, var1)
        page.evaluate("document.getElementById('log').textContent = ''")
        load_order(page, var1)
        shot("03_portal_model_caka_na_schvalenie.png")

        page.click("#open")
        page.wait_for_timeout(500)
        shot("04_portal_model_otvoreny.png")

        page.fill("#comment", "Otvory na skrutky majú byť o 2 mm väčšie.")
        page.click("#reject")
        page.wait_for_timeout(500)
        shot("05_portal_nesuhlas_s_komentarom.png")

        api.post(f"{REPO}/orders/{var1}/model_versions", headers=modeler,
                 files={"file": ("drziak_v2.stl", b"solid drziak v2\nendsolid drziak\n")})
        api.post(f"{WS}/orders/{var1}/model_approvals/{approval_id}/revisions", headers=modeler,
                 json={"model_version": 2, "note": "Otvory zväčšené o 2 mm"})
        page.click("#load")
        page.wait_for_timeout(500)
        shot("06_portal_nova_revizia.png")

        page.click("#open")
        page.wait_for_timeout(400)
        page.click("#approve")
        page.wait_for_timeout(500)
        shot("07_portal_model_schvaleny.png")

        page.click("#logout")
        page.wait_for_url("**/portal/login.html")
        log_in(page, "boris", "Boris-heslo-1")
        load_order(page, var2)
        page.evaluate("document.getElementById('log').textContent = ''")
        page.click("[data-consent=model_fix][data-decision=granted]")
        page.wait_for_timeout(500)
        shot("08_portal_suhlas_s_opravou.png")

        page.goto(f"{BASE}/portal/chat.html")
        page.fill("#order", var2)
        page.fill("#text", "Dobrý deň, čo presne opravíte na mojom modeli?")
        page.click("button[type=submit]")
        page.wait_for_timeout(1200)
        shot("09_chat_mockup.png")

        for i, (prefix, name) in enumerate([("customer_portal", "authentication"),
                                            ("modeling_workspace", "model_approval"),
                                            ("model_repository", "model_repository"),
                                            ("model_validator", "model_validation")], start=10):
            page.goto(f"{BASE}/api/{prefix}/docs")
            page.wait_for_selector(".opblock", timeout=15000)
            shot(f"{i}_api_{name}.png")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        mobile.goto(f"{BASE}/portal/login.html")
        mobile.wait_for_timeout(300)
        mobile.screenshot(path=str(OUT / "14_mobil_login.png"))
        print("✓ 14_mobil_login.png")
        log_in(mobile, "anna", "Anna-heslo-1")
        load_order(mobile, var1)
        mobile.screenshot(path=str(OUT / "15_mobil_portal.png"))
        print("✓ 15_mobil_portal.png")
        browser.close()


if __name__ == "__main__":
    main()
