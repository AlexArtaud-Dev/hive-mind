"""
Interface pour les modèles de langage (LLM).

Abstraction selon le principe Dependency Inversion.
Les services dépendent de cette interface, pas d'implémentations concrètes.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """
    Réponse d'un modèle LLM.

    Attributes:
        content: Contenu de la réponse générée
        tokens_used: Nombre de tokens utilisés
        metadata: Métadonnées additionnelles (temps de génération, etc.)
    """

    content: str
    tokens_used: int
    metadata: Optional[Dict[str, Any]] = None


class LLMInterface(ABC):
    """
    Interface abstraite pour les modèles de langage.

    Toutes les implémentations LLM (Phi-3, Llama, etc.) doivent
    implémenter cette interface.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[list[str]] = None,
    ) -> LLMResponse:
        """
        Génère une réponse complète à partir d'un prompt.

        Args:
            prompt: Prompt à envoyer au modèle
            max_tokens: Nombre maximum de tokens à générer
            temperature: Température de génération (0.0-2.0)
            stop_sequences: Séquences pour arrêter la génération

        Returns:
            LLMResponse contenant la réponse générée et métadonnées

        Raises:
            LLMError: Si la génération échoue
        """
        pass

    @abstractmethod
    async def generate_streaming(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[list[str]] = None,
    ) -> AsyncIterator[str]:
        """
        Génère une réponse en streaming (chunk par chunk).

        Args:
            prompt: Prompt à envoyer au modèle
            max_tokens: Nombre maximum de tokens à générer
            temperature: Température de génération (0.0-2.0)
            stop_sequences: Séquences pour arrêter la génération

        Yields:
            Chunks de texte au fur et à mesure de la génération

        Raises:
            LLMError: Si la génération échoue
        """
        pass

    @abstractmethod
    async def is_loaded(self) -> bool:
        """
        Vérifie si le modèle est chargé et prêt.

        Returns:
            True si le modèle est prêt à générer
        """
        pass

    @abstractmethod
    async def unload(self) -> None:
        """
        Décharge le modèle de la mémoire.

        Utile pour libérer les ressources quand le modèle n'est plus utilisé.
        """
        pass

    @abstractmethod
    def get_context_size(self) -> int:
        """
        Retourne la taille de la fenêtre de contexte du modèle.

        Returns:
            Nombre de tokens de contexte disponibles
        """
        pass
