"""Simple test to debug collection issue"""
import pytest


def test_simple():
    """Simple test"""
    assert 1 + 1 == 2


class TestSimple:
    """Simple test class"""
    
    def test_method(self):
        """Test method"""
        assert True
