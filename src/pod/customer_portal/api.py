from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from pod.core import auth
from pod.core.auth import Principal, cookie_principal
from pod.core.db import get_session
from pod.customer_portal import service

router = APIRouter()
_cookie_secure = False


def configure(cookie_secure: bool) -> None:
    global _cookie_secure
    _cookie_secure = cookie_secure


class LoginIn(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class SessionOut(BaseModel):
    account_id: str
    role: Literal["customer", "modeler", "manager"]
    nickname: str | None = None
    expires_at: datetime


@router.post("/sessions", operation_id="create_session", status_code=201, response_model=SessionOut)
def create_session(body: LoginIn, response: Response, db: Session = Depends(get_session),
                   x_correlation_id: str | None = Header(None)):
    token, session = service.login(db, body.login, body.password)
    response.set_cookie(auth.SESSION_COOKIE, token, httponly=True, samesite="strict", path="/",
                        max_age=int(auth.SESSION_LIFETIME.total_seconds()), secure=_cookie_secure)
    return session


@router.get("/sessions/current", operation_id="get_current_session", response_model=SessionOut)
def get_current_session(principal: Principal = Depends(cookie_principal), x_correlation_id: str | None = Header(None)):
    return service.session_out(principal.account_id or principal.subject_id, principal.role,
                               principal.nickname, principal.expires_at)


@router.delete("/sessions/current", operation_id="delete_current_session", status_code=204)
def delete_current_session(response: Response, principal: Principal = Depends(cookie_principal),
                           db: Session = Depends(get_session), x_correlation_id: str | None = Header(None)):
    auth.end_session(db, principal)
    response.delete_cookie(auth.SESSION_COOKIE, path="/", httponly=True, samesite="strict", secure=_cookie_secure)
    response.status_code = 204
    return None
