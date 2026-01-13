"""
Erreurs de base pour Hive Mind.

Définit la hiérarchie d'erreurs selon les principes Clean Architecture.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class BaseError(Exception):
    """
    Erreur de base pour toutes les erreurs Hive Mind.

    Toutes les erreurs personnalisées doivent hériter de cette classe.
    Fournit une structure commune pour le logging et le debugging.

    Attributes:
        message: Message d'erreur lisible
        error_code: Code d'erreur unique pour identification
        timestamp: Timestamp de l'erreur
        context: Contexte additionnel (optionnel)
    """

    message: str
    error_code: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        """Retourne une représentation string de l'erreur."""
        return f"[{self.error_code}] {self.message}"

    def __post_init__(self) -> None:
        """Initialise l'exception après création du dataclass."""
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Sérialise l'erreur en dictionnaire pour logging.

        Returns:
            Dict contenant toutes les informations de l'erreur

        Examples:
            >>> error = BaseError("Test error", "TEST_ERROR")
            >>> error.to_dict()
            {
                'error_code': 'TEST_ERROR',
                'message': 'Test error',
                'timestamp': '2026-01-13T12:00:00.000000Z',
                'context': {}
            }
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context or {},
            "error_type": self.__class__.__name__,
        }
