"""Pytest configuration and fixtures"""
import os
import sys

# Set environment variables IMMEDIATELY at module load time
# This must happen BEFORE any app imports
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/API_s_GRA"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-for-testing-only-12345"
os.environ["API_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DEBUG"] = "True"

# Clear any previously imported app modules
for module in list(sys.modules.keys()):
    if module.startswith('app'):
        del sys.modules[module]

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base


def pytest_configure(config):
    """Configure pytest"""
    pass


@pytest.fixture
def api_key():
    """Test API key"""
    return "test-api-key-12345"

@pytest.fixture
def api_secret():
    """Test API secret"""
    return "test-api-secret-67890"

@pytest.fixture
def db_session():
    """Create a test database session using PostgreSQL"""
    # Use PostgreSQL database for testing
    database_url = "postgresql://postgres:postgres@localhost:5432/API_s_GRA"
    engine = create_engine(database_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session with autoflush=False to have better control
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()


def create_test_business(db_session, name="Test Business"):
    """Create a test business"""
    from app.models.models import Business
    from uuid import uuid4
    import secrets
    
    business = Business(
        id=uuid4(),
        name=name,
        api_key=secrets.token_urlsafe(32),
        api_secret=secrets.token_urlsafe(32),
        gra_tin="C00XXXXXXXX",
        gra_company_name="Test Company",
        gra_security_key="test-security-key"
    )
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)
    return business


def create_test_api_key(db_session, business_id):
    """Get the API key for a business"""
    from app.models.models import Business
    
    business = db_session.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise ValueError(f"Business {business_id} not found")
    
    # Return a simple object with api_key and api_secret attributes
    class APIKeyInfo:
        def __init__(self, api_key, api_secret):
            self.api_key = api_key
            self.api_secret = api_secret
    
    return APIKeyInfo(business.api_key, business.api_secret)


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data before each test"""
    from sqlalchemy import create_engine, text
    database_url = "postgresql://postgres:postgres@localhost:5432/API_s_GRA"
    engine = create_engine(database_url)
    
    # Clean up test data with specific API keys before test
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM invoices WHERE submission_id IN (SELECT id FROM submissions WHERE business_id IN (SELECT id FROM businesses WHERE api_key LIKE 'test-api-key%'))"))
            conn.execute(text("DELETE FROM submissions WHERE business_id IN (SELECT id FROM businesses WHERE api_key LIKE 'test-api-key%')"))
            conn.execute(text("DELETE FROM businesses WHERE api_key LIKE 'test-api-key%'"))
            conn.commit()
    except:
        pass  # Ignore errors during cleanup
    
    yield
    
    # Cleanup after test
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM invoices WHERE submission_id IN (SELECT id FROM submissions WHERE business_id IN (SELECT id FROM businesses WHERE api_key LIKE 'test-api-key%'))"))
            conn.execute(text("DELETE FROM submissions WHERE business_id IN (SELECT id FROM businesses WHERE api_key LIKE 'test-api-key%')"))
            conn.execute(text("DELETE FROM businesses WHERE api_key LIKE 'test-api-key%'"))
            conn.commit()
    except:
        pass  # Ignore errors during cleanup


@pytest.fixture
def client_with_db(db_session):
    """Create a test client with database override"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    
    def override_get_db():
        # Return the same session used for test setup
        try:
            yield db_session
        finally:
            pass  # Don't close - let fixture handle it
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    # Cleanup
    app.dependency_overrides.clear()
