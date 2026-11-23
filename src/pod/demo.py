"""Čistý štart ukážky: vymaže vývojovú databázu a vytvorí účty.

POZOR: zmaže všetky objednávky vo vývojovej databáze (POD_DATABASE_URL).
Spustenie:  python -m pod.demo
"""
from pod.core import auth
from pod.core.db import init_db
from pod.core.settings import Settings
from pod.customer_portal import service as portal
from pod.dev_seed import ACCOUNTS


def main() -> None:
    settings = Settings()
    db = init_db(settings.database_url)
    auth.configure(settings.jwt_secret)
    db.drop_schema()
    db.create_schema()
    with db.sessions.begin() as s:
        for account_id, login, password, role, nickname in ACCOUNTS:
            portal.create_account(s, account_id, login, password, role, nickname)

    print("Ukážka je pripravená (prázdna databáza):  http://127.0.0.1:8000/portal/\n")
    for _, login, password, role, _ in ACCOUNTS:
        print(f"  {login:6} / {password:14} {role}")


if __name__ == "__main__":
    main()
