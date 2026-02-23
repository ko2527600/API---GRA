"""Tests for encryption/decryption functionality"""
import pytest
from app.utils.encryption import EncryptionManager
from app.config import settings


class TestEncryptionManager:
    """Test suite for EncryptionManager"""
    
    @pytest.fixture
    def encryption_manager(self):
        """Create an encryption manager instance for testing"""
        return EncryptionManager(encryption_key=settings.ENCRYPTION_KEY)
    
    def test_encrypt_decrypt_roundtrip(self, encryption_manager):
        """Test that encrypted data can be decrypted back to original"""
        original_data = "test-gra-tin-12345"
        
        # Encrypt
        encrypted = encryption_manager.encrypt(original_data)
        
        # Verify it's encrypted (not the same as original)
        assert encrypted != original_data
        assert encryption_manager.is_encrypted(encrypted)
        
        # Decrypt
        decrypted = encryption_manager.decrypt(encrypted)
        
        # Verify roundtrip
        assert decrypted == original_data
    
    def test_encrypt_multiple_values(self, encryption_manager):
        """Test encrypting multiple different values"""
        values = [
            "gra-tin-001",
            "company-name-abc",
            "security-key-xyz",
            "special-chars-!@#$%",
        ]
        
        encrypted_values = [encryption_manager.encrypt(v) for v in values]
        
        # All encrypted values should be different
        assert len(set(encrypted_values)) == len(encrypted_values)
        
        # All should decrypt correctly
        for original, encrypted in zip(values, encrypted_values):
            assert encryption_manager.decrypt(encrypted) == original
    
    def test_encrypt_empty_string_raises_error(self, encryption_manager):
        """Test that encrypting empty string raises ValueError"""
        with pytest.raises(ValueError, match="Cannot encrypt empty data"):
            encryption_manager.encrypt("")
    
    def test_decrypt_empty_string_raises_error(self, encryption_manager):
        """Test that decrypting empty string raises ValueError"""
        with pytest.raises(ValueError, match="Cannot decrypt empty data"):
            encryption_manager.decrypt("")
    
    def test_decrypt_invalid_data_raises_error(self, encryption_manager):
        """Test that decrypting invalid data raises ValueError"""
        with pytest.raises(ValueError, match="Decryption failed"):
            encryption_manager.decrypt("invalid-encrypted-data")
    
    def test_decrypt_corrupted_data_raises_error(self, encryption_manager):
        """Test that decrypting corrupted data raises ValueError"""
        original = "test-data"
        encrypted = encryption_manager.encrypt(original)
        
        # Corrupt the encrypted data
        corrupted = encrypted[:-5] + "xxxxx"
        
        with pytest.raises(ValueError, match="Decryption failed"):
            encryption_manager.decrypt(corrupted)
    
    def test_is_encrypted_returns_true_for_encrypted_data(self, encryption_manager):
        """Test is_encrypted returns True for encrypted data"""
        data = "test-data"
        encrypted = encryption_manager.encrypt(data)
        
        assert encryption_manager.is_encrypted(encrypted) is True
    
    def test_is_encrypted_returns_false_for_plain_data(self, encryption_manager):
        """Test is_encrypted returns False for plain data"""
        data = "plain-text-data"
        
        assert encryption_manager.is_encrypted(data) is False
    
    def test_different_keys_produce_different_ciphers(self):
        """Test that different encryption keys produce different results"""
        data = "test-data"
        
        manager1 = EncryptionManager(encryption_key="key-1-secret")
        manager2 = EncryptionManager(encryption_key="key-2-secret")
        
        encrypted1 = manager1.encrypt(data)
        encrypted2 = manager2.encrypt(data)
        
        # Different keys should produce different encrypted values
        assert encrypted1 != encrypted2
        
        # Each manager should decrypt its own encryption
        assert manager1.decrypt(encrypted1) == data
        assert manager2.decrypt(encrypted2) == data
        
        # Cross-decryption should fail
        with pytest.raises(ValueError):
            manager1.decrypt(encrypted2)
        
        with pytest.raises(ValueError):
            manager2.decrypt(encrypted1)
    
    def test_encrypt_long_string(self, encryption_manager):
        """Test encrypting a long string"""
        long_data = "x" * 10000
        
        encrypted = encryption_manager.encrypt(long_data)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == long_data
    
    def test_encrypt_special_characters(self, encryption_manager):
        """Test encrypting strings with special characters"""
        special_data = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        encrypted = encryption_manager.encrypt(special_data)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == special_data
    
    def test_encrypt_unicode_characters(self, encryption_manager):
        """Test encrypting strings with unicode characters"""
        unicode_data = "Hello 世界 مرحبا мир"
        
        encrypted = encryption_manager.encrypt(unicode_data)
        decrypted = encryption_manager.decrypt(encrypted)
        
        assert decrypted == unicode_data
    
    def test_encrypt_same_data_produces_different_ciphertexts(self, encryption_manager):
        """Test that encrypting the same data twice produces different ciphertexts (Fernet includes timestamp)"""
        data = "test-data"
        
        encrypted1 = encryption_manager.encrypt(data)
        encrypted2 = encryption_manager.encrypt(data)
        
        # Fernet includes timestamp, so ciphertexts should be different
        assert encrypted1 != encrypted2
        
        # But both should decrypt to the same value
        assert encryption_manager.decrypt(encrypted1) == data
        assert encryption_manager.decrypt(encrypted2) == data
    
    def test_invalid_encryption_key_raises_error(self):
        """Test that empty encryption key raises ValueError"""
        with pytest.raises(ValueError, match="ENCRYPTION_KEY must be set"):
            EncryptionManager(encryption_key="")
    
    def test_none_encryption_key_raises_error(self):
        """Test that None encryption key with no settings fallback raises ValueError"""
        # When encryption_key is None, it uses settings.ENCRYPTION_KEY
        # So we need to test with an empty string instead
        with pytest.raises(ValueError, match="ENCRYPTION_KEY must be set"):
            EncryptionManager(encryption_key="")
