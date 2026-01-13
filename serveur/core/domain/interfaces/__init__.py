"""
Interfaces du domaine (abstractions).

Ces interfaces définissent les contrats que doivent respecter
les implémentations de l'infrastructure selon le principe
Dependency Inversion (SOLID).

Usage:
    from core.domain.interfaces import LLMInterface, ContextInterface, PluginInterface

    class MyLLM(LLMInterface):
        async def generate(self, prompt: str, **kwargs) -> LLMResponse:
            # Implémentation...
            pass
"""

from core.domain.interfaces.llm_interface import LLMInterface, LLMResponse
from core.domain.interfaces.context_interface import (
    ContextInterface,
    Message,
)
from core.domain.interfaces.plugin_interface import PluginInterface

__all__ = [
    # LLM
    "LLMInterface",
    "LLMResponse",
    # Context
    "ContextInterface",
    "Message",
    # Plugin
    "PluginInterface",
]
