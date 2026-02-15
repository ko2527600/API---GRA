"""Tests for Z-Report endpoints and schemas"""
import pytest
from datetime import datetime
from app.schemas.z_report import (
    ZReportRequestSchema,
    ZReportResponseSchema,
    ZReportRetrievalSchema,
    ZReportDataSchema
)


class TestZReportSchemas:
    """Tests for Z-Report schemas"""
    
    def test_z_report_request_schema_valid(self):
        """Test valid Z-Report request schema"""
        request_data = {"zd_date": "2026-02-10"}
        schema = ZReportRequestSchema(**request_data)
        assert schema.zd_date == "2026-02-10"
    
    def test_z_report_request_schema_invalid_format(self):
        """Test Z-Report request schema with invalid date format"""
        request_data = {"zd_date": "02-10-2026"}
        with pytest.raises(ValueError):
            ZReportRequestSchema(**request_data)
    
    def test_z_report_request_schema_various_dates(self):
        """Test Z-Report request schema with various valid dates"""
        valid_dates = [
            "2026-01-01",
            "2026-12-31",
            "2025-06-15",
            "2024-02-29"
        ]
        
        for date in valid_dates:
            schema = ZReportRequestSchema(zd_date=date)
            assert schema.zd_date == date
    
    def test_z_report_data_schema(self):
        """Test Z-Report data schema"""
        data = {
            "inv_close": 5,
            "inv_count": 10,
            "inv_open": 5,
            "inv_vat": 1500.00,
            "inv_total": 10000.00,
            "inv_levy": 500.00
        }
        schema = ZReportDataSchema(**data)
        assert schema.inv_close == 5
        assert schema.inv_count == 10
        assert schema.inv_vat == 1500.00
    
    def test_z_report_data_schema_partial(self):
        """Test Z-Report data schema with partial data"""
        data = {
            "inv_close": 5,
            "inv_count": 10
        }
        schema = ZReportDataSchema(**data)
        assert schema.inv_close == 5
        assert schema.inv_count == 10
        assert schema.inv_open is None
        assert schema.inv_vat is None
    
    def test_z_report_response_schema(self):
        """Test Z-Report response schema"""
        response_data = {
            "submission_id": "uuid-12345",
            "report_date": "2026-02-10",
            "status": "RECEIVED",
            "data": None,
            "gra_response_code": None,
            "message": "Z-Report request received",
            "timestamp": datetime.utcnow()
        }
        schema = ZReportResponseSchema(**response_data)
        assert schema.submission_id == "uuid-12345"
        assert schema.report_date == "2026-02-10"
        assert schema.status == "RECEIVED"
    
    def test_z_report_retrieval_schema(self):
        """Test Z-Report retrieval schema"""
        retrieval_data = {
            "report_date": "2026-02-10",
            "inv_close": 5,
            "inv_count": 10,
            "inv_open": 5,
            "inv_vat": 1500.00,
            "inv_total": 10000.00,
            "inv_levy": 500.00,
            "gra_response_code": None,
            "created_at": datetime.utcnow()
        }
        schema = ZReportRetrievalSchema(**retrieval_data)
        assert schema.report_date == "2026-02-10"
        assert schema.inv_close == 5
        assert schema.inv_count == 10
    
    def test_z_report_retrieval_schema_with_gra_code(self):
        """Test Z-Report retrieval schema with GRA response code"""
        retrieval_data = {
            "report_date": "2026-02-10",
            "inv_close": 5,
            "inv_count": 10,
            "gra_response_code": "D06",
            "created_at": datetime.utcnow()
        }
        schema = ZReportRetrievalSchema(**retrieval_data)
        assert schema.gra_response_code == "D06"
    
    def test_z_report_request_schema_empty_date(self):
        """Test Z-Report request schema with empty date"""
        with pytest.raises(ValueError):
            ZReportRequestSchema(zd_date="")
    
    def test_z_report_request_schema_invalid_month(self):
        """Test Z-Report request schema with invalid month"""
        with pytest.raises(ValueError):
            ZReportRequestSchema(zd_date="2026-13-01")
    
    def test_z_report_request_schema_invalid_day(self):
        """Test Z-Report request schema with invalid day"""
        with pytest.raises(ValueError):
            ZReportRequestSchema(zd_date="2026-02-32")
    
    def test_z_report_data_schema_zero_values(self):
        """Test Z-Report data schema with zero values"""
        data = {
            "inv_close": 0,
            "inv_count": 0,
            "inv_open": 0,
            "inv_vat": 0.0,
            "inv_total": 0.0,
            "inv_levy": 0.0
        }
        schema = ZReportDataSchema(**data)
        assert schema.inv_close == 0
        assert schema.inv_count == 0
        assert schema.inv_vat == 0.0
    
    def test_z_report_data_schema_large_values(self):
        """Test Z-Report data schema with large values"""
        data = {
            "inv_close": 999999,
            "inv_count": 999999,
            "inv_open": 999999,
            "inv_vat": 999999999.99,
            "inv_total": 999999999.99,
            "inv_levy": 999999999.99
        }
        schema = ZReportDataSchema(**data)
        assert schema.inv_close == 999999
        assert schema.inv_vat == 999999999.99
    
    def test_z_report_response_schema_with_data(self):
        """Test Z-Report response schema with data"""
        response_data = {
            "submission_id": "uuid-12345",
            "report_date": "2026-02-10",
            "status": "SUCCESS",
            "data": {
                "inv_close": 5,
                "inv_count": 10,
                "inv_vat": 1500.00
            },
            "gra_response_code": None,
            "message": "Z-Report processed successfully",
            "timestamp": datetime.utcnow()
        }
        schema = ZReportResponseSchema(**response_data)
        assert schema.status == "SUCCESS"
        assert schema.data.inv_close == 5
    
    def test_z_report_retrieval_schema_partial_data(self):
        """Test Z-Report retrieval schema with partial data"""
        retrieval_data = {
            "report_date": "2026-02-10",
            "inv_close": 5,
            "inv_count": 10,
            "created_at": datetime.utcnow()
        }
        schema = ZReportRetrievalSchema(**retrieval_data)
        assert schema.inv_close == 5
        assert schema.inv_open is None
        assert schema.inv_vat is None

