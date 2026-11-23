from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pod.core import auth
from pod.core.db import init_db
from pod.core.problems import install_problem_handlers
from pod.core.settings import Settings
from pod.customer_portal import api as portal_api
from pod.model_repository import service as repository
from pod.model_repository.api import router as repository_router
from pod.model_validator.api import router as validator_router
from pod.modeling_workspace.api import router as workspace_router

SUB_APPS = {
    "/api/customer_portal": ("Authentication API", portal_api.router),
    "/api/modeling_workspace": ("Model Approval API", workspace_router),
    "/api/model_validator": ("Model Validation API", validator_router),
    "/api/model_repository": ("Model Repository API", repository_router),
}

PORTAL_DIR = Path(__file__).resolve().parent.parent / "portal_mock"


VERSIONS = {"Authentication API": "0.1.0"}


def build_sub_app(title: str, router) -> FastAPI:
    sub = FastAPI(title=title, version=VERSIONS.get(title, "0.3.0"))
    install_problem_handlers(sub)
    sub.include_router(router)
    return sub


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    init_db(settings.database_url)
    auth.configure(settings.jwt_secret)
    portal_api.configure(settings.cookie_secure)
    repository.configure(settings.model_storage_dir, settings.upload_limit, settings.upload_limit_period_days)
    Path(settings.model_storage_dir).mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="PrintOnDemand – R-001", version="0.2.0")
    for prefix, (title, router) in SUB_APPS.items():
        app.mount(prefix, build_sub_app(title, router))
    app.mount("/model_files", StaticFiles(directory=settings.model_storage_dir), name="model_files")
    app.mount("/portal", StaticFiles(directory=PORTAL_DIR, html=True), name="portal")
    return app
