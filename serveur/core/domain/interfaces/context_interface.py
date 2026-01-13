"""
Interface pour la gestion du contexte conversationnel.

Abstraction pour le stockage et la récupération du contexte
partagé entre tous les clients.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """
    Message dans le contexte conversationnel.

    Attributes:
        role: Rôle du message ("user", "assistant", "system")
        content: Contenu du message
        timestamp: Timestamp du message
        client_id: ID du client source (optionnel)
        metadata: Métadonnées additionnelles (optionnel)
    """

    role: str
    content: str
    timestamp: datetime
    client_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le message en dictionnaire."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "client_id": self.client_id,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Désérialise un message depuis un dictionnaire."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            client_id=data.get("client_id"),
            metadata=data.get("metadata"),
        )


class ContextInterface(ABC):
    """
    Interface abstraite pour la gestion du contexte conversationnel.

    Permet de stocker et récupérer l'historique des conversations
    partagé entre tous les clients.
    """

    @abstractmethod
    async def add_message(
        self,
        role: str,
        content: str,
        client_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Ajoute un message au contexte conversationnel.

        Args:
            role: Rôle du message ("user", "assistant", "system")
            content: Contenu du message
            client_id: ID du client source (optionnel)
            metadata: Métadonnées additionnelles (optionnel)

        Raises:
            ContextError: Si l'ajout échoue
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
    ) -> List[Message]:
        """
        Récupère les messages du contexte conversationnel.

        Args:
            limit: Nombre maximum de messages à récupérer (du plus récent au plus ancien)
            since: Ne récupérer que les messages après cette date

        Returns:
            Liste de messages triés par timestamp (du plus ancien au plus récent)

        Raises:
            ContextError: Si la récupération échoue
        """
        pass

    @abstractmethod
    async def clear_context(self) -> None:
        """
        Efface tout le contexte conversationnel.

        Utile pour réinitialiser la conversation ou pour maintenance.

        Raises:
            ContextError: Si l'effacement échoue
        """
        pass

    @abstractmethod
    async def get_context_size(self) -> int:
        """
        Retourne le nombre de messages dans le contexte.

        Returns:
            Nombre de messages stockés

        Raises:
            ContextError: Si la requête échoue
        """
        pass

    @abstractmethod
    async def prune_old_messages(self, before: datetime) -> int:
        """
        Supprime les messages plus anciens qu'une date donnée.

        Args:
            before: Date limite (messages avant cette date seront supprimés)

        Returns:
            Nombre de messages supprimés

        Raises:
            ContextError: Si la suppression échoue
        """
        pass

    @abstractmethod
    async def format_for_llm(
        self,
        limit: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Formate le contexte pour le LLM.

        Args:
            limit: Nombre maximum de messages à inclure
            system_prompt: Prompt système à ajouter en début (optionnel)

        Returns:
            Contexte formaté prêt pour le LLM

        Raises:
            ContextError: Si le formatage échoue
        """
        pass
