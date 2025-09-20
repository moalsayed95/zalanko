"""
Custom exceptions for Zalanko backend.
Provides structured error handling across the application.
"""


class ZalankoError(Exception):
    """Base exception for all Zalanko-specific errors."""
    pass


class ConfigurationError(ZalankoError):
    """Raised when there's a configuration issue."""
    pass


class SearchError(ZalankoError):
    """Raised when search operations fail."""
    pass


class VirtualTryOnError(ZalankoError):
    """Raised when virtual try-on operations fail."""
    pass


class ImageProcessingError(ZalankoError):
    """Raised when image processing fails."""
    pass


class ExternalServiceError(ZalankoError):
    """Raised when external service calls fail."""
    pass


# Export all exceptions
__all__ = [
    "ZalankoError",
    "ConfigurationError",
    "SearchError",
    "VirtualTryOnError",
    "ImageProcessingError",
    "ExternalServiceError"
]