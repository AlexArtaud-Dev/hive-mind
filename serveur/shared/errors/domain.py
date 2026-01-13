"""
Erreurs du domaine métier.

Ces erreurs représentent des violations de règles métier
ou des états invalides dans le domaine.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from shared.errors.base import BaseError


class DomainError(BaseError):
    """Erreur métier générique."""

    pass


class ValidationError(DomainError):
    """
    Erreur de validation des données.

    Levée quand des données ne respectent pas les contraintes métier.
    """

    def __init__(
        self,
        field: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur de validation.

        Args:
            field: Nom du champ en erreur
            message: Description de l'erreur de validation
            context: Contexte additionnel (optionnel)
            timestamp: Timestamp personnalisé (optionnel)
        """
        full_message = f"Validation failed for '{field}': {message}"
        super().__init__(
            message=full_message,
            error_code="VALIDATION_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context={"field": field, **(context or {})},
        )


class AudioProcessingError(DomainError):
    """
    Erreur lors du traitement audio.

    Levée quand l'audio est corrompu, invalide ou non processable.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur de traitement audio.

        Args:
            message: Description de l'erreur
            context: Contexte additionnel (ex: format, taille)
            timestamp: Timestamp personnalisé (optionnel)
        """
        super().__init__(
            message=message,
            error_code="AUDIO_PROCESSING_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context=context,
        )


class LLMError(DomainError):
    """
    Erreur lors de l'utilisation du LLM.

    Levée quand le LLM ne peut pas générer de réponse valide
    ou rencontre une erreur interne.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur LLM.

        Args:
            message: Description de l'erreur
            context: Contexte additionnel (ex: prompt, modèle)
            timestamp: Timestamp personnalisé (optionnel)
        """
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context=context,
        )


class PluginExecutionError(DomainError):
    """
    Erreur lors de l'exécution d'un plugin.

    Levée quand un plugin échoue à exécuter son action.
    """

    def __init__(
        self,
        plugin_name: str,
        intent: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur d'exécution de plugin.

        Args:
            plugin_name: Nom du plugin en erreur
            intent: Intent qui a échoué
            message: Description de l'erreur
            context: Contexte additionnel
            timestamp: Timestamp personnalisé (optionnel)
        """
        full_message = f"Plugin '{plugin_name}' failed to execute intent '{intent}': {message}"
        super().__init__(
            message=full_message,
            error_code="PLUGIN_EXECUTION_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context={"plugin": plugin_name, "intent": intent, **(context or {})},
        )


class ContextError(DomainError):
    """
    Erreur lors de la gestion du contexte conversationnel.

    Levée quand le contexte ne peut pas être chargé, sauvegardé
    ou est corrompu.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialise une erreur de contexte.

        Args:
            message: Description de l'erreur
            context: Contexte additionnel
            timestamp: Timestamp personnalisé (optionnel)
        """
        super().__init__(
            message=message,
            error_code="CONTEXT_ERROR",
            timestamp=timestamp or datetime.utcnow(),
            context=context,
        )
