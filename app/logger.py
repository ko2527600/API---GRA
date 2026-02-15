"""Centralized logging configuration with sensitive data masking"""
import logging
import json
import re
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from app.config import settings


class SensitiveDataMasker:
    """Utility class for masking sensitive data in logs"""
    
    # Patterns for sensitive data
    SENSITIVE_PATTERNS = {
        "api_key": r"(X-API-Key|api_key|API_KEY)[\s:]*([^\s,}\"]+)",
        "api_secret": r"(X-API-Signature|api_secret|API_SECRET|secret)[\s:]*([^\s,}\"]+)",
        "gra_security_key": r"(COMPANY_SECURITY_KEY|gra_security_key|security_key)[\s:]*([^\s,}\"]+)",
        "tin": r"(CLIENT_TIN|COMPANY_TIN|client_tin|company_tin|TIN)[\s:]*([A-Z0-9]{11,15})",
        "password": r"(password|passwd)[\s:]*([^\s,}\"]+)",
        "encryption_key": r"(encryption_key|ENCRYPTION_KEY)[\s:]*([^\s,}\"]+)",
    }
    
    @staticmethod
    def mask_value(value: str, mask_type: str = "default") -> str:
        """
        Mask a sensitive value
        
        Args:
            value: The value to mask
            mask_type: Type of masking (default, tin, partial)
            
        Returns:
            Masked value
        """
        if not value or len(value) == 0:
            return value
        
        if mask_type == "tin":
            # Show only last 4 digits for TIN
            if len(value) > 4:
                return f"***{value[-4:]}"
            return "***"
        elif mask_type == "partial":
            # Show first 4 and last 4 characters
            if len(value) > 8:
                return f"{value[:4]}***{value[-4:]}"
            return "***"
        else:
            # Default: show only first 4 characters
            if len(value) > 4:
                return f"{value[:4]}***"
            return "***"
    
    @staticmethod
    def mask_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask sensitive data in a dictionary
        
        Args:
            data: Dictionary to mask
            
        Returns:
            Dictionary with sensitive data masked
        """
        if not isinstance(data, dict):
            return data
        
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            
            # Check if key matches sensitive patterns
            if any(pattern in key_lower for pattern in [
                "api_key", "api_secret", "signature", "secret", 
                "password", "encryption_key", "security_key"
            ]):
                masked[key] = SensitiveDataMasker.mask_value(str(value), "partial")
            elif any(pattern in key_lower for pattern in ["tin", "tpin"]):
                masked[key] = SensitiveDataMasker.mask_value(str(value), "tin")
            elif isinstance(value, dict):
                masked[key] = SensitiveDataMasker.mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [
                    SensitiveDataMasker.mask_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        
        return masked
    
    @staticmethod
    def mask_string(text: str) -> str:
        """
        Mask sensitive data in a string
        
        Args:
            text: String to mask
            
        Returns:
            String with sensitive data masked
        """
        if not isinstance(text, str):
            return text
        
        masked = text
        
        # Mask API keys and secrets
        masked = re.sub(
            r"(X-API-Key|api_key|API_KEY)[\s:]*([^\s,}\"]+)",
            r"\1: ****",
            masked,
            flags=re.IGNORECASE
        )
        
        # Mask signatures
        masked = re.sub(
            r"(X-API-Signature|api_signature|signature)[\s:]*([^\s,}\"]+)",
            r"\1: ****",
            masked,
            flags=re.IGNORECASE
        )
        
        # Mask GRA security keys
        masked = re.sub(
            r"(COMPANY_SECURITY_KEY|security_key)[\s:]*([^\s,}\"]+)",
            r"\1: ****",
            masked,
            flags=re.IGNORECASE
        )
        
        # Mask TINs (show only last 4 digits)
        masked = re.sub(
            r"(CLIENT_TIN|COMPANY_TIN|client_tin|company_tin)[\s:]*([A-Z0-9]{11,15})",
            lambda m: f"{m.group(1)}: ***{m.group(2)[-4:]}",
            masked,
            flags=re.IGNORECASE
        )
        
        # Mask passwords
        masked = re.sub(
            r"(password|passwd)[\s:]*([^\s,}\"]+)",
            r"\1: ****",
            masked,
            flags=re.IGNORECASE
        )
        
        return masked


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": SensitiveDataMasker.mask_string(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            extra = record.extra
            if isinstance(extra, dict):
                extra = SensitiveDataMasker.mask_dict(extra)
            log_data.update(extra)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Custom text formatter with sensitive data masking"""
    
    def format(self, record):
        message = SensitiveDataMasker.mask_string(record.getMessage())
        return f"{record.asctime} - {record.name} - {record.levelname} - {message}"


