"""
Erreurs de l'infrastructure.

Ces erreurs représentent des problèmes avec les systèmes externes
(base de données, APIs, réseau, etc.).
"""

from datetime import datetime
from typing import Optional, Dict, Any
from shared.errors.base import BaseError


class InfrastructureError(BaseError):
    """Erreur d'infrastructure générique."""

    pass


class DatabaseError(InfrastructureError):
    """
    Erreur lors de l'accès à la base de données.

    Levée lors de problèmes de connexion, requêtes invalides,
    ou timeouts.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur de base de données.

        Args:
            message: Description de l'erreur
            context: Contexte additionnel (ex: query, table)
            timestamp: Timestamp personnalisé (optionnel)
        """
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context=context,
        )


class RedisError(InfrastructureError):
    """
    Erreur lors de l'accès à Redis.

    Levée lors de problèmes de connexion ou d'opérations Redis.
    """

    def __init__(
        self,
        message: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur Redis.

        Args:
            message: Description de l'erreur
            operation: Opération Redis qui a échoué (get, set, delete, etc.)
            context: Contexte additionnel
            timestamp: Timestamp personnalisé (optionnel)
        """
        full_message = f"Redis operation '{operation}' failed: {message}"
        super().__init__(
            message=full_message,
            error_code="REDIS_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context={"operation": operation, **(context or {})},
        )


class ExternalAPIError(InfrastructureError):
    """
    Erreur lors de l'appel à une API externe.

    Levée quand une API tierce (OpenWeather, Google Calendar, etc.)
    retourne une erreur ou est indisponible.
    """

    def __init__(
        self,
        api_name: str,
        status_code: Optional[int] = None,
        message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur d'API externe.

        Args:
            api_name: Nom de l'API (ex: "OpenWeather", "Google Calendar")
            status_code: Code HTTP retourné (optionnel)
            message: Message d'erreur de l'API (optionnel)
            context: Contexte additionnel (ex: endpoint, params)
            timestamp: Timestamp personnalisé (optionnel)
        """
        if status_code:
            full_message = f"API '{api_name}' returned status {status_code}"
            if message:
                full_message += f": {message}"
        else:
            full_message = f"API '{api_name}' error: {message or 'Unknown error'}"

        super().__init__(
            message=full_message,
            error_code="EXTERNAL_API_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context={
                "api_name": api_name,
                "status_code": status_code,
                **(context or {}),
            },
        )


class NetworkError(InfrastructureError):
    """
    Erreur réseau générique.

    Levée lors de problèmes de connexion, timeouts,
    ou erreurs de communication réseau.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur réseau.

        Args:
            message: Description de l'erreur
            context: Contexte additionnel (ex: host, port)
            timestamp: Timestamp personnalisé (optionnel)
        """
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context=context,
        )


class ConfigurationError(InfrastructureError):
    """
    Erreur de configuration.

    Levée quand la configuration est invalide ou manquante
    (variables d'environnement, fichiers de config, etc.).
    """

    def __init__(
        self,
        field: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur de configuration.

        Args:
            field: Champ de configuration en erreur
            message: Description de l'erreur
            context: Contexte additionnel
            timestamp: Timestamp personnalisé (optionnel)
        """
        full_message = f"Configuration error for '{field}': {message}"
        super().__init__(
            message=full_message,
            error_code="CONFIGURATION_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context={"field": field, **(context or {})},
        )


class ModelLoadError(InfrastructureError):
    """
    Erreur lors du chargement d'un modèle IA.

    Levée quand un modèle (LLM, STT, TTS) ne peut pas être chargé.
    """

    def __init__(
        self,
        model_name: str,
        model_path: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur de chargement de modèle.

        Args:
            model_name: Nom du modèle (ex: "Phi-3-mini")
            model_path: Chemin du modèle
            message: Description de l'erreur
            context: Contexte additionnel
            timestamp: Timestamp personnalisé (optionnel)
        """
        full_message = f"Failed to load model '{model_name}' from '{model_path}': {message}"
        super().__init__(
            message=full_message,
            error_code="MODEL_LOAD_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context={
                "model_name": model_name,
                "model_path": model_path,
                **(context or {}),
            },
        )
