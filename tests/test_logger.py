"""Tests for centralized logging module"""
import pytest
import logging
from app.logger import (
    get_logger,
    get_audit_logger,
    SensitiveDataMasker,
    JSONFormatter,
    TextFormatter,
    AuditLogger,
)


class TestSensitiveDataMasker:
    """Test sensitive data masking functionality"""
    
    def test_mask_value_default(self):
        """Test default masking shows first 4 chars"""
        result = SensitiveDataMasker.mask_value("secret123456")
        assert result == "secr***"
    
    def test_mask_value_tin(self):
        """Test TIN masking shows only last 4 digits"""
        result = SensitiveDataMasker.mask_value("C0022825405", "tin")
        assert result == "***5405"
    
    def test_mask_value_partial(self):
        """Test partial masking shows first and last 4 chars"""
        result = SensitiveDataMasker.mask_value("secret123456789", "partial")
        assert result == "secr***6789"
    
    def test_mask_value_short_string(self):
        """Test masking short strings"""
        result = SensitiveDataMasker.mask_value("abc", "default")
        assert result == "***"
    
    def test_mask_dict_api_key(self):
        """Test masking API key in dictionary"""
        data = {"api_key": "secret123456", "name": "test"}
        result = SensitiveDataMasker.mask_dict(data)
        assert result["api_key"] == "secr***3456"  # partial masking shows first and last 4
        assert result["name"] == "test"
    
    def test_mask_dict_tin(self):
        """Test masking TIN in dictionary"""
        data = {"CLIENT_TIN": "C0022825405", "name": "test"}
        result = SensitiveDataMasker.mask_dict(data)
        assert result["CLIENT_TIN"] == "***5405"
        assert result["name"] == "test"
    
    def test_mask_dict_nested(self):
        """Test masking nested dictionaries"""
        data = {
            "company": {
                "api_secret": "secret123456",
                "name": "ABC Corp"
            },
            "items": [
                {"api_key": "key123456", "value": 100}
            ]
        }
        result = SensitiveDataMasker.mask_dict(data)
        assert result["company"]["api_secret"] == "secr***3456"  # partial masking
        assert result["company"]["name"] == "ABC Corp"
        assert result["items"][0]["api_key"] == "key1***3456"  # partial masking
    
    def test_mask_string_api_key(self):
        """Test masking API key in string"""
        text = "X-API-Key: secret123456"
        result = SensitiveDataMasker.mask_string(text)
        assert "secret123456" not in result
        assert "X-API-Key" in result
    
    def test_mask_string_tin(self):
        """Test masking TIN in string"""
        text = "CLIENT_TIN: C0022825405"
        result = SensitiveDataMasker.mask_string(text)
        assert "C0022825405" not in result
        assert "***5405" in result
    
    def test_mask_string_gra_security_key(self):
        """Test masking GRA security key in string"""
        text = "COMPANY_SECURITY_KEY: UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        result = SensitiveDataMasker.mask_string(text)
        assert "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH" not in result
        assert "COMPANY_SECURITY_KEY" in result


