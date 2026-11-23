"""Vývojové údaje: vytvorí schému, ukážkové objednávky a vypíše tokeny.

Objednávky a prihlásenie nie sú súčasťou contractu R-001 (AC-OrderOrchestrator,
AC-CustomerPortal), preto ich na ukážku vytvára tento skript.
Spustenie:  python -m pod.dev_seed
"""
from pod.core import auth
from pod.core.db import init_db
from pod.core.settings import Settings
from pod.order_orchestrator import service as orders


def main() -> None:
    settings = Settings()
    db = init_db(settings.database_url)
    auth.configure(settings.jwt_secret)
    db.create_schema()
    with db.sessions.begin() as session:
        var1 = orders.create_order(session, "customer-anna", "VAR-1", "Držiak na bicykel, 30×30 cm", True)
        var2 = orders.create_order(session, "customer-boris", "VAR-2", "Vlastný model krytu", False)
        print(f"VAR-1 objednávka (customer-anna): {var1.order_id}")
        print(f"VAR-2 objednávka (customer-boris): {var2.order_id}")
    print()
    print("customer-anna :", auth.issue_token("customer-anna", "customer"))
    print("customer-boris:", auth.issue_token("customer-boris", "customer"))
    print("modeler       :", auth.issue_token("emp-17", "modeler", "jan.m"))
    print("manager       :", auth.issue_token("emp-02", "manager", "eva.k"))


if __name__ == "__main__":
    main()
