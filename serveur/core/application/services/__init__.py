"""
Services de la couche application.

Services orchestrant la logique métier.
"""

from core.application.services.plugin_service import PluginLoader

__all__ = [
    "PluginLoader",
]