class AuditLogger:
    """Specialized logger for audit logging"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(
        self,
        business_id: str,
        endpoint: str,
        method: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Log API request
        
        Args:
            business_id: Business identifier
            endpoint: API endpoint
            method: HTTP method
            ip_address: Client IP address
            user_agent: Client user agent
            request_data: Request payload (will be masked)
        """
        masked_data = SensitiveDataMasker.mask_dict(request_data) if request_data else {}
        
        self.logger.info(
            f"API Request: {method} {endpoint}",
            extra={
                "audit": True,
                "action": "API_REQUEST",
                "business_id": business_id,
                "endpoint": endpoint,
                "method": method,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_data": masked_data,
            }
        )
    
    def log_response(
        self,
        business_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Log API response
        
        Args:
            business_id: Business identifier
            endpoint: API endpoint
            method: HTTP method
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            response_data: Response payload (will be masked)
        """
        masked_data = SensitiveDataMasker.mask_dict(response_data) if response_data else {}
        
        self.logger.info(
            f"API Response: {method} {endpoint} - {status_code}",
            extra={
                "audit": True,
                "action": "API_RESPONSE",
                "business_id": business_id,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "response_data": masked_data,
            }
        )
    
    def log_gra_submission(
        self,
        business_id: str,
        submission_id: str,
        submission_type: str,
        request_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Log GRA submission
        
        Args:
            business_id: Business identifier
            submission_id: Submission identifier
            submission_type: Type of submission (INVOICE, REFUND, etc)
            request_data: Request payload (will be masked)
        """
        masked_data = SensitiveDataMasker.mask_dict(request_data) if request_data else {}
        
        self.logger.info(
            f"GRA Submission: {submission_type}",
            extra={
                "audit": True,
                "action": "GRA_SUBMISSION",
                "business_id": business_id,
                "submission_id": submission_id,
                "submission_type": submission_type,
                "request_data": masked_data,
            }
        )
    
    def log_gra_response(
        self,
        business_id: str,
        submission_id: str,
        response_code: str,
        response_message: str,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Log GRA response
        
        Args:
            business_id: Business identifier
            submission_id: Submission identifier
            response_code: GRA response code
            response_message: GRA response message
            response_data: Response payload (will be masked)
        """
        masked_data = SensitiveDataMasker.mask_dict(response_data) if response_data else {}
        
        self.logger.info(
            f"GRA Response: {response_code} - {response_message}",
            extra={
                "audit": True,
                "action": "GRA_RESPONSE",
                "business_id": business_id,
                "submission_id": submission_id,
                "response_code": response_code,
                "response_message": response_message,
                "response_data": masked_data,
            }
        )
    
    def log_validation_error(
        self,
        business_id: str,
        submission_id: str,
        error_code: str,
        error_message: str,
        field: Optional[str] = None,
    ):
        """
        Log validation error
        
        Args:
            business_id: Business identifier
            submission_id: Submission identifier
            error_code: Error code
            error_message: Error message
            field: Field that failed validation
        """
        self.logger.warning(
            f"Validation Error: {error_code} - {error_message}",
            extra={
                "audit": True,
                "action": "VALIDATION_ERROR",
                "business_id": business_id,
                "submission_id": submission_id,
                "error_code": error_code,
                "error_message": error_message,
                "field": field,
            }
        )
    
    def log_auth_attempt(
        self,
        business_id: Optional[str],
        ip_address: str,
        success: bool,
        reason: Optional[str] = None,
    ):
        """
        Log authentication attempt
        
        Args:
            business_id: Business identifier (None if auth failed)
            ip_address: Client IP address
            success: Whether authentication succeeded
            reason: Reason for failure (if applicable)
        """
        level = "info" if success else "warning"
        action = "AUTH_SUCCESS" if success else "AUTH_FAILED"
        
        log_func = self.logger.info if success else self.logger.warning
        log_func(
            f"Authentication {'succeeded' if success else 'failed'}",
            extra={
                "audit": True,
                "action": action,
                "business_id": business_id,
                "ip_address": ip_address,
                "reason": reason,
            }
        )
    
    def log_authorization_failure(
        self,
        business_id: str,
        ip_address: str,
        endpoint: str,
        reason: str,
    ):
        """
        Log authorization failure
        
        Args:
            business_id: Business identifier
            ip_address: Client IP address
            endpoint: Attempted endpoint
            reason: Reason for failure
        """
        self.logger.warning(
            f"Authorization failed: {reason}",
            extra={
                "audit": True,
                "action": "AUTHZ_FAILURE",
                "business_id": business_id,
                "ip_address": ip_address,
                "endpoint": endpoint,
                "reason": reason,
            }
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(settings.LOG_LEVEL)
    
    # Set formatter based on configuration
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Add file handler if configured
    if settings.LOG_FILE:
        try:
            file_handler = logging.FileHandler(settings.LOG_FILE)
            file_handler.setLevel(settings.LOG_LEVEL)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to create file handler: {str(e)}")
    
    return logger


def get_audit_logger(name: str) -> AuditLogger:
    """
    Get an audit logger instance
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        AuditLogger instance
    """
    logger = get_logger(name)
    return AuditLogger(logger)


# Create root logger
logger = get_logger("gra_api")

# Create audit logger
audit_logger = get_audit_logger("gra_api.audit")
