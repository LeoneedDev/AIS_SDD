import os
import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from contract_check import ContractIndex
from pod.core import auth
from pod.core.db import Database
from pod.core.settings import Settings
from pod.main import create_app

TEST_DB = os.environ.get("POD_TEST_DATABASE_URL", "postgresql+psycopg://pod:pod@localhost:5432/pod_test")
WS, VAL, REPO = "/api/modeling_workspace", "/api/model_validator", "/api/model_repository"


@pytest.fixture(scope="session")
def contracts():
    return ContractIndex()


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    settings = Settings(database_url=TEST_DB, jwt_secret="test-secret-for-pytest-only-32-bytes!",
                        model_storage_dir=str(tmp_path_factory.mktemp("model_files")),
                        upload_limit=10, upload_limit_period_days=None)
    application = create_app(settings)
    db = Database(TEST_DB)
    try:
        with db.engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception as exc:
        pytest.exit(f"PostgreSQL nie je dostupný ({TEST_DB}): spusti `docker compose up -d`. {exc}", returncode=2)
    application.state.test_db = db
    return application


@pytest.fixture
def db(app):
    database = app.state.test_db
    database.drop_schema()
    database.create_schema()
    return database


class ContractClient:
    """TestClient, ktorý každú odpoveď API overí voči approved contractu."""

    def __init__(self, client: TestClient, contracts: ContractIndex):
        self.client = client
        self.contracts = contracts

    def request(self, method: str, url: str, token: str | None = None, **kwargs):
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self.client.request(method, url, headers=headers, **kwargs)
        if url.startswith("/api/"):
            body = response.json() if response.content else None
            self.contracts.check(method, url.split("?")[0], response.status_code, body)
        return response

    def get(self, url, token=None, **kw):
        return self.request("GET", url, token, **kw)

    def post(self, url, token=None, **kw):
        return self.request("POST", url, token, **kw)


class World:
    def __init__(self, api: ContractClient, db: Database):
        self.api = api
        self.db = db
        self.modeler = auth.issue_token("emp-17", "modeler", "jan.m")
        self.manager = auth.issue_token("emp-02", "manager", "eva.k")
        self.order_id = None
        self.customer = None
        self.model_id = None
        self.approval = None
        self.last = None
        self.data = SimpleNamespace()

    @staticmethod
    def customer_token(customer_id: str) -> str:
        return auth.issue_token(customer_id, "customer")

    def session(self):
        return self.db.sessions.begin()

    def new_order(self, path: str, customer_id: str = "customer-anna", description: str = "Držiak na bicykel",
                  sharing: bool = False) -> uuid.UUID:
        from pod.order_orchestrator import service as orders
        with self.session() as s:
            order = orders.create_order(s, customer_id, path, description, sharing)
            order_id = order.order_id
        self.order_id, self.customer = order_id, self.customer_token(customer_id)
        return order_id

    def upload(self, token: str, content: bytes, order_id=None, name: str = "model.stl", expect: int = 201):
        r = self.api.post(f"{REPO}/orders/{order_id or self.order_id}/model_versions", token,
                          files={"file": (name, content, "application/octet-stream")})
        assert r.status_code == expect, r.text
        if r.status_code == 201:
            self.model_id = r.json()["model_id"]
        return r

    def send_for_approval(self, version: int = 1, origin: str = "new_model", order_id=None):
        r = self.api.post(f"{WS}/orders/{order_id or self.order_id}/model_approvals", self.modeler,
                          json={"model_version": version, "model_origin": origin, "note": "Nový model"})
        assert r.status_code == 201, r.text
        self.approval = r.json()
        return self.approval

    def approval_url(self, suffix: str = "") -> str:
        return f"{WS}/orders/{self.order_id}/model_approvals/{self.approval['model_approval_id']}{suffix}"

    def customer_open(self):
        r = self.api.post(self.approval_url("/review_starts"), self.customer)
        assert r.status_code == 200, r.text
        self.approval = r.json()

    def customer_approve(self):
        r = self.api.post(self.approval_url("/approvals"), self.customer)
        assert r.status_code == 200, r.text
        self.approval = r.json()

    def customer_reject(self, comment: str = "Otvory majú byť väčšie."):
        r = self.api.post(self.approval_url("/rejections"), self.customer, json={"comment": comment})
        assert r.status_code == 200, r.text
        self.approval = self.last = r.json()
        return self.last

    def submit_revision(self, version: int):
        r = self.api.post(self.approval_url("/revisions"), self.modeler, json={"model_version": version})
        assert r.status_code == 200, r.text
        self.approval = r.json()

    def validate(self, version: int, path: str):
        r = self.api.post(f"{VAL}/model_validations", self.modeler, json={
            "order_id": str(self.order_id), "model_id": self.model_id, "model_version": version,
            "print_type": "plast", "path": path})
        assert r.status_code == 201, r.text
        self.last = r.json()
        return self.last

    def refresh_approval(self):
        r = self.api.get(self.approval_url(), self.customer)
        assert r.status_code == 200
        self.approval = r.json()
        return self.approval

    def order(self):
        from pod.order_orchestrator import service as orders
        with self.session() as s:
            return orders.get_order(s, self.order_id)

    def notifications(self, kind: str | None = None):
        from pod.notifier import service as notifier
        with self.session() as s:
            items = notifier.for_order(s, self.order_id)
        return [n for n in items if kind is None or n.kind == kind]

    def task_kinds(self):
        from pod.order_orchestrator import service as orders
        with self.session() as s:
            return [t.kind for t in orders.open_tasks(s, self.order_id)]

    def open_consent_questions(self, consent_type: str):
        from pod.modeling_workspace.models import CustomerConsent
        with self.session() as s:
            return list(s.scalars(select(CustomerConsent).where(
                CustomerConsent.order_id == self.order_id, CustomerConsent.consent_type == consent_type,
                CustomerConsent.decision.is_(None))))

    def version_count(self):
        from pod.model_repository.models import ModelVersion
        if self.model_id is None:
            return 0
        with self.session() as s:
            return len(list(s.scalars(select(ModelVersion).where(ModelVersion.model_id == uuid.UUID(self.model_id)))))


@pytest.fixture
def api(app, contracts):
    with TestClient(app) as client:
        yield ContractClient(client, contracts)


@pytest.fixture
def world(api, db):
    return World(api, db)
