"""SQLAlchemy models for GRA External Integration API"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Enum, 
    ForeignKey, Text, JSON, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.models.base import Base, TimestampMixin


class SubmissionStatus(str, enum.Enum):
    """Submission status values"""
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PENDING_GRA = "PENDING_GRA"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class SubmissionType(str, enum.Enum):
    """Submission type values"""
    INVOICE = "INVOICE"
    REFUND = "REFUND"
    PURCHASE = "PURCHASE"
    ITEM = "ITEM"
    INVENTORY = "INVENTORY"
    TIN_VALIDATION = "TIN_VALIDATION"
    TAG_DESCRIPTION = "TAG_DESCRIPTION"
    Z_REPORT = "Z_REPORT"
    VSDC_HEALTH_CHECK = "VSDC_HEALTH_CHECK"


class TaxCode(str, enum.Enum):
    """Tax code values"""
    A = "A"  # Exempted
    B = "B"  # Taxable
    C = "C"  # Export
    D = "D"  # Non-Taxable
    E = "E"  # Non-VAT


class ComputationType(str, enum.Enum):
    """Computation type values"""
    INCLUSIVE = "INCLUSIVE"
    EXCLUSIVE = "EXCLUSIVE"


class Flag(str, enum.Enum):
    """Flag values for submission type"""
    INVOICE = "INVOICE"
    REFUND = "REFUND"
    PROFORMA = "PROFORMA"
    PARTIAL_REFUND = "PARTIAL_REFUND"
    PURCHASE = "PURCHASE"


class TINValidationStatus(str, enum.Enum):
    """TIN validation status values"""
    VALID = "VALID"
    INVALID = "INVALID"
    STOPPED = "STOPPED"
    PROTECTED = "PROTECTED"


class VSDCStatus(str, enum.Enum):
    """VSDC health check status values"""
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"


class Business(Base, TimestampMixin):
    """Business registration model"""
    __tablename__ = "businesses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    api_secret = Column(String(255), nullable=False)  # Hashed
    gra_tin = Column(String(255), nullable=False)  # Encrypted
    gra_company_name = Column(String(255), nullable=False)  # Encrypted
    gra_security_key = Column(String(255), nullable=False)  # Encrypted
    status = Column(String(50), default="active", nullable=False)
    
    # Relationships
    submissions = relationship("Submission", back_populates="business", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="business", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="business", cascade="all, delete-orphan")
    items = relationship("Item", back_populates="business", cascade="all, delete-orphan")
    tag_descriptions = relationship("TagDescription", back_populates="business", cascade="all, delete-orphan")
    z_reports = relationship("ZReport", cascade="all, delete-orphan")
    vsdc_health_checks = relationship("VSDCHealthCheck", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_business_api_key", "api_key"),
        Index("idx_business_status", "status"),
    )
    
    def get_decrypted_gra_tin(self) -> str:
        """
        Get decrypted GRA TIN.
        
        Returns:
            Decrypted GRA TIN
            
        Raises:
            ValueError: If decryption fails
        """
        from app.utils.encryption import encryption_manager
        if not encryption_manager:
            raise ValueError("Encryption manager not initialized")
        return encryption_manager.decrypt(self.gra_tin)
    
    def get_decrypted_gra_company_name(self) -> str:
        """
        Get decrypted GRA company name.
        
        Returns:
            Decrypted GRA company name
            
        Raises:
            ValueError: If decryption fails
        """
        from app.utils.encryption import encryption_manager
        if not encryption_manager:
            raise ValueError("Encryption manager not initialized")
        return encryption_manager.decrypt(self.gra_company_name)
    
    def get_decrypted_gra_security_key(self) -> str:
        """
        Get decrypted GRA security key.
        
        Returns:
            Decrypted GRA security key
            
        Raises:
            ValueError: If decryption fails
        """
        from app.utils.encryption import encryption_manager
        if not encryption_manager:
            raise ValueError("Encryption manager not initialized")
        return encryption_manager.decrypt(self.gra_security_key)
    
    def get_decrypted_gra_credentials(self) -> dict:
        """
        Get all decrypted GRA credentials as a dictionary.
        
        Returns:
            Dictionary with keys: gra_tin, gra_company_name, gra_security_key
            
        Raises:
            ValueError: If decryption fails
        """
        return {
            "gra_tin": self.get_decrypted_gra_tin(),
            "gra_company_name": self.get_decrypted_gra_company_name(),
            "gra_security_key": self.get_decrypted_gra_security_key(),
        }


class Submission(Base, TimestampMixin):
    """Submission tracking model"""
    __tablename__ = "submissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    submission_type = Column(String(50), nullable=False)
    submission_status = Column(String(50), default=SubmissionStatus.RECEIVED.value, nullable=False)
    gra_response_code = Column(String(50), nullable=True)
    gra_response_message = Column(Text, nullable=True)
    gra_invoice_id = Column(String(255), nullable=True)
    gra_qr_code = Column(Text, nullable=True)
    gra_receipt_num = Column(String(255), nullable=True)
    # Signature/Stamping details from VSDC
    ysdcid = Column(String(255), nullable=True)
    ysdcrecnum = Column(String(255), nullable=True)
    ysdcintdata = Column(Text, nullable=True)
    ysdcnrc = Column(String(255), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    raw_request = Column(JSON, nullable=False)
    raw_response = Column(JSON, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="submissions")
    invoice = relationship("Invoice", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    refund = relationship("Refund", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    purchase = relationship("Purchase", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_submission_business_id", "business_id"),
        Index("idx_submission_status", "submission_status"),
        Index("idx_submission_type", "submission_type"),
        Index("idx_submission_created_at", "created_at"),
    )


class Invoice(Base, TimestampMixin):
    """Invoice model"""
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False, unique=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    invoice_num = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)
    client_tin = Column(String(50), nullable=True)
    invoice_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    computation_type = Column(String(50), nullable=False)
    total_vat = Column(Float, nullable=False)
    total_levy = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    items_count = Column(Integer, nullable=False)
    
    # Relationships
    submission = relationship("Submission", back_populates="invoice")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("business_id", "invoice_num", name="uq_business_invoice_num"),
        Index("idx_invoice_business_id", "business_id"),
        Index("idx_invoice_num", "invoice_num"),
        Index("idx_invoice_date", "invoice_date"),
    )


class InvoiceItem(Base, TimestampMixin):
    """Invoice item model"""
    __tablename__ = "invoice_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    itmref = Column(String(255), nullable=False)
    itmdes = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unityprice = Column(Float, nullable=False)
    taxcode = Column(String(10), nullable=False)
    taxrate = Column(Float, nullable=False)
    levy_amount_a = Column(Float, nullable=False)
    levy_amount_b = Column(Float, nullable=False)
    levy_amount_c = Column(Float, nullable=False)
    levy_amount_d = Column(Float, nullable=False)
    itmdiscount = Column(Float, default=0.0, nullable=False)
    item_total = Column(Float, nullable=False)
    item_category = Column(String(255), nullable=True)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    
    __table_args__ = (
        Index("idx_invoice_item_invoice_id", "invoice_id"),
        Index("idx_invoice_item_itmref", "itmref"),
    )


class Refund(Base, TimestampMixin):
    """Refund model"""
    __tablename__ = "refunds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False, unique=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    refund_id = Column(String(255), nullable=False)
    original_invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    refund_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    total_vat = Column(Float, nullable=False)
    total_levy = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    items_count = Column(Integer, nullable=False)
    
    # Relationships
    submission = relationship("Submission", back_populates="refund")
    items = relationship("RefundItem", back_populates="refund", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_refund_business_id", "business_id"),
        Index("idx_refund_id", "refund_id"),
    )


class RefundItem(Base, TimestampMixin):
    """Refund item model"""
    __tablename__ = "refund_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    refund_id = Column(UUID(as_uuid=True), ForeignKey("refunds.id"), nullable=False, index=True)
    itmref = Column(String(255), nullable=False)
    itmdes = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unityprice = Column(Float, nullable=False)
    taxcode = Column(String(10), nullable=False)
    taxrate = Column(Float, nullable=False)
    levy_amount_a = Column(Float, nullable=False)
    levy_amount_b = Column(Float, nullable=False)
    levy_amount_c = Column(Float, nullable=False)
    levy_amount_d = Column(Float, nullable=False)
    item_total = Column(Float, nullable=False)
    
    # Relationships
    refund = relationship("Refund", back_populates="items")
    
    __table_args__ = (
        Index("idx_refund_item_refund_id", "refund_id"),
    )


class Purchase(Base, TimestampMixin):
    """Purchase model"""
    __tablename__ = "purchases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False, unique=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    purchase_num = Column(String(255), nullable=False)
    supplier_name = Column(String(255), nullable=False)
    supplier_tin = Column(String(50), nullable=True)
    purchase_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    total_vat = Column(Float, nullable=False)
    total_levy = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    items_count = Column(Integer, nullable=False)
    
    # Relationships
    submission = relationship("Submission", back_populates="purchase")
    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("business_id", "purchase_num", name="uq_business_purchase_num"),
        Index("idx_purchase_business_id", "business_id"),
        Index("idx_purchase_num", "purchase_num"),
    )


class PurchaseItem(Base, TimestampMixin):
    """Purchase item model"""
    __tablename__ = "purchase_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_id = Column(UUID(as_uuid=True), ForeignKey("purchases.id"), nullable=False, index=True)
    itmref = Column(String(255), nullable=False)
    itmdes = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unityprice = Column(Float, nullable=False)
    taxcode = Column(String(10), nullable=False)
    taxrate = Column(Float, nullable=False)
    item_total = Column(Float, nullable=False)
    
    # Relationships
    purchase = relationship("Purchase", back_populates="items")
    
    __table_args__ = (
        Index("idx_purchase_item_purchase_id", "purchase_id"),
    )


class Item(Base, TimestampMixin):
    """Item registration model"""
    __tablename__ = "items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    item_ref = Column(String(255), nullable=False)
    item_name = Column(String(255), nullable=False)
    item_category = Column(String(255), nullable=True)
    tax_code = Column(String(10), nullable=False)
    gra_registration_status = Column(String(50), default="PENDING", nullable=False)
    gra_item_id = Column(String(255), nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="items")
    
    __table_args__ = (
        UniqueConstraint("business_id", "item_ref", name="uq_business_item_ref"),
        Index("idx_item_business_id", "business_id"),
        Index("idx_item_ref", "item_ref"),
    )


class Inventory(Base, TimestampMixin):
    """Inventory model"""
    __tablename__ = "inventory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    niki_code = Column(String(255), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    gra_sync_status = Column(String(50), default="PENDING", nullable=False)
    
    # Relationships
    item = relationship("Item", backref="inventory_records")
    
    __table_args__ = (
        UniqueConstraint("business_id", "niki_code", name="uq_business_niki_code"),
        Index("idx_inventory_business_id", "business_id"),
        Index("idx_inventory_niki_code", "niki_code"),
    )


class TINValidation(Base, TimestampMixin):
    """TIN validation cache model"""
    __tablename__ = "tin_validations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    tin = Column(String(50), nullable=False)
    validation_status = Column(String(50), nullable=False)
    taxpayer_name = Column(String(255), nullable=True)
    gra_response_code = Column(String(50), nullable=True)
    cached_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("business_id", "tin", name="uq_business_tin"),
        Index("idx_tin_validation_business_id", "business_id"),
        Index("idx_tin_validation_tin", "tin"),
        Index("idx_tin_validation_expires_at", "expires_at"),
    )


class TagDescription(Base, TimestampMixin):
    """Tag description model"""
    __tablename__ = "tag_descriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    tag_code = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(255), nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="tag_descriptions")
    
    __table_args__ = (
        UniqueConstraint("business_id", "tag_code", name="uq_business_tag_code"),
        Index("idx_tag_description_business_id", "business_id"),
        Index("idx_tag_description_tag_code", "tag_code"),
    )


class ZReport(Base, TimestampMixin):
    """Z-Report model"""
    __tablename__ = "z_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    report_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    inv_close = Column(Integer, nullable=True)
    inv_count = Column(Integer, nullable=True)
    inv_open = Column(Integer, nullable=True)
    inv_vat = Column(Float, nullable=True)
    inv_total = Column(Float, nullable=True)
    inv_levy = Column(Float, nullable=True)
    gra_response_code = Column(String(50), nullable=True)
    raw_response = Column(JSON, nullable=True)
    
    __table_args__ = (
        UniqueConstraint("business_id", "report_date", name="uq_business_report_date"),
        Index("idx_z_report_business_id", "business_id"),
        Index("idx_z_report_date", "report_date"),
    )


class VSDCHealthCheck(Base, TimestampMixin):
    """VSDC health check model"""
    __tablename__ = "vsdc_health_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    sdc_id = Column(String(255), nullable=True)
    gra_response_code = Column(String(50), nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    __table_args__ = (
        Index("idx_vsdc_health_check_business_id", "business_id"),
        Index("idx_vsdc_health_check_expires_at", "expires_at"),
    )


class AuditLog(Base, TimestampMixin):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    request_payload = Column(JSON, nullable=True)
    response_code = Column(Integer, nullable=False)
    response_status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Relationships
    business = relationship("Business", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_log_business_id", "business_id"),
        Index("idx_audit_log_created_at", "created_at"),
        Index("idx_audit_log_action", "action"),
    )


class Webhook(Base, TimestampMixin):
    """Webhook registration model"""
    __tablename__ = "webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False, index=True)
    webhook_url = Column(String(500), nullable=False)
    events = Column(JSON, nullable=False)  # List of event types
    is_active = Column(Boolean, default=True, nullable=False)
    secret = Column(String(255), nullable=False)  # For HMAC signature
    
    # Relationships
    business = relationship("Business", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_webhook_business_id", "business_id"),
        Index("idx_webhook_is_active", "is_active"),
    )


class WebhookDelivery(Base, TimestampMixin):
    """Webhook delivery tracking model"""
    __tablename__ = "webhook_deliveries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.id"), nullable=False, index=True)
    event_type = Column(String(255), nullable=False)
    submission_id = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSON, nullable=False)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    delivery_status = Column(String(50), nullable=False)  # SUCCESS, FAILED, PENDING
    retry_count = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    
    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")
    
    __table_args__ = (
        Index("idx_webhook_delivery_webhook_id", "webhook_id"),
        Index("idx_webhook_delivery_status", "delivery_status"),
        Index("idx_webhook_delivery_next_retry_at", "next_retry_at"),
    )
