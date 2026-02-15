"""Tests for health check endpoint"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health_check():
    """Test that health check endpoint returns 200"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "version" in response.json()
    assert "environment" in response.json()
