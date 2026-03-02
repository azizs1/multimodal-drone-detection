import os

# Must be set before any app module is imported so database.py picks up SQLite
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import pytest
from app.database.database import Base, get_db
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLITE_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    SQLITE_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the real DB dependency with the SQLite one
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True, scope="session")
def setup_database():
    """Create all tables before the test session, drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    if os.path.exists("./test.db"):
        os.remove("./test.db")
