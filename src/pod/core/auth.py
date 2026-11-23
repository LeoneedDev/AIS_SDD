from dataclasses import dataclass
from typing import Literal

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pod.core.problems import Problem, forbidden

Role = Literal["customer", "modeler", "manager"]
STAFF: tuple[Role, ...] = ("modeler", "manager")

_bearer = HTTPBearer(auto_error=False, scheme_name="bearer_auth")
_secret: str = "dev-secret-change-me-at-least-32-bytes"


def configure(secret: str) -> None:
    global _secret
    _secret = secret


@dataclass(frozen=True)
class Principal:
    subject_id: str
    role: Role
    nickname: str | None = None

    @property
    def is_staff(self) -> bool:
        return self.role in STAFF


def issue_token(subject_id: str, role: Role, nickname: str | None = None) -> str:
    claims = {"sub": subject_id, "role": role}
    if nickname:
        claims["nickname"] = nickname
    return jwt.encode(claims, _secret, algorithm="HS256")


def current_principal(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Principal:
    if creds is None:
        raise Problem(401, "urn:problem:unauthorized", "Chýba bearer token.")
    try:
        claims = jwt.decode(creds.credentials, _secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise Problem(401, "urn:problem:unauthorized", "Neplatný token.")
    if claims.get("role") not in ("customer", "modeler", "manager"):
        raise Problem(401, "urn:problem:unauthorized", "Token nemá platnú rolu.")
    return Principal(subject_id=str(claims["sub"]), role=claims["role"], nickname=claims.get("nickname"))


def require(principal: Principal, *roles: Role) -> None:
    if principal.role not in roles:
        raise forbidden()
