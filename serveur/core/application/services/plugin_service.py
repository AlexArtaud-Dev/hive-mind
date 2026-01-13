"""
Service de gestion des plugins.

Gère le chargement, l'exécution et le cycle de vie des plugins.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import importlib.util
import json
from datetime import datetime

from core.domain.interfaces import PluginInterface
from shared.errors import PluginExecutionError, ConfigurationError


class PluginLoader:
    """
    Charge et gère les plugins dynamiquement.

    Scanne le dossier plugins/ et charge les plugins qui respectent
    la convention (plugin.json + handler.py).
    """

    def __init__(self, plugins_dir: Path):
        """
        Initialise le plugin loader.

        Args:
            plugins_dir: Chemin vers le dossier contenant les plugins
        """
        self.plugins_dir = plugins_dir
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.plugin_manifests: Dict[str, Dict[str, Any]] = {}

    def _load_manifest(self, plugin_path: Path) -> Dict[str, Any]:
        """
        Charge le manifest d'un plugin.

        Args:
            plugin_path: Chemin du dossier du plugin

        Returns:
            Dictionnaire contenant le manifest

        Raises:
            ConfigurationError: Si le manifest est invalide
        """
        manifest_path = plugin_path / "plugin.json"

        if not manifest_path.exists():
            raise ConfigurationError(
                field="plugin.json",
                message=f"Manifest not found for plugin at {plugin_path}",
                timestamp=datetime.utcnow(),
            )

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Valider les champs requis
            required_fields = ["name", "version", "description", "intents"]
            for field in required_fields:
                if field not in manifest:
                    raise ConfigurationError(
                        field=field,
                        message=f"Missing required field '{field}' in {manifest_path}",
                        timestamp=datetime.utcnow(),
                    )

            return manifest

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                field="plugin.json",
                message=f"Invalid JSON in {manifest_path}: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    def _load_plugin_module(
        self, plugin_path: Path, plugin_name: str
    ) -> PluginInterface:
        """
        Charge le module Python d'un plugin.

        Args:
            plugin_path: Chemin du dossier du plugin
            plugin_name: Nom du plugin

        Returns:
            Instance du plugin

        Raises:
            ConfigurationError: Si le module ne peut pas être chargé
        """
        handler_path = plugin_path / "handler.py"

        if not handler_path.exists():
            raise ConfigurationError(
                field="handler.py",
                message=f"Handler not found for plugin {plugin_name}",
                timestamp=datetime.utcnow(),
            )

        try:
            # Import dynamique du module
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}.handler", handler_path
            )
            if spec is None or spec.loader is None:
                raise ConfigurationError(
                    field="handler.py",
                    message=f"Failed to load spec for {handler_path}",
                    timestamp=datetime.utcnow(),
                )

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Trouver la classe du plugin (doit se terminer par "Plugin")
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PluginInterface)
                    and attr is not PluginInterface
                ):
                    plugin_class = attr
                    break

            if plugin_class is None:
                raise ConfigurationError(
                    field="handler.py",
                    message=f"No PluginInterface subclass found in {handler_path}",
                    timestamp=datetime.utcnow(),
                )

            # Instancier le plugin
            return plugin_class()

        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                field="handler.py",
                message=f"Failed to load plugin {plugin_name}: {str(e)}",
                context={"error_type": type(e).__name__},
                timestamp=datetime.utcnow(),
            )

    async def load_plugin(self, plugin_name: str) -> None:
        """
        Charge un plugin spécifique.

        Args:
            plugin_name: Nom du plugin à charger

        Raises:
            ConfigurationError: Si le plugin ne peut pas être chargé
        """
        plugin_path = self.plugins_dir / plugin_name

        if not plugin_path.is_dir():
            raise ConfigurationError(
                field="plugin_directory",
                message=f"Plugin directory not found: {plugin_path}",
                timestamp=datetime.utcnow(),
            )

        # Charger le manifest
        manifest = self._load_manifest(plugin_path)

        # Vérifier si le plugin est activé
        if not manifest.get("enabled", True):
            return

        # Charger le module
        plugin = self._load_plugin_module(plugin_path, plugin_name)

        # Appeler le hook on_load
        await plugin.on_load()

        # Stocker le plugin et son manifest
        self.loaded_plugins[plugin_name] = plugin
        self.plugin_manifests[plugin_name] = manifest

    async def load_all_plugins(self) -> None:
        """
        Charge tous les plugins du dossier plugins/.

        Ignore les dossiers commençant par _ (comme _template).
        """
        if not self.plugins_dir.exists():
            return

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Ignorer les dossiers spéciaux
            if plugin_dir.name.startswith("_"):
                continue

            try:
                await self.load_plugin(plugin_dir.name)
            except ConfigurationError as e:
                # Log l'erreur mais continue le chargement des autres plugins
                print(f"Warning: Failed to load plugin {plugin_dir.name}: {e.message}")

    async def unload_plugin(self, plugin_name: str) -> None:
        """
        Décharge un plugin.

        Args:
            plugin_name: Nom du plugin à décharger
        """
        if plugin_name in self.loaded_plugins:
            plugin = self.loaded_plugins[plugin_name]
            await plugin.on_unload()
            del self.loaded_plugins[plugin_name]
            del self.plugin_manifests[plugin_name]

    async def unload_all_plugins(self) -> None:
        """Décharge tous les plugins."""
        plugin_names = list(self.loaded_plugins.keys())
        for plugin_name in plugin_names:
            await self.unload_plugin(plugin_name)

    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        Récupère un plugin chargé.

        Args:
            plugin_name: Nom du plugin

        Returns:
            Instance du plugin ou None si non trouvé
        """
        return self.loaded_plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """
        Récupère tous les plugins chargés.

        Returns:
            Dictionnaire {nom: instance}
        """
        return self.loaded_plugins.copy()

    def get_plugin_manifest(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le manifest d'un plugin.

        Args:
            plugin_name: Nom du plugin

        Returns:
            Manifest du plugin ou None si non trouvé
        """
        return self.plugin_manifests.get(plugin_name)

    def get_all_plugin_contexts(self) -> str:
        """
        Récupère les contextes de tous les plugins pour le LLM.

        Returns:
            Contexte combiné de tous les plugins
        """
        contexts = []
        for plugin_name, plugin in self.loaded_plugins.items():
            manifest = self.plugin_manifests[plugin_name]
            contexts.append(f"## {manifest['description']}")
            contexts.append(plugin.get_prompt_context())
            contexts.append("")  # Ligne vide entre plugins

        return "\n".join(contexts)

    async def execute_plugin(
        self, plugin_name: str, intent: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute une action d'un plugin.

        Args:
            plugin_name: Nom du plugin
            intent: Intent à exécuter
            params: Paramètres de l'action

        Returns:
            Résultat de l'exécution

        Raises:
            PluginExecutionError: Si l'exécution échoue
        """
        plugin = self.get_plugin(plugin_name)

        if plugin is None:
            raise PluginExecutionError(
                plugin_name=plugin_name,
                intent=intent,
                message=f"Plugin '{plugin_name}' not loaded",
                timestamp=datetime.utcnow(),
            )

        try:
            result = await plugin.execute(intent, params)
            return result

        except Exception as e:
            raise PluginExecutionError(
                plugin_name=plugin_name,
                intent=intent,
                message=str(e),
                context={
                    "error_type": type(e).__name__,
                    "params": params,
                },
                timestamp=datetime.utcnow(),
            )

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Vérifie la santé de tous les plugins.

        Returns:
            Dictionnaire {plugin_name: is_healthy}
        """
        health_status = {}
        for plugin_name, plugin in self.loaded_plugins.items():
            try:
                is_healthy = await plugin.health_check()
                health_status[plugin_name] = is_healthy
            except Exception:
                health_status[plugin_name] = False

        return health_status
