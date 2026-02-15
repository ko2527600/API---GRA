"""Tests for audit logging system"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.models import Business, AuditLog
from app.services.audit_log_service import AuditLogService
from app.logger import get_logger
from tests.conftest import create_test_business, create_test_api_key

logger = get_logger(__name__)


@pytest.fixture
def test_business(db_session):
    """Create a test business"""
    return create_test_business(db_session)


@pytest.fixture
def test_api_key(db_session, test_business):
    """Create a test API key"""
    return create_test_api_key(db_session, test_business.id)


class TestAuditLogService:
    """Test audit log service functionality"""
    
    def test_create_audit_log(self, db_session, test_business):
        """Test creating an audit log entry"""
        audit_log = AuditLogService.create_audit_log(
            db=db_session,
            business_id=test_business.id,
            action="API_REQUEST",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            response_code=202,
            response_status="SUCCESS",
            request_payload={"invoice_num": "INV-001"},
            ip_address="192.168.1.1",
            user_agent="TestClient/1.0",
        )
        
        assert audit_log.id is not None
        assert audit_log.business_id == test_business.id
        assert audit_log.action == "API_REQUEST"
        assert audit_log.endpoint == "/api/v1/invoices/submit"
        assert audit_log.method == "POST"
        assert audit_log.response_code == 202
        assert audit_log.response_status == "SUCCESS"
        assert audit_log.request_payload == {"invoice_num": "INV-001"}
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.user_agent == "TestClient/1.0"
    
    def test_create_audit_log_with_error(self, db_session, test_business):
        """Test creating an audit log with error message"""
        audit_log = AuditLogService.create_audit_log(
            db=db_session,
            business_id=test_business.id,
            action="API_REQUEST",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            response_code=400,
            response_status="FAILED",
            error_message="Validation failed: TOTAL_AMOUNT mismatch",
            ip_address="192.168.1.1",
        )
        
        assert audit_log.response_code == 400
        assert audit_log.response_status == "FAILED"
        assert audit_log.error_message == "Validation failed: TOTAL_AMOUNT mismatch"
    
    def test_get_audit_logs(self, db_session, test_business):
        """Test retrieving audit logs"""
        # Create multiple audit logs
        for i in range(5):
            AuditLogService.create_audit_log(
                db=db_session,
                business_id=test_business.id,
                action="API_REQUEST",
                endpoint=f"/api/v1/endpoint-{i}",
                method="POST",
                response_code=200,
                response_status="SUCCESS",
            )
        
        logs, total = AuditLogService.get_audit_logs(
            db=db_session,
            business_id=test_business.id,
            limit=10,
            offset=0,
        )
        
        assert len(logs) == 5
        assert total == 5
    
    def test_get_audit_logs_with_pagination(self, db_session, test_business):
        """Test retrieving audit logs with pagination"""
        # Create 15 audit logs
        for i in range(15):
            AuditLogService.create_audit_log(
                db=db_session,
                business_id=test_business.id,
                action="API_REQUEST",
                endpoint="/api/v1/invoices/submit",
                method="POST",
                response_code=200,
                response_status="SUCCESS",
            )
        
        # Get first page
        logs1, total1 = AuditLogService.get_audit_logs(
            db=db_session,
            business_id=test_business.id,
            limit=10,
            offset=0,
        )
        
        assert len(logs1) == 10
        assert total1 == 15
        
        # Get second page
        logs2, total2 = AuditLogService.get_audit_logs(
            db=db_session,
            business_id=test_business.id,
            limit=10,
            offset=10,
        )
        
        assert len(logs2) == 5
        assert total2 == 15
    
    def test_get_audit_logs_by_action(self, db_session, test_business):
        """Test retrieving audit logs filtered by action"""
        # Create logs with different actions
        for i in range(3):
            AuditLogService.create_audit_log(
                db=db_session,
                business_id=test_business.id,
                action="API_REQUEST",
                endpoint="/api/v1/invoices/submit",
                method="POST",
                response_code=200,
                response_status="SUCCESS",
            )
        
        for i in range(2):
            AuditLogService.create_audit_log(
                db=db_session,
                business_id=test_business.id,
                action="GRA_SUBMISSION",
                endpoint="/api/v1/invoices/submit",
                method="POST",
                response_code=200,
                response_status="SUCCESS",
            )
        
        # Get logs by action
        logs = AuditLogService.get_audit_logs_by_action(
            db=db_session,
            business_id=test_business.id,
            action="API_REQUEST",
        )
        
        assert len(logs) == 3
        assert all(log.action == "API_REQUEST" for log in logs)
    
    def test_get_audit_logs_by_date_range(self, db_session, test_business):
        """Test retrieving audit logs by date range"""
        # Create logs
        for i in range(5):
            AuditLogService.create_audit_log(
                db=db_session,
                business_id=test_business.id,
                action="API_REQUEST",
                endpoint="/api/v1/invoices/submit",
                method="POST",
                response_code=200,
                response_status="SUCCESS",
            )
        
        # Get logs within date range
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)
        
        logs = AuditLogService.get_audit_logs_by_date_range(
            db=db_session,
            business_id=test_business.id,
            start_date=start_date,
            end_date=end_date,
        )
        
        assert len(logs) == 5
    
    def test_get_audit_log_by_id(self, db_session, test_business):
        """Test retrieving a specific audit log"""
        # Create an audit log
        created_log = AuditLogService.create_audit_log(
            db=db_session,
            business_id=test_business.id,
            action="API_REQUEST",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            response_code=200,
            response_status="SUCCESS",
        )
        
        # Retrieve it
        log = AuditLogService.get_audit_log_by_id(
            db=db_session,
            business_id=test_business.id,
            audit_log_id=created_log.id,
        )
        
        assert log is not None
        assert log.id == created_log.id
        assert log.action == "API_REQUEST"
    
    def test_get_audit_log_by_id_not_found(self, db_session, test_business):
        """Test retrieving non-existent audit log"""
        log = AuditLogService.get_audit_log_by_id(
            db=db_session,
            business_id=test_business.id,
            audit_log_id=uuid4(),
        )
        
        assert log is None
    
    def test_get_audit_log_cross_tenant_isolation(self, db_session):
        """Test that audit logs are isolated per business"""
        # Create two businesses
        business1 = create_test_business(db_session, "Business 1")
        business2 = create_test_business(db_session, "Business 2")
        
        # Create logs for each business
        AuditLogService.create_audit_log(
            db=db_session,
            business_id=business1.id,
            action="API_REQUEST",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            response_code=200,
            response_status="SUCCESS",
        )
        
        AuditLogService.create_audit_log(
            db=db_session,
            business_id=business2.id,
            action="API_REQUEST",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            response_code=200,
            response_status="SUCCESS",
        )
        
        # Get logs for business1
        logs1, total1 = AuditLogService.get_audit_logs(
            db=db_session,
            business_id=business1.id,
        )
        
        # Get logs for business2
        logs2, total2 = AuditLogService.get_audit_logs(
            db=db_session,
            business_id=business2.id,
        )
        
        assert total1 == 1
        assert total2 == 1
        assert logs1[0].business_id == business1.id
        assert logs2[0].business_id == business2.id
    
    def test_delete_old_audit_logs(self, db_session, test_business):
        """Test deleting old audit logs"""
        # Create an old audit log (manually set created_at)
        old_log = AuditLog(
            business_id=test_business.id,
            action="API_REQUEST",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            response_code=200,
            response_status="SUCCESS",
            created_at=datetime.utcnow() - timedelta(days=3000),
        )
        db_session.add(old_log)
        
        # Create a recent log
        recent_log = AuditLogService.create_audit_log(
            db=db_session,
            business_id=test_business.id,
            action="API_REQUEST",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            response_code=200,
            response_status="SUCCESS",
        )
        
        # Delete logs older than 2555 days (7 years)
        deleted_count = AuditLogService.delete_old_audit_logs(
            db=db_session,
            days_to_keep=2555,
        )
        
        assert deleted_count == 1
        
        # Verify old log is deleted
        logs, total = AuditLogService.get_audit_logs(
            db=db_session,
            business_id=test_business.id,
        )
        
        assert total == 1
        assert logs[0].id == recent_log.id
    
    def test_audit_log_tracks_failed_requests(self, db_session, test_business):
        """Test that failed requests are tracked in audit logs"""
        # Create an audit log for a failed request
        audit_log = AuditLogService.create_audit_log(
            db=db_session,
            business_id=test_business.id,
            action="API_REQUEST",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            response_code=400,
            response_status="FAILED",
            error_message="Validation failed: TOTAL_AMOUNT mismatch",
            ip_address="192.168.1.1",
        )
        
        # Verify the log was created
        retrieved_log = AuditLogService.get_audit_log_by_id(
            db=db_session,
            business_id=test_business.id,
            audit_log_id=audit_log.id,
        )
        
        assert retrieved_log.response_code == 400
        assert retrieved_log.response_status == "FAILED"
        assert "TOTAL_AMOUNT" in retrieved_log.error_message
    
    def test_audit_log_tracks_ip_address(self, db_session, test_business):
        """Test that IP addresses are tracked in audit logs"""
        # Create audit logs from different IP addresses
        for ip in ["192.168.1.1", "10.0.0.1", "172.16.0.1"]:
            AuditLogService.create_audit_log(
                db=db_session,
                business_id=test_business.id,
                action="API_REQUEST",
                endpoint="/api/v1/invoices/submit",
                method="POST",
                response_code=200,
                response_status="SUCCESS",
                ip_address=ip,
            )
        
        # Retrieve logs and verify IP addresses
        logs, total = AuditLogService.get_audit_logs(
            db=db_session,
            business_id=test_business.id,
        )
        
        assert total == 3
        ip_addresses = {log.ip_address for log in logs}
        assert ip_addresses == {"192.168.1.1", "10.0.0.1", "172.16.0.1"}
