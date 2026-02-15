"""Integration tests for Z-Report endpoints"""
import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
import secrets

from app.main import app
from app.database import get_db
from app.models.models import Business, Submission, ZReport
from app.utils.hmac_signature import HMACSignatureManager
from tests.conftest import create_test_business, create_test_api_key


def setup_test_business(db_session: Session):
    """Setup a test business with API credentials"""
    business = create_test_business(db_session)
    api_key_info = create_test_api_key(db_session, business.id)
    return business, api_key_info.api_key, api_key_info.api_secret


def generate_signature(api_secret: str, request_body: str) -> str:
    """Generate HMAC signature for request"""
    body_hash = HMACSignatureManager.generate_body_hash(request_body.encode())
    message = HMACSignatureManager.generate_signature_message(
        method="POST",
        path="/api/v1/reports/z-report",
        timestamp=datetime.utcnow().isoformat() + "Z",
        body_hash=body_hash
    )
    return HMACSignatureManager.generate_signature(api_secret, message)


client = TestClient(app)


class TestZReportRequestEndpoint:
    """Tests for POST /api/v1/reports/z-report endpoint"""
    
    def test_z_report_request_valid(self, db_session: Session):
        """Test valid Z-Report request returns 202 Accepted"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        request_data = {
            "zd_date": "2026-02-10"
        }
        
        request_body = json.dumps(request_data)
        signature = generate_signature(api_secret, request_body)
        
        # Make request
        response = client.post(
            "/api/v1/reports/z-report",
            json=request_data,
            headers={
                "X-API-Key": api_key,
                "X-API-Signature": signature
            }
        )
        
        # Assertions
        assert response.status_code == 202
        data = response.json()
        assert data["submission_id"] is not None
        assert data["report_date"] == "2026-02-10"
        assert data["status"] == "RECEIVED"
        assert data["message"] is not None
        
        # Verify submission was created
        submission = db_session.query(Submission).filter(
            Submission.id == data["submission_id"]
        ).first()
        assert submission is not None
        assert submission.submission_type == "Z_REPORT"
        assert submission.submission_status == "RECEIVED"
        assert submission.business_id == business.id
    
    def test_z_report_request_invalid_date_format(self, db_session: Session):
        """Test Z-Report request with invalid date format returns 400"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        request_data = {
            "zd_date": "02-10-2026"  # Invalid format
        }
        
        request_body = json.dumps(request_data)
        signature = generate_signature(api_secret, request_body)
        
        # Make request
        response = client.post(
            "/api/v1/reports/z-report",
            json=request_data,
            headers={
                "X-API-Key": api_key,
                "X-API-Signature": signature
            }
        )
        
        # Assertions
        assert response.status_code == 422  # Validation error
    
    def test_z_report_request_invalid_api_key(self, db_session: Session):
        """Test Z-Report request with invalid API key returns 401"""
        request_data = {
            "zd_date": "2026-02-10"
        }
        
        request_body = json.dumps(request_data)
        signature = generate_signature("wrong_secret", request_body)
        
        # Make request
        response = client.post(
            "/api/v1/reports/z-report",
            json=request_data,
            headers={
                "X-API-Key": "invalid_key",
                "X-API-Signature": signature
            }
        )
        
        # Assertions
        assert response.status_code == 401
    
    def test_z_report_request_missing_api_key(self, db_session: Session):
        """Test Z-Report request without API key returns 422 (validation error)"""
        request_data = {
            "zd_date": "2026-02-10"
        }
        
        # Make request without API key
        response = client.post(
            "/api/v1/reports/z-report",
            json=request_data
        )
        
        # Assertions - 422 because schema validation fails before auth
        assert response.status_code == 422
    
    def test_z_report_request_multiple_dates(self, db_session: Session):
        """Test multiple Z-Report requests with different dates"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        dates = ["2026-02-10", "2026-02-11", "2026-02-12"]
        submission_ids = []
        
        for date in dates:
            request_data = {"zd_date": date}
            request_body = json.dumps(request_data)
            signature = generate_signature(api_secret, request_body)
            
            response = client.post(
                "/api/v1/reports/z-report",
                json=request_data,
                headers={
                    "X-API-Key": api_key,
                    "X-API-Signature": signature
                }
            )
            
            assert response.status_code == 202
            data = response.json()
            submission_ids.append(data["submission_id"])
            assert data["report_date"] == date
        
        # Verify all submissions were created
        submissions = db_session.query(Submission).filter(
            Submission.id.in_(submission_ids)
        ).all()
        assert len(submissions) == 3
    
    def test_z_report_request_creates_z_report_record(self, db_session: Session):
        """Test that Z-Report request creates Z-Report record in database"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        request_data = {
            "zd_date": "2026-02-10"
        }
        
        request_body = json.dumps(request_data)
        signature = generate_signature(api_secret, request_body)
        
        # Make request
        response = client.post(
            "/api/v1/reports/z-report",
            json=request_data,
            headers={
                "X-API-Key": api_key,
                "X-API-Signature": signature
            }
        )
        
        assert response.status_code == 202
        
        # Verify Z-Report record was created
        z_report = db_session.query(ZReport).filter(
            ZReport.business_id == business.id,
            ZReport.report_date == "2026-02-10"
        ).first()
        assert z_report is not None
        assert z_report.report_date == "2026-02-10"
    
    def test_z_report_request_response_format(self, db_session: Session):
        """Test Z-Report response has correct format"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        request_data = {
            "zd_date": "2026-02-10"
        }
        
        request_body = json.dumps(request_data)
        signature = generate_signature(api_secret, request_body)
        
        # Make request
        response = client.post(
            "/api/v1/reports/z-report",
            json=request_data,
            headers={
                "X-API-Key": api_key,
                "X-API-Signature": signature
            }
        )
        
        assert response.status_code == 202
        data = response.json()
        
        # Verify response format
        assert "submission_id" in data
        assert "report_date" in data
        assert "status" in data
        assert "message" in data
        assert "timestamp" in data
        assert data["status"] == "RECEIVED"
        assert data["report_date"] == "2026-02-10"
    
    def test_z_report_request_queues_for_processing(self, db_session: Session):
        """Test that Z-Report request is queued for background processing"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        request_data = {
            "zd_date": "2026-02-10"
        }
        
        request_body = json.dumps(request_data)
        signature = generate_signature(api_secret, request_body)
        
        # Make request
        response = client.post(
            "/api/v1/reports/z-report",
            json=request_data,
            headers={
                "X-API-Key": api_key,
                "X-API-Signature": signature
            }
        )
        
        assert response.status_code == 202
        data = response.json()
        
        # Verify submission status is RECEIVED (queued)
        submission = db_session.query(Submission).filter(
            Submission.id == data["submission_id"]
        ).first()
        assert submission.submission_status == "RECEIVED"
    
    def test_z_report_request_stores_raw_request(self, db_session: Session):
        """Test that Z-Report request stores raw request data"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        request_data = {
            "zd_date": "2026-02-10"
        }
        
        request_body = json.dumps(request_data)
        signature = generate_signature(api_secret, request_body)
        
        # Make request
        response = client.post(
            "/api/v1/reports/z-report",
            json=request_data,
            headers={
                "X-API-Key": api_key,
                "X-API-Signature": signature
            }
        )
        
        assert response.status_code == 202
        data = response.json()
        
        # Verify raw request is stored
        submission = db_session.query(Submission).filter(
            Submission.id == data["submission_id"]
        ).first()
        assert submission.raw_request is not None
        assert submission.raw_request["zd_date"] == "2026-02-10"
    
    def test_z_report_request_edge_case_dates(self, db_session: Session):
        """Test Z-Report requests with edge case dates"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        edge_dates = [
            "2026-01-01",  # First day of year
            "2026-12-31",  # Last day of year
            "2024-02-29",  # Leap year
        ]
        
        for date in edge_dates:
            request_data = {"zd_date": date}
            request_body = json.dumps(request_data)
            signature = generate_signature(api_secret, request_body)
            
            response = client.post(
                "/api/v1/reports/z-report",
                json=request_data,
                headers={
                    "X-API-Key": api_key,
                    "X-API-Signature": signature
                }
            )
            
            assert response.status_code == 202
            data = response.json()
            assert data["report_date"] == date


