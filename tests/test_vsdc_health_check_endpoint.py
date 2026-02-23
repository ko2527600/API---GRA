"""Tests for VSDC health check endpoints"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.models.models import Business, VSDCHealthCheck
from app.services.business_service import BusinessService


client = TestClient(app)


@pytest.fixture
def test_db():
    """Create test database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.base import Base
    
    #