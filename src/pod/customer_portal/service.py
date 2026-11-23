import base64
import hashlib
import hmac
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from pod.core import auth
from pod.core.problems import Problem
from pod.customer_portal.models import UserAccount

_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=_N, r=_R, p=_P)
    return hmac.compare_digest(digest, base64.b64decode(digest_b64))


_DUMMY_HASH = hash_password("dummy-password-for-timing")


def create_account(db: Session, account_id: str, login: str, password: str, role: str,
                   nickname: str | None = None) -> UserAccount:
    account = UserAccount(account_id=account_id, login=login, password_hash=hash_password(password),
                          role=role, nickname=nickname)
    db.add(account)
    db.flush()
    return account


def login(db: Session, login_name: str, password: str) -> tuple[str, dict]:
    account = db.scalars(select(UserAccount).where(UserAccount.login == login_name)).first()
    valid = verify_password(password, account.password_hash if account else _DUMMY_HASH)
    if account is None or not valid:
        raise Problem(401, "urn:problem:invalid_credentials", "Nesprávny login alebo heslo.")
    token, session = auth.start_session(db, account.account_id, account.account_id, account.role,
                                        account.nickname)
    return token, session_out(account.account_id, account.role, account.nickname, session.expires_at)


def session_out(account_id: str, role: str, nickname: str | None, expires_at) -> dict:
    return {"account_id": account_id, "role": role, "nickname": nickname, "expires_at": expires_at}