class TestZReportRetrievalEndpoint:
    """Tests for GET /api/v1/reports/z-report/{date} endpoint"""
    
    def test_z_report_retrieval_success(self, db_session: Session):
        """Test successful Z-Report retrieval"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        # Create Z-Report record
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        db_session.add(z_report)
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/v1/reports/z-report/2026-02-10",
            headers={
                "X-API-Key": api_key
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["report_date"] == "2026-02-10"
        assert data["inv_close"] == 5
        assert data["inv_count"] == 10
        assert data["inv_vat"] == 1500.00
        assert data["inv_total"] == 10000.00
        assert data["inv_levy"] == 500.00
    
    def test_z_report_retrieval_not_found(self, db_session: Session):
        """Test Z-Report retrieval for non-existent date returns 404"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        # Make request for non-existent date
        response = client.get(
            "/api/v1/reports/z-report/2026-02-10",
            headers={
                "X-API-Key": api_key
            }
        )
        
        # Assertions
        assert response.status_code == 404
    
    def test_z_report_retrieval_invalid_date_format(self, db_session: Session):
        """Test Z-Report retrieval with invalid date format returns 400"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        # Make request with invalid date
        response = client.get(
            "/api/v1/reports/z-report/02-10-2026",
            headers={
                "X-API-Key": api_key
            }
        )
        
        # Assertions
        assert response.status_code == 400
    
    def test_z_report_retrieval_invalid_api_key(self, db_session: Session):
        """Test Z-Report retrieval with invalid API key returns 401"""
        # Make request with invalid API key
        response = client.get(
            "/api/v1/reports/z-report/2026-02-10",
            headers={
                "X-API-Key": "invalid_key"
            }
        )
        
        # Assertions
        assert response.status_code == 401
    
    def test_z_report_retrieval_multi_tenant_isolation(self, db_session: Session):
        """Test that businesses can only retrieve their own Z-Reports"""
        # Setup two businesses
        business1, api_key1, api_secret1 = setup_test_business(db_session)
        business2, api_key2, api_secret2 = setup_test_business(db_session)
        
        # Create Z-Report for business1
        z_report = ZReport(
            business_id=business1.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10
        )
        db_session.add(z_report)
        db_session.commit()
        
        # Try to retrieve with business2's API key
        response = client.get(
            "/api/v1/reports/z-report/2026-02-10",
            headers={
                "X-API-Key": api_key2
            }
        )
        
        # Assertions - should not find the report
        assert response.status_code == 404
    
    def test_z_report_retrieval_response_format(self, db_session: Session):
        """Test Z-Report retrieval response has correct format"""
        # Setup
        business, api_key, api_secret = setup_test_business(db_session)
        
        # Create Z-Report record
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_vat=1500.00
        )
        db_session.add(z_report)
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/v1/reports/z-report/2026-02-10",
            headers={
                "X-API-Key": api_key
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response format
        assert "report_date" in data
        assert "inv_close" in data
        assert "inv_count" in data
        assert "inv_vat" in data
        assert "created_at" in data
