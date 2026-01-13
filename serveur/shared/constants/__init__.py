"""
Constantes partagées de l'application.

Contient les constantes globales utilisées dans tout le projet.
"""

from shared.constants.prompts import (
    SYSTEM_PROMPT,
    USER_MESSAGE_TEMPLATE,
    PLUGIN_CALL_TEMPLATE,
    ERROR_RESPONSE_TEMPLATE,
    GREETING_PROMPT,
    CLARIFICATION_PROMPT,
)

__all__ = [
    "SYSTEM_PROMPT",
    "USER_MESSAGE_TEMPLATE",
    "PLUGIN_CALL_TEMPLATE",
    "ERROR_RESPONSE_TEMPLATE",
    "GREETING_PROMPT",
    "CLARIFICATION_PROMPT",
]
