import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

import jwt
from fastapi import Depends
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from pod.core.db import Base, get_session, utcnow
from pod.core.problems import Problem, forbidden

Role = Literal["customer", "modeler", "manager"]
STAFF: tuple[Role, ...] = ("modeler", "manager")
SESSION_COOKIE = "pod_session"
SESSION_LIFETIME = timedelta(hours=8)

_bearer = HTTPBearer(auto_error=False, scheme_name="bearer_auth")
_cookie = APIKeyCookie(name=SESSION_COOKIE, auto_error=False, scheme_name="cookie_auth")
_secret: str = "dev-secret-change-me-at-least-32-bytes"


def configure(secret: str) -> None:
    global _secret
    _secret = secret


class LoginSession(Base):
    """Relácia po prihlásení (QR-002); odhlásenie ju zruší aj na serveri."""

    __tablename__ = "login_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(default=False)


@dataclass(frozen=True)
class Principal:
    subject_id: str
    role: Role
    nickname: str | None = None
    session_id: uuid.UUID | None = None
    account_id: str | None = None
    expires_at: datetime | None = None

    @property
    def is_staff(self) -> bool:
        return self.role in STAFF


def issue_token(subject_id: str, role: Role, nickname: str | None = None) -> str:
    """Token bez relácie – iba pre vývoj a testy (pod.dev_seed)."""
    claims = {"sub": subject_id, "role": role}
    if nickname:
        claims["nickname"] = nickname
    return jwt.encode(claims, _secret, algorithm="HS256")


def start_session(db: Session, account_id: str, subject_id: str, role: Role,
                  nickname: str | None) -> tuple[str, LoginSession]:
    login = LoginSession(account_id=account_id, expires_at=utcnow() + SESSION_LIFETIME)
    db.add(login)
    db.flush()
    claims = {"sub": subject_id, "role": role, "sid": str(login.session_id), "acc": account_id,
              "exp": int(login.expires_at.timestamp())}
    if nickname:
        claims["nickname"] = nickname
    return jwt.encode(claims, _secret, algorithm="HS256"), login


def end_session(db: Session, principal: Principal) -> None:
    if principal.session_id is not None:
        login = db.get(LoginSession, principal.session_id)
        if login is not None:
            login.revoked = True


def _unauthorized(detail: str) -> Problem:
    return Problem(401, "urn:problem:unauthorized", detail)


def _principal_from(token: str | None, db: Session) -> Principal:
    if not token:
        raise _unauthorized("Nie ste prihlásený.")
    try:
        claims = jwt.decode(token, _secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Relácia vypršala, prihláste sa znova.")
    except jwt.PyJWTError:
        raise _unauthorized("Neplatný token.")
    if claims.get("role") not in ("customer", "modeler", "manager"):
        raise _unauthorized("Token nemá platnú rolu.")
    session_id = expires_at = None
    if "sid" in claims:
        login = db.get(LoginSession, uuid.UUID(claims["sid"]))
        if login is None or login.revoked:
            raise _unauthorized("Relácia bola ukončená.")
        if login.expires_at <= utcnow():
            raise _unauthorized("Relácia vypršala, prihláste sa znova.")
        session_id, expires_at = login.session_id, login.expires_at
    return Principal(subject_id=str(claims["sub"]), role=claims["role"], nickname=claims.get("nickname"),
                     session_id=session_id, account_id=claims.get("acc"), expires_at=expires_at)


def current_principal(creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
                      cookie: str | None = Depends(_cookie),
                      db: Session = Depends(get_session)) -> Principal:
    """Bearer hlavička alebo HttpOnly cookie (contracts 0.3.0)."""
    return _principal_from(creds.credentials if creds else cookie, db)


def cookie_principal(cookie: str | None = Depends(_cookie), db: Session = Depends(get_session)) -> Principal:
    """Iba relácia z cookie (auth-api 0.1.0)."""
    return _principal_from(cookie, db)


def require(principal: Principal, *roles: Role) -> None:
    if principal.role not in roles:
        raise forbidden()
