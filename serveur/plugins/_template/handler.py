"""
Template pour créer un nouveau plugin.

Copiez ce dossier et adaptez-le à vos besoins.
"""

from typing import Dict, Any

from core.domain.interfaces import PluginInterface


class ExamplePlugin(PluginInterface):
    """
    Plugin d'exemple.

    Remplacez cette classe par votre implémentation.
    """

    def __init__(self):
        """Initialise le plugin."""
        # Charger la configuration si nécessaire
        pass

    async def execute(self, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Exécute une action du plugin.

        Args:
            intent: Nom de l'intent à exécuter
            params: Paramètres extraits par l'IA

        Returns:
            Résultat de l'action

        Raises:
            PluginExecutionError: Si l'exécution échoue
        """
        if intent == "example_action":
            # Implémenter la logique ici
            return {
                "success": True,
                "message": "Action executed successfully",
                "data": params,
            }

        return {
            "success": False,
            "error": f"Unknown intent: {intent}",
        }

    def get_prompt_context(self) -> str:
        """
        Retourne le contexte à injecter dans le prompt LLM.

        Returns:
            Description des capacités du plugin
        """
        return """Tu as accès à la fonction 'example_action'.

Paramètres:
- param1 (requis): description
- param2 (optionnel): description

Retourne: description du résultat

Exemple d'utilisation:
User: "Exécute l'exemple avec param1"
Assistant: Je vais utiliser example_action avec param1="value"
"""

    def get_manifest(self) -> Dict[str, Any]:
        """
        Retourne le manifest du plugin.

        Returns:
            Manifest chargé depuis plugin.json
        """
        return {
            "name": "example",
            "version": "1.0.0",
            "description": "Example plugin template",
            "triggers": ["example", "test"],
            "intents": ["example_action"],
            "enabled": False,
        }

    async def on_load(self) -> None:
        """
        Hook appelé lors du chargement du plugin.

        Utilisé pour initialiser des ressources (connexions, caches, etc.).
        """
        # Exemple: initialiser une connexion API
        pass

    async def on_unload(self) -> None:
        """
        Hook appelé lors du déchargement du plugin.

        Utilisé pour libérer des ressources.
        """
        # Exemple: fermer les connexions
        pass

    async def health_check(self) -> bool:
        """
        Vérifie que le plugin est opérationnel.

        Returns:
            True si le plugin fonctionne correctement
        """
        # Exemple: tester la connexion à une API externe
        return True
