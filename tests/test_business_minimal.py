"""Minimal test to verify pytest works"""
import pytest


def test_simple():
    """Simple test that should always pass"""
    assert 1 + 1 == 2


class TestSimpleClass:
    """Simple test class"""
    
    def test_class_method(self):
        """Test method in class"""
        assert True
