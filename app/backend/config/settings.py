"""
Configuration management for Zalanko backend.
Centralizes all environment variables and provides validation.
"""

import os
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """Application settings with validation and defaults."""

    def __init__(self):
        # Load environment variables
        if not os.environ.get("RUNNING_IN_PRODUCTION"):
            load_dotenv(override=True)

        self._validate_required_settings()

    # Azure OpenAI Settings
    @property
    def azure_openai_endpoint(self) -> str:
        return self._get_required("AZURE_OPENAI_ENDPOINT")

    @property
    def azure_openai_api_key(self) -> Optional[str]:
        return os.environ.get("AZURE_OPENAI_API_KEY")

    @property
    def azure_openai_realtime_deployment(self) -> str:
        return self._get_required("AZURE_OPENAI_REALTIME_DEPLOYMENT")

    @property
    def azure_openai_embedding_model(self) -> str:
        return os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

    @property
    def azure_openai_api_version(self) -> str:
        return os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    @property
    def azure_openai_voice_choice(self) -> str:
        return os.environ.get("AZURE_OPENAI_REALTIME_VOICE_CHOICE", "alloy")

    # Azure Search Settings
    @property
    def azure_search_service_name(self) -> str:
        return self._get_required("AZURE_SEARCH_SERVICE_NAME")

    @property
    def azure_search_api_key(self) -> Optional[str]:
        return os.environ.get("AZURE_SEARCH_API_KEY")

    @property
    def azure_search_index(self) -> str:
        return os.environ.get("AZURE_SEARCH_INDEX", "fashion-products")

    # Azure Storage Settings
    @property
    def azure_storage_account_name(self) -> str:
        return os.environ.get("AZURE_STORAGE_ACCOUNT_NAME", "zalankoimages")

    @property
    def azure_storage_container_name(self) -> str:
        return os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "product-images")

    @property
    def azure_storage_connection_string(self) -> Optional[str]:
        return os.environ.get("AZURE_STORAGE_CONNECTION_STRING")

    # Google Cloud Settings
    @property
    def google_cloud_api_key(self) -> Optional[str]:
        return os.environ.get("GOOGLE_CLOUD_API_KEY")

    @property
    def google_cloud_project_id(self) -> Optional[str]:
        return os.environ.get("GOOGLE_CLOUD_PROJECT_ID")

    # Application Settings
    @property
    def azure_tenant_id(self) -> Optional[str]:
        return os.environ.get("AZURE_TENANT_ID")

    @property
    def is_production(self) -> bool:
        return bool(os.environ.get("RUNNING_IN_PRODUCTION"))

    @property
    def log_level(self) -> str:
        return os.environ.get("LOG_LEVEL", "INFO")

    @property
    def max_request_size_mb(self) -> int:
        return int(os.environ.get("MAX_REQUEST_SIZE_MB", "50"))

    def _get_required(self, key: str) -> str:
        """Get required environment variable or raise error."""
        value = os.environ.get(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def _validate_required_settings(self) -> None:
        """Validate that all required settings are present."""
        required_settings = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_REALTIME_DEPLOYMENT",
            "AZURE_SEARCH_SERVICE_NAME"
        ]

        missing = []
        for setting in required_settings:
            if not os.environ.get(setting):
                missing.append(setting)

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


# Global settings instance
settings = Settings()