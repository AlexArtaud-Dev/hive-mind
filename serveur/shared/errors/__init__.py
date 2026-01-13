"""
Système d'erreurs personnalisées pour Hive Mind.

Ce module fournit une hiérarchie d'erreurs structurée selon
les principes Clean Architecture:
- BaseError: Erreur de base avec sérialisation JSON
- DomainError: Erreurs métier
- InfrastructureError: Erreurs systèmes externes

Usage:
    from shared.errors import ValidationError, ExternalAPIError

    # Lever une erreur de validation
    raise ValidationError(field="email", message="Email invalide")

    # Lever une erreur d'API externe
    raise ExternalAPIError(
        api_name="OpenWeather",
        status_code=503,
        message="Service temporarily unavailable"
    )
"""

# Base errors
from shared.errors.base import BaseError

# Domain errors
from shared.errors.domain import (
    DomainError,
    ValidationError,
    AudioProcessingError,
    LLMError,
    PluginExecutionError,
    ContextError,
)

# Infrastructure errors
from shared.errors.infrastructure import (
    InfrastructureError,
    DatabaseError,
    RedisError,
    ExternalAPIError,
    NetworkError,
    ConfigurationError,
    ModelLoadError,
)

__all__ = [
    # Base
    "BaseError",
    # Domain
    "DomainError",
    "ValidationError",
    "AudioProcessingError",
    "LLMError",
    "PluginExecutionError",
    "ContextError",
    # Infrastructure
    "InfrastructureError",
    "DatabaseError",
    "RedisError",
    "ExternalAPIError",
    "NetworkError",
    "ConfigurationError",
    "ModelLoadError",
]
