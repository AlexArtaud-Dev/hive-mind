"""
Infrastructure LLM - Implémentations concrètes des modèles de langage.

Contient les wrappers pour différents modèles LLM (Phi-3, etc.).
"""

from core.infrastructure.llm.phi3_model import Phi3Model

__all__ = [
    "Phi3Model",
]