class TestLoggerCreation:
    """Test logger creation and configuration"""
    
    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance"""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_get_logger_has_handlers(self):
        """Test logger has at least one handler"""
        logger = get_logger("test_logger_2")
        assert len(logger.handlers) > 0
    
    def test_get_audit_logger_returns_audit_logger(self):
        """Test get_audit_logger returns an AuditLogger instance"""
        audit_logger = get_audit_logger("test_audit_logger")
        assert isinstance(audit_logger, AuditLogger)
    
    def test_logger_level_configuration(self):
        """Test logger respects configured log level"""
        logger = get_logger("test_logger_level")
        # Logger level should be set from settings
        assert logger.level > 0


class TestAuditLogger:
    """Test audit logger functionality"""
    
    def test_audit_logger_log_request(self, caplog):
        """Test logging API request"""
        audit_logger = get_audit_logger("test_audit")
        
        with caplog.at_level(logging.INFO):
            audit_logger.log_request(
                business_id="biz-123",
                endpoint="/api/v1/invoices/submit",
                method="POST",
                ip_address="192.168.1.1",
                user_agent="TestClient/1.0",
                request_data={"api_key": "secret123"}
            )
        
        assert "API Request" in caplog.text
        # The extra fields are logged in JSON format, check for them in the output
        assert "/api/v1/invoices/submit" in caplog.text
    
    def test_audit_logger_log_response(self, caplog):
        """Test logging API response"""
        audit_logger = get_audit_logger("test_audit_2")
        
        with caplog.at_level(logging.INFO):
            audit_logger.log_response(
                business_id="biz-123",
                endpoint="/api/v1/invoices/submit",
                method="POST",
                status_code=202,
                response_time_ms=150.5,
                response_data={"submission_id": "sub-123"}
            )
        
        assert "API Response" in caplog.text
        assert "202" in caplog.text
    
    def test_audit_logger_log_gra_submission(self, caplog):
        """Test logging GRA submission"""
        audit_logger = get_audit_logger("test_audit_3")
        
        with caplog.at_level(logging.INFO):
            audit_logger.log_gra_submission(
                business_id="biz-123",
                submission_id="sub-123",
                submission_type="INVOICE",
                request_data={"api_secret": "secret123"}
            )
        
        assert "GRA Submission" in caplog.text
        assert "INVOICE" in caplog.text
    
    def test_audit_logger_log_validation_error(self, caplog):
        """Test logging validation error"""
        audit_logger = get_audit_logger("test_audit_4")
        
        with caplog.at_level(logging.WARNING):
            audit_logger.log_validation_error(
                business_id="biz-123",
                submission_id="sub-123",
                error_code="B16",
                error_message="INVOICE TOTAL AMOUNT DIFFERENT",
                field="TOTAL_AMOUNT"
            )
        
        assert "Validation Error" in caplog.text
        assert "B16" in caplog.text
    
    def test_audit_logger_log_auth_attempt_success(self, caplog):
        """Test logging successful authentication"""
        audit_logger = get_audit_logger("test_audit_5")
        
        with caplog.at_level(logging.INFO):
            audit_logger.log_auth_attempt(
                business_id="biz-123",
                ip_address="192.168.1.1",
                success=True
            )
        
        assert "Authentication succeeded" in caplog.text
    
    def test_audit_logger_log_auth_attempt_failure(self, caplog):
        """Test logging failed authentication"""
        audit_logger = get_audit_logger("test_audit_6")
        
        with caplog.at_level(logging.WARNING):
            audit_logger.log_auth_attempt(
                business_id=None,
                ip_address="192.168.1.1",
                success=False,
                reason="Invalid API key"
            )
        
        assert "Authentication failed" in caplog.text
        # The reason is logged in JSON format as extra field
    
    def test_audit_logger_log_authorization_failure(self, caplog):
        """Test logging authorization failure"""
        audit_logger = get_audit_logger("test_audit_7")
        
        with caplog.at_level(logging.WARNING):
            audit_logger.log_authorization_failure(
                business_id="biz-123",
                ip_address="192.168.1.1",
                endpoint="/api/v1/invoices/submit",
                reason="Cross-tenant access attempt"
            )
        
        assert "Authorization failed" in caplog.text
        assert "Cross-tenant access attempt" in caplog.text


class TestFormatterIntegration:
    """Test formatter integration with logging"""
    
    def test_json_formatter_creates_valid_json(self):
        """Test JSON formatter produces valid JSON"""
        import json
        
        logger = get_logger("test_json_formatter")
        handler = logger.handlers[0]
        
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = handler.formatter.format(record)
        
        # Should be valid JSON
        try:
            data = json.loads(formatted)
            assert "timestamp" in data
            assert "level" in data
            assert "message" in data
        except json.JSONDecodeError:
            pytest.fail("Formatter did not produce valid JSON")
