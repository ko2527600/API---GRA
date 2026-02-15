"""Secrets management configuration"""
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import Optional, Literal
from enum import Enum


class SecretsBackend(str, Enum):
    """Supported secrets backends"""
    LOCAL = "local"  # Local encrypted storage (default)
    VAULT = "vault"  # HashiCorp Vault
    AWS_SECRETS = "aws_secrets"  # AWS Secrets Manager
    AZURE_KEYVAULT = "azure_keyvault"  # Azure Key Vault


class SecretsConfig(BaseSettings):
    """Secrets management configuration"""
    
    # Backend selection
    SECRETS_BACKEND: SecretsBackend = Field(
        default=SecretsBackend.LOCAL,
        description="Secrets backend: local, vault, aws_secrets, azure_keyvault"
    )
    
    # Local backend settings
    SECRETS_ENCRYPTION_KEY: str = Field(
        default="your-encryption-key-change-in-production",
        description="Encryption key for local secrets storage"
    )
    SECRETS_KEY_ROTATION_ENABLED: bool = Field(
        default=False,
        description="Enable automatic key rotation"
    )
    SECRETS_KEY_ROTATION_DAYS: int = Field(
        default=90,
        description="Days between key rotations"
    )
    
    # HashiCorp Vault settings
    VAULT_ADDR: Optional[str] = Field(
        default=None,
        description="HashiCorp Vault server address (e.g., https://vault.example.com:8200)"
    )
    VAULT_TOKEN: Optional[str] = Field(
        default=None,
        description="Vault authentication token"
    )
    VAULT_NAMESPACE: Optional[str] = Field(
        default=None,
        description="Vault namespace (Enterprise only)"
    )
    VAULT_ENGINE_PATH: str = Field(
        default="secret",
        description="Vault KV engine path"
    )
    VAULT_SECRET_PATH: str = Field(
        default="gra-credentials",
        description="Path to store GRA credentials in Vault"
    )
    VAULT_SKIP_VERIFY: bool = Field(
        default=False,
        description="Skip SSL verification for Vault (development only)"
    )
    
    # AWS Secrets Manager settings
    AWS_REGION: Optional[str] = Field(
        default=None,
        description="AWS region for Secrets Manager"
    )
    AWS_SECRET_NAME_PREFIX: str = Field(
        default="gra-api",
        description="Prefix for secret names in AWS Secrets Manager"
    )
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="AWS access key ID"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="AWS secret access key"
    )
    
    # Azure Key Vault settings
    AZURE_VAULT_URL: Optional[str] = Field(
        default=None,
        description="Azure Key Vault URL (e.g., https://myvault.vault.azure.net/)"
    )
    AZURE_TENANT_ID: Optional[str] = Field(
        default=None,
        description="Azure tenant ID"
    )
    AZURE_CLIENT_ID: Optional[str] = Field(
        default=None,
        description="Azure client ID"
    )
    AZURE_CLIENT_SECRET: Optional[str] = Field(
        default=None,
        description="Azure client secret"
    )
    
    # Audit and compliance
    SECRETS_AUDIT_ENABLED: bool = Field(
        default=True,
        description="Enable audit logging for secrets access"
    )
    SECRETS_AUDIT_LOG_RETENTION_DAYS: int = Field(
        default=2555,
        description="Audit log retention in days (7 years)"
    )
    
    # Credential rotation
    SECRETS_CREDENTIAL_ROTATION_ENABLED: bool = Field(
        default=False,
        description="Enable automatic credential rotation"
    )
    SECRETS_CREDENTIAL_ROTATION_DAYS: int = Field(
        default=180,
        description="Days between credential rotations"
    )
    
    # Revocation
    SECRETS_REVOCATION_ENABLED: bool = Field(
        default=True,
        description="Enable credential revocation"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"
    
    @validator("SECRETS_BACKEND")
    def validate_backend(cls, v):
        """Validate secrets backend"""
        if isinstance(v, str):
            try:
                return SecretsBackend(v)
            except ValueError:
                raise ValueError(f"Invalid secrets backend: {v}")
        return v
    
    def is_local_backend(self) -> bool:
        """Check if using local backend"""
        return self.SECRETS_BACKEND == SecretsBackend.LOCAL
    
    def is_vault_backend(self) -> bool:
        """Check if using Vault backend"""
        return self.SECRETS_BACKEND == SecretsBackend.VAULT
    
    def is_aws_backend(self) -> bool:
        """Check if using AWS Secrets Manager backend"""
        return self.SECRETS_BACKEND == SecretsBackend.AWS_SECRETS
    
    def is_azure_backend(self) -> bool:
        """Check if using Azure Key Vault backend"""
        return self.SECRETS_BACKEND == SecretsBackend.AZURE_KEYVAULT


# Create secrets config instance
secrets_config = SecretsConfig()
