"""
Interface pour les plugins Hive Mind.

Tous les plugins doivent implémenter cette interface
pour être chargés dynamiquement par le système.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class PluginInterface(ABC):
    """
    Interface abstraite pour tous les plugins Hive Mind.

    Les plugins permettent d'étendre les fonctionnalités du système
    en ajoutant des intégrations tierces (météo, calendar, etc.).
    """

    @abstractmethod
    async def execute(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une action du plugin.

        Args:
            intent: Nom de l'intent à exécuter (ex: "get_weather", "add_event")
            params: Paramètres extraits par l'IA pour cette action

        Returns:
            Résultat de l'action sous forme de dictionnaire
            Doit contenir au minimum:
            - "success": bool indiquant si l'action a réussi
            - En cas de succès: données de résultat
            - En cas d'échec: "error": str avec message d'erreur

        Raises:
            PluginExecutionError: Si l'exécution échoue de manière inattendue

        Examples:
            >>> result = await plugin.execute("get_weather", {"location": "Belfort"})
            >>> print(result)
            {
                "success": True,
                "temperature": 8.5,
                "description": "nuageux",
                "location": "Belfort"
            }
        """
        pass

    @abstractmethod
    def get_prompt_context(self) -> str:
        """
        Retourne le contexte à injecter dans le prompt LLM.

        Cette description explique au LLM quelles sont les capacités
        du plugin et comment l'utiliser.

        Returns:
            Description textuelle des capacités du plugin

        Examples:
            >>> context = plugin.get_prompt_context()
            >>> print(context)
            "Tu as accès à la fonction 'get_weather' pour obtenir la météo.
            Paramètres:
            - location (optionnel): ville, défaut = Belfort, FR
            Retourne: température, description, humidité"
        """
        pass

    @abstractmethod
    def get_manifest(self) -> Dict[str, Any]:
        """
        Retourne le manifest du plugin.

        Le manifest contient les métadonnées du plugin:
        - name: nom unique du plugin
        - version: version sémantique
        - description: description courte
        - triggers: mots-clés qui déclenchent le plugin
        - intents: liste des intents supportés
        - enabled: si le plugin est activé

        Returns:
            Dictionnaire contenant le manifest

        Examples:
            >>> manifest = plugin.get_manifest()
            >>> print(manifest)
            {
                "name": "weather",
                "version": "1.0.0",
                "description": "Récupère les informations météorologiques",
                "triggers": ["météo", "weather", "température"],
                "intents": ["get_weather", "get_forecast"],
                "enabled": True
            }
        """
        pass

    async def on_load(self) -> None:
        """
        Hook appelé lors du chargement du plugin.

        Utilisé pour initialiser des ressources (connexions, caches, etc.).
        Par défaut ne fait rien, peut être surchargé par les plugins.
        """
        pass

    async def on_unload(self) -> None:
        """
        Hook appelé lors du déchargement du plugin.

        Utilisé pour libérer des ressources (fermer connexions, etc.).
        Par défaut ne fait rien, peut être surchargé par les plugins.
        """
        pass

    async def health_check(self) -> bool:
        """
        Vérifie que le plugin est opérationnel.

        Returns:
            True si le plugin fonctionne correctement, False sinon

        Examples:
            >>> is_healthy = await plugin.health_check()
            >>> if not is_healthy:
            ...     print("Plugin indisponible")
        """
        return True
