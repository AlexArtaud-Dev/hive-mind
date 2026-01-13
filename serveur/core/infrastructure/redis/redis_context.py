"""
Implémentation Redis pour le Context Manager.

Gère le stockage et la récupération du contexte conversationnel
partagé entre tous les clients via Redis.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

import redis.asyncio as redis

from core.domain.interfaces import ContextInterface, Message
from shared.errors import ContextError, RedisError
from config import settings


class RedisContext(ContextInterface):
    """
    Implémentation Redis pour la gestion du contexte conversationnel.

    Utilise une liste Redis pour stocker les messages avec TTL automatique.
    Tous les clients partagent le même contexte conversationnel.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        key_prefix: str = "hivemind:context",
    ):
        """
        Initialise le context manager Redis.

        Args:
            redis_url: URL de connexion Redis (défaut: depuis config)
            ttl_seconds: TTL des messages en secondes (défaut: depuis config)
            key_prefix: Préfixe pour les clés Redis

        Raises:
            RedisError: Si la connexion Redis échoue
        """
        self._redis_url = redis_url or settings.redis_url
        self._ttl_seconds = ttl_seconds or settings.redis_ttl_seconds
        self._key_prefix = key_prefix
        self._messages_key = f"{key_prefix}:messages"

        # Connexion Redis (lazy, créée au premier appel)
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        """
        Récupère ou crée la connexion Redis.

        Returns:
            Instance Redis connectée

        Raises:
            RedisError: Si la connexion échoue
        """
        if self._redis is None:
            try:
                self._redis = await redis.from_url(
                    self._redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test de la connexion
                await self._redis.ping()

            except Exception as e:
                raise RedisError(
                    message=f"Failed to connect to Redis: {str(e)}",
                    operation="connect",
                    context={"redis_url": self._redis_url},
                    timestamp=datetime.utcnow(),
                )

        return self._redis

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
        try:
            r = await self._get_redis()

            # Créer le message
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                client_id=client_id,
                metadata=metadata,
            )

            # Sérialiser en JSON
            message_json = json.dumps(message.to_dict())

            # Ajouter à la liste Redis (RPUSH = append à droite)
            await r.rpush(self._messages_key, message_json)

            # Définir le TTL sur la clé (renouvelle à chaque ajout)
            await r.expire(self._messages_key, self._ttl_seconds)

        except RedisError:
            raise
        except Exception as e:
            raise ContextError(
                message=f"Failed to add message: {str(e)}",
                context={
                    "role": role,
                    "content_length": len(content),
                    "error_type": type(e).__name__,
                },
                timestamp=datetime.utcnow(),
            )

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
        try:
            r = await self._get_redis()

            # Récupérer tous les messages (LRANGE 0 -1 = toute la liste)
            messages_json = await r.lrange(self._messages_key, 0, -1)

            # Désérialiser les messages
            messages = []
            for msg_json in messages_json:
                try:
                    msg_dict = json.loads(msg_json)
                    message = Message.from_dict(msg_dict)

                    # Filtrer par date si spécifié
                    if since and message.timestamp < since:
                        continue

                    messages.append(message)
                except Exception as e:
                    # Log l'erreur mais continue (message corrompu)
                    print(f"Warning: Failed to parse message: {e}")
                    continue

            # Appliquer la limite (prendre les N derniers messages)
            if limit and limit > 0:
                messages = messages[-limit:]

            return messages

        except RedisError:
            raise
        except Exception as e:
            raise ContextError(
                message=f"Failed to get messages: {str(e)}",
                context={
                    "limit": limit,
                    "error_type": type(e).__name__,
                },
                timestamp=datetime.utcnow(),
            )

    async def clear_context(self) -> None:
        """
        Efface tout le contexte conversationnel.

        Utile pour réinitialiser la conversation ou pour maintenance.

        Raises:
            ContextError: Si l'effacement échoue
        """
        try:
            r = await self._get_redis()
            await r.delete(self._messages_key)

        except RedisError:
            raise
        except Exception as e:
            raise ContextError(
                message=f"Failed to clear context: {str(e)}",
                context={"error_type": type(e).__name__},
                timestamp=datetime.utcnow(),
            )

    async def get_context_size(self) -> int:
        """
        Retourne le nombre de messages dans le contexte.

        Returns:
            Nombre de messages stockés

        Raises:
            ContextError: Si la requête échoue
        """
        try:
            r = await self._get_redis()
            size = await r.llen(self._messages_key)
            return size

        except RedisError:
            raise
        except Exception as e:
            raise ContextError(
                message=f"Failed to get context size: {str(e)}",
                context={"error_type": type(e).__name__},
                timestamp=datetime.utcnow(),
            )

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
        try:
            r = await self._get_redis()

            # Récupérer tous les messages
            messages = await self.get_messages()

            # Filtrer les messages à conserver
            messages_to_keep = [
                msg for msg in messages if msg.timestamp >= before
            ]

            # Reconstruire la liste
            await r.delete(self._messages_key)

            if messages_to_keep:
                messages_json = [
                    json.dumps(msg.to_dict()) for msg in messages_to_keep
                ]
                await r.rpush(self._messages_key, *messages_json)
                await r.expire(self._messages_key, self._ttl_seconds)

            deleted_count = len(messages) - len(messages_to_keep)
            return deleted_count

        except (RedisError, ContextError):
            raise
        except Exception as e:
            raise ContextError(
                message=f"Failed to prune old messages: {str(e)}",
                context={
                    "before": before.isoformat(),
                    "error_type": type(e).__name__,
                },
                timestamp=datetime.utcnow(),
            )

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
        try:
            messages = await self.get_messages(limit=limit)

            # Construire le prompt
            lines = []

            # Ajouter le system prompt si fourni
            if system_prompt:
                lines.append(f"<|system|>\n{system_prompt}<|end|>")

            # Ajouter les messages
            for msg in messages:
                if msg.role == "user":
                    lines.append(f"<|user|>\n{msg.content}<|end|>")
                elif msg.role == "assistant":
                    lines.append(f"<|assistant|>\n{msg.content}<|end|>")
                elif msg.role == "system":
                    lines.append(f"<|system|>\n{msg.content}<|end|>")

            # Ajouter le tag d'assistant pour déclencher la génération
            lines.append("<|assistant|>")

            return "\n".join(lines)

        except (RedisError, ContextError):
            raise
        except Exception as e:
            raise ContextError(
                message=f"Failed to format context for LLM: {str(e)}",
                context={
                    "limit": limit,
                    "error_type": type(e).__name__,
                },
                timestamp=datetime.utcnow(),
            )

    async def close(self) -> None:
        """
        Ferme la connexion Redis.

        À appeler lors de l'arrêt du serveur.
        """
        if self._redis:
            await self._redis.close()
            self._redis = None
