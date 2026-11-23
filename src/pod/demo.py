"""Príprava dát na ukážku (mockup). Server musí bežať na :8000.

Spustenie:  python -m pod.demo
"""
import httpx
from sqlalchemy import select

from pod.core import auth
from pod.core.db import init_db
from pod.core.settings import Settings
from pod.customer_portal import service as portal
from pod.customer_portal.models import UserAccount
from pod.dev_seed import ACCOUNTS
from pod.order_orchestrator import service as orders

BASE = "http://127.0.0.1:8000"


def main() -> None:
    settings = Settings()
    db = init_db(settings.database_url)
    auth.configure(settings.jwt_secret)
    db.create_schema()
    with db.sessions.begin() as s:
        for account_id, login, password, role, nickname in ACCOUNTS:
            if s.scalars(select(UserAccount).where(UserAccount.login == login)).first() is None:
                portal.create_account(s, account_id, login, password, role, nickname)
        anna_order = str(orders.create_order(s, "customer-anna", "VAR-1", "Držiak na bicykel, 30×30 cm", True).order_id)
        boris_order = str(orders.create_order(s, "customer-boris", "VAR-2", "Vlastný model krytu").order_id)

    modeler = {"Authorization": "Bearer " + auth.issue_token("emp-17", "modeler", "jan.m")}
    boris = {"Authorization": "Bearer " + auth.issue_token("customer-boris", "customer")}
    api = httpx.Client(base_url=BASE, trust_env=False, timeout=10)
    try:
        api.get("/portal/login.html")
    except httpx.HTTPError:
        raise SystemExit(f"Server nebeží na {BASE}. Najprv spusti uvicorn (pozri docs/demo/README.md).")

    api.post(f"/api/model_repository/orders/{anna_order}/model_versions", headers=modeler,
             files={"file": ("drziak_v1.stl", b"solid drziak\nendsolid drziak\n")}).raise_for_status()
    api.post(f"/api/modeling_workspace/orders/{anna_order}/model_approvals", headers=modeler,
             json={"model_version": 1, "model_origin": "new_model",
                   "note": "Prvá verzia držiaka podľa vášho popisu"}).raise_for_status()

    model = api.post(f"/api/model_repository/orders/{boris_order}/model_versions", headers=boris,
                     files={"file": ("kryt.stl", b"STUB:ERROR kryt")})
    model.raise_for_status()
    api.post("/api/model_validator/model_validations", headers=modeler,
             json={"order_id": boris_order, "model_id": model.json()["model_id"], "model_version": 1,
                   "print_type": "plast", "path": "VAR-2"}).raise_for_status()

    print("Ukážka je pripravená:  http://127.0.0.1:8000/portal/\n")
    print(f"  anna  / Anna-heslo-1   objednávka {anna_order}  (model čaká na schválenie)")
    print(f"  boris / Boris-heslo-1  objednávka {boris_order}  (model má chybu, čaká sa na súhlas s opravou)")


if __name__ == "__main__":
    main()
