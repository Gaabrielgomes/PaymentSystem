import pytest
import app.relay as relay_module
import app.consumer as consumer_module
from unittest.mock import patch
from testcontainers.community.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.base import Base
from app.main import app
from app.db.session import get_db

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def engine(postgres_container):
    url = postgres_container.get_connection_url()
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client(engine, db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def concurrent_client(engine):
    Session = sessionmaker(bind=engine)

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def relay_session_factory(engine):
    Session = sessionmaker(bind=engine)
    created_sessions = []

    def factory():
        session = Session()
        created_sessions.append(session)
        return session

    with patch.object(relay_module, "SessionLocal", factory):
        yield factory

    for session in created_sessions:
        session.close()


@pytest.fixture
def consumer_session_factory(engine):
    Session = sessionmaker(bind=engine)
    created_sessions = []

    def factory():
        session = Session()
        created_sessions.append(session)
        return session

    with patch.object(consumer_module, "SessionLocal", factory):
        yield factory

    for session in created_sessions:
        session.close()