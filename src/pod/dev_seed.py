"""Vývojové údaje: schéma, účty, ukážkové objednávky.

Registrácia a vytváranie objednávok nie sú súčasťou contractov, preto ich na
ukážku vytvára tento skript.
Spustenie:  python -m pod.dev_seed
"""
from sqlalchemy import select

from pod.core import auth
from pod.core.db import init_db
from pod.core.settings import Settings
from pod.customer_portal import service as portal
from pod.customer_portal.models import UserAccount
from pod.order_orchestrator import service as orders

ACCOUNTS = [
    ("customer-anna", "anna", "Anna-heslo-1", "customer", None),
    ("customer-boris", "boris", "Boris-heslo-1", "customer", None),
    ("emp-17", "jan.m", "Jan-heslo-1", "modeler", "jan.m"),
    ("emp-02", "eva.k", "Eva-heslo-1", "manager", "eva.k"),
]


def main() -> None:
    settings = Settings()
    db = init_db(settings.database_url)
    auth.configure(settings.jwt_secret)
    db.create_schema()
    with db.sessions.begin() as session:
        for account_id, login, password, role, nickname in ACCOUNTS:
            if session.scalars(select(UserAccount).where(UserAccount.login == login)).first() is None:
                portal.create_account(session, account_id, login, password, role, nickname)
        var1 = orders.create_order(session, "customer-anna", "VAR-1", "Držiak na bicykel, 30×30 cm", True)
        var2 = orders.create_order(session, "customer-boris", "VAR-2", "Vlastný model krytu", False)
        print(f"VAR-1 objednávka (anna): {var1.order_id}")
        print(f"VAR-2 objednávka (boris): {var2.order_id}")
    print()
    print("Účty (login / heslo):")
    for _, login, password, role, _ in ACCOUNTS:
        print(f"  {login:6} / {password:14} ({role})")


if __name__ == "__main__":
    main()
