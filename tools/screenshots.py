"""Screenshoty celej ukážky do docs/screenshots/ (server musí bežať na :8000).

POZOR: vymaže a znova vytvorí vývojovú databázu (iba ukážkové dáta).
Spustenie:  PYTHONPATH=src .venv/Scripts/python tools/screenshots.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

from pod.core import auth
from pod.core.db import init_db
from pod.core.settings import Settings
from pod.customer_portal import service as portal
from pod.dev_seed import ACCOUNTS

BASE = "http://127.0.0.1:8000"
OUT = Path("docs/screenshots")
STL = b"solid drziak\nfacet normal 0 0 1\nendfacet\nendsolid drziak\n"


def reset_database() -> None:
    settings = Settings()
    db = init_db(settings.database_url)
    auth.configure(settings.jwt_secret)
    db.drop_schema()
    db.create_schema()
    with db.sessions.begin() as s:
        for account_id, login, password, role, nickname in ACCOUNTS:
            portal.create_account(s, account_id, login, password, role, nickname)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    reset_database()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        anna = browser.new_context(viewport={"width": 1280, "height": 860}).new_page()
        jan = browser.new_context(viewport={"width": 1280, "height": 860}).new_page()

        def shot(page, name: str) -> None:
            page.wait_for_timeout(400)
            page.evaluate("document.getElementById('log-box') && (document.getElementById('log-box').hidden = true)")
            page.screenshot(path=str(OUT / name), full_page=True)
            print("✓", name)

        def log_in(page, login: str, password: str, landing: str) -> None:
            page.goto(f"{BASE}/portal/login.html")
            page.fill("#login", login)
            page.fill("#password", password)
            page.click("#submit")
            page.wait_for_url(f"**/portal/{landing}")
            page.wait_for_timeout(600)

        def reload(page) -> None:
            page.reload()
            page.wait_for_timeout(900)

        # 1. prihlásenie
        anna.goto(f"{BASE}/portal/login.html")
        shot(anna, "01_login.png")
        anna.fill("#login", "anna")
        anna.fill("#password", "zle-heslo")
        anna.click("#submit")
        anna.wait_for_selector("#error:not([hidden])")
        shot(anna, "02_login_nespravne_heslo.png")

        # 2. Anna vytvorí objednávku
        log_in(anna, "anna", "Anna-heslo-1", "index.html")
        anna.fill("#new-desc", "Držiak na bicykel na riadidlá, priemer 30 mm")
        shot(anna, "03_zakaznik_nova_objednavka.png")
        anna.click("#create")
        anna.wait_for_timeout(800)
        shot(anna, "04_zakaznik_objednavka_odoslana.png")

        # 3. modelár pošle model na schválenie
        log_in(jan, "jan.m", "Jan-heslo-1", "modeler.html")
        shot(jan, "05_modelar_zoznam_objednavok.png")
        jan.set_input_files("#file", files=[{"name": "drziak_v1.stl", "mimeType": "model/stl", "buffer": STL}])
        jan.fill("#note", "Prvá verzia držiaka podľa vášho popisu")
        jan.click("#send")
        jan.wait_for_timeout(900)
        shot(jan, "06_modelar_model_poslany_zakaznikovi.png")

        # 4. Anna model otvorí a schváli
        reload(anna)
        shot(anna, "07_zakaznik_model_caka_na_schvalenie.png")
        anna.click("#open")
        anna.wait_for_timeout(600)
        shot(anna, "08_zakaznik_model_otvoreny.png")
        anna.click("#approve")
        anna.wait_for_timeout(800)
        shot(anna, "09_zakaznik_model_schvaleny.png")

        # 5. modelár skontroluje a odošle na tlač
        reload(jan)
        jan.click("#check")
        jan.wait_for_timeout(900)
        shot(jan, "10_modelar_kontrola_tlacitelnosti.png")
        jan.click("#print")
        jan.wait_for_timeout(900)
        shot(jan, "11_modelar_odoslane_na_tlac.png")

        # 6. Anna vidí stav V tlači
        reload(anna)
        shot(anna, "12_zakaznik_objednavka_v_tlaci.png")

        # 7. chat a API
        anna.goto(f"{BASE}/portal/chat.html")
        anna.fill("#text", "Dobrý deň, kedy si môžem diel vyzdvihnúť?")
        anna.click("button[type=submit]")
        anna.wait_for_timeout(1200)
        shot(anna, "13_chat_mockup.png")

        docs = [("customer_portal", "prihlasenie"), ("order_orchestrator", "objednavky"),
                ("modeling_workspace", "schvalenie_modelu"), ("model_repository", "modely"),
                ("model_validator", "kontrola_modelu")]
        for i, (prefix, name) in enumerate(docs, start=14):
            jan.goto(f"{BASE}/api/{prefix}/docs")
            jan.wait_for_selector(".opblock", timeout=15000)
            shot(jan, f"{i}_api_{name}.png")

        # 8. mobil
        mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2).new_page()
        mobile.goto(f"{BASE}/portal/login.html")
        mobile.wait_for_timeout(300)
        mobile.screenshot(path=str(OUT / "19_mobil_login.png"))
        print("✓ 19_mobil_login.png")
        log_in(mobile, "anna", "Anna-heslo-1", "index.html")
        mobile.wait_for_timeout(600)
        mobile.screenshot(path=str(OUT / "20_mobil_moje_objednavky.png"))
        print("✓ 20_mobil_moje_objednavky.png")
        browser.close()


if __name__ == "__main__":
    main()
