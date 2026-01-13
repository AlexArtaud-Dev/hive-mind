"""
Configuration centralisée pour Hive Mind Server.

Utilise Pydantic Settings pour charger la configuration depuis
les variables d'environnement et le fichier .env.
"""

from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration application depuis variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Server Configuration
    server_host: str = Field(
        default="0.0.0.0",
        description="Host sur lequel le serveur écoute"
    )
    server_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port du serveur"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environnement d'exécution"
    )

    # LLM Configuration
    llm_model_path: str = Field(
        default="/app/models/phi3-mini-q4.gguf",
        description="Chemin vers le modèle Phi-3 GGUF"
    )
    llm_context_size: int = Field(
        default=2048,
        ge=512,
        le=8192,
        description="Taille de la fenêtre de contexte du LLM"
    )
    llm_n_threads: int = Field(
        default=8,
        ge=1,
        le=32,
        description="Nombre de threads CPU pour l'inférence"
    )
    llm_n_gpu_layers: int = Field(
        default=0,
        ge=0,
        description="Nombre de couches à offloader sur GPU (0=CPU-only)"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="URL de connexion Redis"
    )
    redis_ttl_seconds: int = Field(
        default=604800,  # 7 jours
        ge=3600,
        description="TTL du contexte conversationnel (secondes)"
    )

    # OpenWeatherMap API
    openweather_api_key: str = Field(
        default="",
        description="Clé API OpenWeatherMap"
    )

    # Google Calendar API (OAuth2)
    google_client_id: str = Field(
        default="",
        description="Client ID Google OAuth2"
    )
    google_client_secret: str = Field(
        default="",
        description="Client Secret Google OAuth2"
    )
    google_redirect_uri: str = Field(
        default="http://localhost:8000/oauth/callback",
        description="URI de redirection OAuth2"
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Niveau de logging"
    )

    # Monitoring
    metrics_enabled: bool = Field(
        default=True,
        description="Activer les métriques Prometheus"
    )

    @field_validator("llm_model_path")
    @classmethod
    def validate_model_path(cls, v: str) -> str:
        """Valide que le chemin du modèle est non vide."""
        if not v or not v.strip():
            raise ValueError("llm_model_path ne peut pas être vide")
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Valide que l'URL Redis commence par redis://."""
        if not v.startswith("redis://"):
            raise ValueError("redis_url doit commencer par 'redis://'")
        return v

    @property
    def is_development(self) -> bool:
        """Retourne True si en mode développement."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Retourne True si en mode production."""
        return self.environment == "production"

    def model_dump_safe(self) -> dict:
        """
        Exporte la configuration en masquant les secrets.

        Returns:
            Dict avec les secrets masqués
        """
        config = self.model_dump()
        # Masquer les secrets
        secrets = [
            "openweather_api_key",
            "google_client_secret",
        ]
        for secret in secrets:
            if secret in config and config[secret]:
                config[secret] = "***MASKED***"
        return config


# Instance globale de configuration
settings = Settings()
