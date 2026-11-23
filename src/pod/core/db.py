from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


class Database:
    def __init__(self, url: str):
        self.engine = create_engine(url)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        import pod.core.auth  # noqa: F401
        import pod.customer_portal.models  # noqa: F401
        import pod.model_repository.models  # noqa: F401
        import pod.model_validator.models  # noqa: F401
        import pod.modeling_workspace.models  # noqa: F401
        import pod.notifier.models  # noqa: F401
        import pod.order_orchestrator.models  # noqa: F401

        Base.metadata.create_all(self.engine)

    def drop_schema(self) -> None:
        Base.metadata.drop_all(self.engine)


_db: Database | None = None


def init_db(url: str) -> Database:
    global _db
    _db = Database(url)
    return _db


def get_session() -> Iterator[Session]:
    assert _db is not None, "Database not initialised"
    with _db.sessions() as session:
        with session.begin():
            yield session
