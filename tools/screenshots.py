"""Screenshoty portálu, chatu a API docs do docs/screenshots/ (server musí bežať na :8000).

Spustenie:  PYTHONPATH=src .venv/Scripts/python tools/screenshots.py
"""
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright

from pod.core import auth
from pod.core.db import init_db
from pod.core.settings import Settings
from pod.order_orchestrator import service as orders

BASE = "http://127.0.0.1:8000"
OUT = Path("docs/screenshots")
WS, VAL, REPO = "/api/modeling_workspace", "/api/model_validator", "/api/model_repository"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    settings = Settings()
    db = init_db(settings.database_url)
    auth.configure(settings.jwt_secret)
    with db.sessions.begin() as s:
        var1 = str(orders.create_order(s, "customer-anna", "VAR-1", "Držiak na bicykel, 30×30 cm", True).order_id)
        var2 = str(orders.create_order(s, "customer-boris", "VAR-2", "Vlastný model krytu").order_id)

    modeler = {"Authorization": "Bearer " + auth.issue_token("emp-17", "modeler", "jan.m")}
    anna = auth.issue_token("customer-anna", "customer")
    boris = auth.issue_token("customer-boris", "customer")
    api = httpx.Client(base_url=BASE, trust_env=False, timeout=10)

    api.post(f"{REPO}/orders/{var1}/model_versions", headers=modeler,
             files={"file": ("drziak_v1.stl", b"solid drziak\nendsolid drziak\n")})
    approval = api.post(f"{WS}/orders/{var1}/model_approvals", headers=modeler,
                        json={"model_version": 1, "model_origin": "new_model",
                              "note": "Prvá verzia držiaka podľa vášho popisu"}).json()
    approval_id = approval["model_approval_id"]

    boris_headers = {"Authorization": "Bearer " + boris}
    model = api.post(f"{REPO}/orders/{var2}/model_versions", headers=boris_headers,
                     files={"file": ("kryt.stl", b"STUB:ERROR kryt")}).json()
    api.post(f"{VAL}/model_validations", headers=modeler,
             json={"order_id": var2, "model_id": model["model_id"], "model_version": 1,
                   "print_type": "plast", "path": "VAR-2"})

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        def shot(name: str) -> None:
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / name), full_page=True)
            print("✓", name)

        def login(token: str, order_id: str) -> None:
            page.fill("#token", token)
            page.fill("#order", order_id)
            page.click("#load")
            page.wait_for_timeout(500)

        page.goto(f"{BASE}/portal/")
        page.evaluate("localStorage.clear()")
        page.reload()
        shot("01_portal_prihlasenie.png")

        login(anna, var1)
        shot("02_portal_model_caka_na_schvalenie.png")

        page.click("#open")
        page.wait_for_timeout(500)
        shot("03_portal_model_otvoreny.png")

        page.fill("#comment", "Otvory na skrutky majú byť o 2 mm väčšie.")
        page.click("#reject")
        page.wait_for_timeout(500)
        shot("04_portal_nesuhlas_s_komentarom.png")

        api.post(f"{REPO}/orders/{var1}/model_versions", headers=modeler,
                 files={"file": ("drziak_v2.stl", b"solid drziak v2\nendsolid drziak\n")})
        api.post(f"{WS}/orders/{var1}/model_approvals/{approval_id}/revisions", headers=modeler,
                 json={"model_version": 2, "note": "Otvory zväčšené o 2 mm"})
        page.click("#load")
        page.wait_for_timeout(500)
        shot("05_portal_nova_revizia.png")

        page.click("#open")
        page.wait_for_timeout(400)
        page.click("#approve")
        page.wait_for_timeout(500)
        shot("06_portal_model_schvaleny.png")

        page.evaluate("document.getElementById('log').textContent = ''")
        login(boris, var2)
        page.click("[data-consent=model_fix][data-decision=granted]")
        page.wait_for_timeout(500)
        shot("07_portal_suhlas_s_opravou.png")

        page.goto(f"{BASE}/portal/chat.html")
        page.fill("#order", var1)
        page.fill("#text", "Dobrý deň, kedy bude môj držiak vytlačený?")
        page.click("button[type=submit]")
        page.wait_for_timeout(1200)
        page.fill("#text", "Ďakujem!")
        page.click("button[type=submit]")
        page.wait_for_timeout(1200)
        shot("08_chat_mockup.png")

        page.goto(f"{BASE}/api/modeling_workspace/docs")
        page.wait_for_selector(".opblock", timeout=15000)
        shot("09_api_model_approval.png")
        page.goto(f"{BASE}/api/model_repository/docs")
        page.wait_for_selector(".opblock", timeout=15000)
        shot("10_api_model_repository.png")
        page.goto(f"{BASE}/api/model_validator/docs")
        page.wait_for_selector(".opblock", timeout=15000)
        shot("11_api_model_validation.png")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        mobile.goto(f"{BASE}/portal/")
        mobile.fill("#token", anna)
        mobile.fill("#order", var1)
        mobile.click("#load")
        mobile.wait_for_timeout(600)
        mobile.screenshot(path=str(OUT / "12_portal_mobil.png"))
        print("✓ 12_portal_mobil.png")
        browser.close()


if __name__ == "__main__":
    main()
