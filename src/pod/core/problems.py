from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

TITLES = {
    400: "Neplatný vstup",
    401: "Chýba alebo je neplatný token",
    403: "Nemáte oprávnenie",
    404: "Záznam neexistuje",
    409: "Konflikt so stavom",
    429: "Limit vyčerpaný",
}


class Problem(Exception):
    def __init__(self, status: int, type_: str, detail: str, **extra):
        self.status = status
        self.type = type_
        self.detail = detail
        self.extra = extra


def _response(status: int, type_: str, detail: str, instance: str, extra: dict | None = None) -> JSONResponse:
    body = {"type": type_, "title": TITLES.get(status, "Chyba"), "status": status, "detail": detail, "instance": instance}
    body.update(extra or {})
    return JSONResponse(body, status_code=status, media_type="application/problem+json")


def install_problem_handlers(app: FastAPI) -> None:
    @app.exception_handler(Problem)
    async def _problem(request: Request, exc: Problem):
        return _response(exc.status, exc.type, exc.detail, request.url.path, exc.extra)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        return _response(400, "urn:problem:bad_request", str(exc.errors()[:3]), request.url.path)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return _response(exc.status_code, f"urn:problem:http_{exc.status_code}", str(exc.detail), request.url.path)


def not_found(what: str) -> Problem:
    return Problem(404, "urn:problem:not_found", f"{what} neexistuje.")


def forbidden(detail: str = "Rola nemá oprávnenie.") -> Problem:
    return Problem(403, "urn:problem:forbidden", detail)
