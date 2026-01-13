# 🤖 Claude.md - Guide de développement Hive Mind

> **Ce document définit les standards de code, architecture et workflow pour le projet Hive Mind.**  
> Il est optimisé pour être utilisé par Claude Code et les développeurs humains.

---

## 📐 Principes fondamentaux

### 1. Clean Architecture

**Séparation stricte des responsabilités** selon les couches :

```
┌─────────────────────────────────────────┐
│          Presentation Layer             │  ← UI, CLI, API endpoints
│  (Controllers, Handlers, Views)         │
└─────────────────────────────────────────┘
              ↓ DTOs
┌─────────────────────────────────────────┐
│          Application Layer              │  ← Use cases, orchestration
│  (Services, Commands, Queries)          │
└─────────────────────────────────────────┘
              ↓ Business objects
┌─────────────────────────────────────────┐
│            Domain Layer                 │  ← Business logic, entities
│  (Models, Entities, Value Objects)      │
└─────────────────────────────────────────┘
              ↓ Interfaces
┌─────────────────────────────────────────┐
│         Infrastructure Layer            │  ← External systems
│  (Repositories, APIs, Database)         │
└─────────────────────────────────────────┘
```

**Organisation des dossiers** :

```
serveur/
├── core/
│   ├── domain/              # Entités, value objects, interfaces
│   │   ├── entities/
│   │   ├── value_objects/
│   │   └── interfaces/
│   ├── application/         # Services, use cases
│   │   ├── services/
│   │   ├── commands/
│   │   └── queries/
│   ├── infrastructure/      # Implémentations concrètes
│   │   ├── repositories/
│   │   ├── external_apis/
│   │   └── database/
│   └── presentation/        # Controllers, handlers
│       ├── websocket/
│       └── http/
├── shared/                  # Code partagé
│   ├── constants/
│   ├── enums/
│   ├── dtos/
│   ├── errors/
│   └── logging/
└── plugins/                 # Plugins métier

client/src/
├── domain/                  # Core business logic
│   ├── models/
│   └── traits/
├── application/             # Services
│   ├── audio/
│   ├── websocket/
│   └── commands/
├── infrastructure/          # Implémentations
│   ├── audio/
│   ├── network/
│   └── storage/
└── presentation/            # UI
    ├── desktop/
    └── embedded/
```

---

### 2. SOLID Principles

#### **S - Single Responsibility Principle**
✅ **Correct** :
```python
class UserRepository:
    """Gère uniquement la persistance des utilisateurs"""
    def save(self, user: User) -> None: ...
    def find_by_id(self, user_id: str) -> Optional[User]: ...

class UserValidator:
    """Gère uniquement la validation des utilisateurs"""
    def validate(self, user: User) -> ValidationResult: ...
```

❌ **Incorrect** :
```python
class UserManager:
    """Fait trop de choses à la fois"""
    def save(self, user: User) -> None: ...
    def validate(self, user: User) -> bool: ...
    def send_email(self, user: User) -> None: ...
    def generate_report(self, user: User) -> str: ...
```

#### **O - Open/Closed Principle**
Ouvert à l'extension, fermé à la modification.

```python
# Base abstraction
class Plugin(ABC):
    @abstractmethod
    async def execute(self, intent: str, params: Dict) -> Dict: ...

# Extension sans modifier la base
class WeatherPlugin(Plugin):
    async def execute(self, intent: str, params: Dict) -> Dict:
        # Implémentation spécifique
        ...
```

#### **L - Liskov Substitution Principle**
Les sous-classes doivent être substituables à leurs classes parentes.

```python
class AudioSource(ABC):
    @abstractmethod
    def capture(self) -> bytes: ...

class MicrophoneSource(AudioSource):
    def capture(self) -> bytes:
        # Respecte le contrat de AudioSource
        return self.mic.read()
```

#### **I - Interface Segregation Principle**
Interfaces spécifiques plutôt qu'une interface générale.

✅ **Correct** :
```python
class Readable(Protocol):
    def read(self) -> bytes: ...

class Writable(Protocol):
    def write(self, data: bytes) -> None: ...

class AudioDevice(Readable, Writable):
    # Implémente seulement ce dont il a besoin
    ...
```

❌ **Incorrect** :
```python
class AllInOne(Protocol):
    def read(self) -> bytes: ...
    def write(self, data: bytes) -> None: ...
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def configure(self, config: Dict) -> None: ...
    # Trop de méthodes, certains devices n'en ont pas besoin
```

#### **D - Dependency Inversion Principle**
Dépendre d'abstractions, pas d'implémentations concrètes.

✅ **Correct** :
```python
class LLMService:
    def __init__(self, model: LLMInterface):  # Dépend de l'interface
        self.model = model

# Injection de dépendance
llm = Phi3Model()
service = LLMService(model=llm)
```

❌ **Incorrect** :
```python
class LLMService:
    def __init__(self):
        self.model = Phi3Model()  # Couplage fort à l'implémentation
```

---

### 3. DRY (Don't Repeat Yourself)

**Principe** : Ne jamais dupliquer de logique. Extraire dans des fonctions/classes réutilisables.

✅ **Correct** :
```python
# shared/utils/validators.py
def validate_non_empty_string(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValidationError(f"{field_name} ne peut pas être vide")

# Usage
validate_non_empty_string(user.name, "name")
validate_non_empty_string(user.email, "email")
```

❌ **Incorrect** :
```python
if not user.name or not user.name.strip():
    raise ValidationError("name ne peut pas être vide")

if not user.email or not user.email.strip():
    raise ValidationError("email ne peut pas être vide")
```

**Règle** : Si du code est dupliqué 2+ fois, extraire immédiatement.

---

### 4. Fonctions simples et testables

#### **Une fonction = un usage**

✅ **Correct** :
```python
def parse_temperature(data: Dict) -> float:
    """Parse la température depuis les données météo API"""
    return float(data["main"]["temp"])

def format_temperature(temp: float) -> str:
    """Formate la température pour affichage"""
    return f"{temp:.1f}°C"

def get_formatted_temperature(data: Dict) -> str:
    """Récupère et formate la température"""
    temp = parse_temperature(data)
    return format_temperature(temp)
```

❌ **Incorrect** :
```python
def do_temperature_stuff(data: Dict, format_it: bool = False) -> Union[float, str]:
    """Fonction qui fait plusieurs choses selon un flag"""
    temp = float(data["main"]["temp"])
    if format_it:
        return f"{temp:.1f}°C"
    return temp
```

#### **Taille maximale** : 
- **20 lignes** pour fonctions standards
- **50 lignes** maximum absolu (si dépassé, découper)

#### **Complexité cyclomatique** : ≤ 10

#### **Inputs/Outputs explicites**

```python
def process_audio(
    audio_data: bytes,
    sample_rate: int,
    channels: int = 1
) -> AudioProcessingResult:
    """
    Traite les données audio brutes.
    
    Args:
        audio_data: Données audio brutes (PCM 16-bit)
        sample_rate: Fréquence d'échantillonnage en Hz
        channels: Nombre de canaux (défaut: 1 = mono)
    
    Returns:
        AudioProcessingResult contenant les données traitées et métadonnées
    
    Raises:
        InvalidAudioDataError: Si audio_data est vide ou corrompu
        UnsupportedSampleRateError: Si sample_rate n'est pas supporté (8000-48000 Hz)
    """
    if not audio_data:
        raise InvalidAudioDataError("audio_data ne peut pas être vide")
    
    if not 8000 <= sample_rate <= 48000:
        raise UnsupportedSampleRateError(
            f"sample_rate {sample_rate} hors limites [8000-48000]"
        )
    
    # Traitement...
    return AudioProcessingResult(...)
```

---

### 5. Typage strict

#### **Python : Type hints exhaustifs**

```python
from typing import Dict, List, Optional, Union, Literal, Protocol
from dataclasses import dataclass

# ✅ Correct
@dataclass
class User:
    id: str
    name: str
    email: str
    age: Optional[int] = None

def get_users(
    filters: Dict[str, Union[str, int]],
    limit: int = 10
) -> List[User]:
    ...

# ❌ Incorrect (pas de types)
def get_users(filters, limit=10):
    ...
```

**Configuration mypy** (Python) :
```ini
# pyproject.toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
```

#### **Rust : Typage déjà strict**

```rust
// ✅ Rust enforce le typage
pub fn process_message(
    message: &str,
    timestamp: DateTime<Utc>
) -> Result<ProcessedMessage, ProcessingError> {
    // ...
}

// Pas besoin de vérifications supplémentaires
```

---

### 6. Naming Conventions

| Élément | Convention | Exemple |
|---------|------------|---------|
| **Variables** | `snake_case` | `user_name`, `audio_buffer` |
| **Fonctions** | `snake_case` (verbe) | `get_user()`, `validate_input()` |
| **Classes** | `PascalCase` | `UserRepository`, `AudioProcessor` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| **Enums** | `PascalCase` | `ConnectionState`, `ErrorCode` |
| **Privé Python** | `_leading_underscore` | `_internal_method()` |
| **Privé Rust** | Pas de convention (scope par défaut) | N/A |

**Noms de fonctions** : Toujours un verbe d'action
```python
# ✅ Correct
get_user()
create_session()
validate_token()
is_connected()
has_permission()

# ❌ Incorrect
user()
session()
token()
connected()
```

---

### 7. Pas de Magic Numbers

✅ **Correct** :
```python
# shared/constants/audio.py
SAMPLE_RATE_HZ = 16000
CHANNELS_MONO = 1
BUFFER_SIZE_MS = 100
MAX_AUDIO_DURATION_SEC = 30

# Usage
if duration > MAX_AUDIO_DURATION_SEC:
    raise AudioTooLongError()
```

❌ **Incorrect** :
```python
if duration > 30:  # Qu'est-ce que 30 ?
    raise AudioTooLongError()

buffer = allocate(16000 * 100 / 1000)  # Calcul obscur
```

---

### 8. Documentation obligatoire

#### **Python : Docstrings Google Style**

```python
def calculate_similarity(
    text1: str,
    text2: str,
    algorithm: str = "levenshtein"
) -> float:
    """
    Calcule la similarité entre deux textes.
    
    Args:
        text1: Premier texte à comparer
        text2: Deuxième texte à comparer
        algorithm: Algorithme à utiliser ("levenshtein" ou "cosine")
    
    Returns:
        Score de similarité entre 0.0 (différent) et 1.0 (identique)
    
    Raises:
        ValueError: Si algorithm n'est pas supporté
        EmptyTextError: Si text1 ou text2 est vide
    
    Examples:
        >>> calculate_similarity("hello", "hallo")
        0.8
        >>> calculate_similarity("chat", "chien", algorithm="cosine")
        0.3
    """
    ...
```

#### **Rust : Rustdoc**

```rust
/// Calcule la similarité entre deux textes.
///
/// # Arguments
///
/// * `text1` - Premier texte à comparer
/// * `text2` - Deuxième texte à comparer
/// * `algorithm` - Algorithme à utiliser
///
/// # Returns
///
/// Score de similarité entre 0.0 et 1.0
///
/// # Errors
///
/// Retourne `Err(SimilarityError)` si :
/// - `algorithm` n'est pas supporté
/// - `text1` ou `text2` est vide
///
/// # Examples
///
/// ```
/// let score = calculate_similarity("hello", "hallo", Algorithm::Levenshtein)?;
/// assert_eq!(score, 0.8);
/// ```
pub fn calculate_similarity(
    text1: &str,
    text2: &str,
    algorithm: Algorithm
) -> Result<f64, SimilarityError> {
    // ...
}
```

---

### 9. Guard Clauses (Early Return)

✅ **Correct** :
```python
def process_user_request(user: User, request: Request) -> Response:
    """Traite une requête utilisateur"""
    
    # Guards en premier
    if not user.is_authenticated:
        raise UnauthorizedError("User not authenticated")
    
    if not request.is_valid():
        raise InvalidRequestError("Invalid request format")
    
    if user.is_rate_limited():
        raise RateLimitError("Too many requests")
    
    # Logique principale (pas d'indentation profonde)
    result = perform_action(request)
    return create_response(result)
```

❌ **Incorrect** :
```python
def process_user_request(user: User, request: Request) -> Response:
    if user.is_authenticated:
        if request.is_valid():
            if not user.is_rate_limited():
                result = perform_action(request)  # Pyramide d'indentation
                return create_response(result)
            else:
                raise RateLimitError()
        else:
            raise InvalidRequestError()
    else:
        raise UnauthorizedError()
```

---

### 10. Énumérations pour valeurs fixes

✅ **Correct** :
```python
# shared/enums/connection_state.py
from enum import Enum, auto

class ConnectionState(Enum):
    """États possibles de la connexion client-serveur"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    DEGRADED = auto()

# Usage avec typage strict
def handle_state_change(state: ConnectionState) -> None:
    match state:
        case ConnectionState.CONNECTED:
            logger.info("Connection established")
        case ConnectionState.DEGRADED:
            logger.warning("Degraded mode activated")
        # ...
```

```rust
// shared/enums.rs
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ConnectionState {
    Disconnected,
    Connecting,
    Connected,
    Reconnecting,
    Degraded,
}

// Usage
fn handle_state_change(state: ConnectionState) {
    match state {
        ConnectionState::Connected => info!("Connection established"),
        ConnectionState::Degraded => warn!("Degraded mode activated"),
        // Rust force l'exhaustivité du match
    }
}
```

❌ **Incorrect** :
```python
# String literals magiques
if connection_status == "connected":  # Typo risk: "conected", "Connected"
    ...

STATE_CONNECTED = "connected"  # Mieux mais pas type-safe
```

---

### 11. Gestion des erreurs

#### **Hiérarchie d'erreurs**

```python
# shared/errors/base.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class BaseError(Exception):
    """Erreur de base pour toutes les erreurs Hive Mind"""
    message: str
    error_code: str
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'erreur pour logging"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context or {}
        }

# shared/errors/domain.py
class DomainError(BaseError):
    """Erreur métier"""
    pass

class ValidationError(DomainError):
    """Erreur de validation"""
    def __init__(self, field: str, message: str, **kwargs):
        super().__init__(
            message=f"Validation failed for {field}: {message}",
            error_code="VALIDATION_ERROR",
            **kwargs
        )

class AudioProcessingError(DomainError):
    """Erreur de traitement audio"""
    pass

# shared/errors/infrastructure.py
class InfrastructureError(BaseError):
    """Erreur infrastructure"""
    pass

class DatabaseError(InfrastructureError):
    """Erreur base de données"""
    pass

class ExternalAPIError(InfrastructureError):
    """Erreur API externe"""
    def __init__(self, api_name: str, status_code: int, **kwargs):
        super().__init__(
            message=f"API {api_name} returned {status_code}",
            error_code="EXTERNAL_API_ERROR",
            context={"api_name": api_name, "status_code": status_code},
            **kwargs
        )
```

#### **Rust : Result type**

```rust
// shared/errors.rs
use thiserror::Error;

#[derive(Error, Debug)]
pub enum HiveMindError {
    #[error("Audio processing failed: {0}")]
    AudioProcessing(String),
    
    #[error("WebSocket connection error: {0}")]
    WebSocket(#[from] tokio_tungstenite::tungstenite::Error),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    #[error("Invalid configuration: {field} - {reason}")]
    InvalidConfig { field: String, reason: String },
}

pub type Result<T> = std::result::Result<T, HiveMindError>;
```

#### **Error handling exhaustif**

❌ **Incorrect** :
```python
try:
    result = risky_operation()
except Exception as e:  # Trop général
    logger.error(f"Error: {e}")
```

✅ **Correct** :
```python
try:
    result = risky_operation()
except ValidationError as e:
    logger.error("Validation failed", extra=e.to_dict())
    raise
except DatabaseError as e:
    logger.error("Database error", extra=e.to_dict())
    # Retry logic ou fallback
except Exception as e:
    # Erreur inattendue
    logger.critical("Unexpected error", exc_info=True)
    raise InfrastructureError(
        message=f"Unexpected error: {e}",
        error_code="UNEXPECTED_ERROR",
        timestamp=datetime.utcnow()
    )
```

---

### 12. Logging structuré

#### **Configuration logger générique**

```python
# shared/logging/logger.py
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from shared.errors.base import BaseError

class StructuredLogger:
    """Logger avec format JSON structuré"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_handler()
    
    def _setup_handler(self):
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def _log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        error: Optional[BaseError] = None
    ):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "service": self.logger.name
        }
        
        if extra:
            log_entry["extra"] = extra
        
        if error:
            log_entry["error"] = error.to_dict()
        
        self.logger.log(
            getattr(logging, level),
            json.dumps(log_entry)
        )
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log("CRITICAL", message, **kwargs)

# Usage
logger = StructuredLogger("weather_plugin")

logger.info(
    "Weather data fetched",
    extra={"location": "Belfort", "temperature": 8.5}
)

logger.error(
    "Failed to fetch weather",
    error=ExternalAPIError("OpenWeather", 503, timestamp=datetime.utcnow())
)
```

**Format de log** :
```json
{
  "timestamp": "2026-01-06T14:30:00.123456Z",
  "level": "ERROR",
  "message": "Failed to fetch weather",
  "service": "weather_plugin",
  "error": {
    "error_code": "EXTERNAL_API_ERROR",
    "message": "API OpenWeather returned 503",
    "timestamp": "2026-01-06T14:30:00Z",
    "context": {
      "api_name": "OpenWeather",
      "status_code": 503
    }
  }
}
```

#### **Rust : tracing**

```rust
// Cargo.toml: tracing = "0.1", tracing-subscriber = { version = "0.3", features = ["json"] }

use tracing::{info, warn, error, instrument};

#[instrument(skip(audio_data))]
pub async fn process_audio(audio_data: &[u8]) -> Result<ProcessedAudio> {
    info!(
        size = audio_data.len(),
        "Processing audio data"
    );
    
    match perform_processing(audio_data) {
        Ok(result) => {
            info!(duration_ms = result.duration, "Audio processed successfully");
            Ok(result)
        }
        Err(e) => {
            error!(error = %e, "Audio processing failed");
            Err(e)
        }
    }
}
```

---

### 13. Immutabilité par défaut

✅ **Correct** :
```python
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)  # Immutable
class AudioConfig:
    sample_rate: int
    channels: int
    buffer_size: int

# Rust : immutable par défaut
let config = AudioConfig {
    sample_rate: 16000,
    channels: 1,
};
// config.sample_rate = 48000;  // ❌ Erreur de compilation
```

**Mutations explicites** :
```python
# Si mutation nécessaire, créer une nouvelle instance
def with_sample_rate(config: AudioConfig, new_rate: int) -> AudioConfig:
    return AudioConfig(
        sample_rate=new_rate,
        channels=config.channels,
        buffer_size=config.buffer_size
    )
```

---

### 14. Configuration externalisée

```python
# config/settings.py
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Configuration application depuis variables d'environnement"""
    
    # Server
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=8000, env="SERVER_PORT")
    
    # LLM
    llm_model_path: str = Field(..., env="LLM_MODEL_PATH")  # Requis
    llm_context_size: int = Field(default=2048, env="LLM_CONTEXT_SIZE")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_ttl_seconds: int = Field(default=604800, env="REDIS_TTL_SECONDS")  # 7 jours
    
    # OpenWeather
    openweather_api_key: str = Field(..., env="OPENWEATHER_API_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

**.env** (jamais commité, .gitignore) :
```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LLM_MODEL_PATH=/app/models/phi3-mini-q4.gguf
REDIS_URL=redis://redis:6379
OPENWEATHER_API_KEY=your_key_here
```

---

### 15. Dependency Injection

```python
# core/application/services/llm_service.py
from core.domain.interfaces.llm_interface import LLMInterface

class LLMService:
    """Service utilisant l'IA pour générer des réponses"""
    
    def __init__(self, model: LLMInterface):  # Injection via constructeur
        self.model = model
    
    async def generate_response(self, prompt: str) -> str:
        return await self.model.generate(prompt)

# core/infrastructure/llm/phi3_model.py
class Phi3Model(LLMInterface):
    async def generate(self, prompt: str) -> str:
        # Implémentation Phi-3
        ...

# main.py
from core.application.services.llm_service import LLMService
from core.infrastructure.llm.phi3_model import Phi3Model

# Composition manuelle (ou via DI container)
model = Phi3Model(model_path=settings.llm_model_path)
llm_service = LLMService(model=model)
```

#### **DI Container (optionnel pour gros projets)**

```python
# dependency_injector example
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    llm_model = providers.Singleton(
        Phi3Model,
        model_path=config.llm_model_path
    )
    
    llm_service = providers.Factory(
        LLMService,
        model=llm_model
    )

container = Container()
container.config.from_pydantic(settings)
```

---

### 16. Tests exhaustifs

#### **Test Pyramid**

```
       /\
      /  \     E2E Tests (5%)
     /____\    
    /      \   Integration Tests (15%)
   /________\  
  /          \ Unit Tests (80%)
 /____________\
```

#### **Structure AAA (Arrange-Act-Assert)**

```python
# tests/unit/test_weather_plugin.py
import pytest
from unittest.mock import AsyncMock, patch
from plugins.weather.handler import WeatherPlugin
from shared.errors.infrastructure import ExternalAPIError

class TestWeatherPlugin:
    """Tests unitaires du plugin météo"""
    
    @pytest.fixture
    def plugin(self):
        """Fixture pour créer une instance du plugin"""
        config = {
            "api_key": "test_key",
            "default_location": "Belfort, FR"
        }
        return WeatherPlugin(config)
    
    @pytest.mark.asyncio
    async def test_get_weather_success(self, plugin):
        """Doit retourner les données météo pour une localisation valide"""
        # ARRANGE
        mock_response = {
            "main": {"temp": 8.5, "feels_like": 6.0, "humidity": 75},
            "weather": [{"description": "nuageux"}]
        }
        
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.json = AsyncMock(return_value=mock_response)
            
            # ACT
            result = await plugin.execute(
                intent="get_weather",
                params={"location": "Paris"}
            )
            
            # ASSERT
            assert result["success"] is True
            assert result["temperature"] == 8.5
            assert result["description"] == "nuageux"
            assert result["location"] == "Paris"
    
    @pytest.mark.asyncio
    async def test_get_weather_api_error(self, plugin):
        """Doit lever ExternalAPIError si l'API échoue"""
        # ARRANGE
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            # ACT & ASSERT
            with pytest.raises(ExternalAPIError) as exc_info:
                await plugin.execute("get_weather", {"location": "Paris"})
            
            assert "OpenWeather" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_weather_uses_default_location(self, plugin):
        """Doit utiliser la localisation par défaut si non spécifiée"""
        # ARRANGE
        mock_response = {"main": {"temp": 10}, "weather": [{"description": "soleil"}]}
        
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value.json = AsyncMock(return_value=mock_response)
            
            # ACT
            result = await plugin.execute("get_weather", {})
            
            # ASSERT
            assert result["location"] == "Belfort, FR"
```

#### **Rust : Tests unitaires**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_parse_temperature_valid() {
        // ARRANGE
        let data = r#"{"main": {"temp": 8.5}}"#;
        let json: serde_json::Value = serde_json::from_str(data).unwrap();
        
        // ACT
        let temp = parse_temperature(&json);
        
        // ASSERT
        assert_eq!(temp, 8.5);
    }
    
    #[test]
    #[should_panic(expected = "Missing temperature")]
    fn test_parse_temperature_missing_field() {
        // ARRANGE
        let data = r#"{"weather": "sunny"}"#;
        let json: serde_json::Value = serde_json::from_str(data).unwrap();
        
        // ACT
        parse_temperature(&json);  // Doit paniquer
    }
    
    #[tokio::test]
    async fn test_audio_processing_pipeline() {
        // ARRANGE
        let audio = vec![0u8; 16000];  // 1 seconde @ 16kHz
        let processor = AudioProcessor::new();
        
        // ACT
        let result = processor.process(&audio).await;
        
        // ASSERT
        assert!(result.is_ok());
        let processed = result.unwrap();
        assert_eq!(processed.duration_ms, 1000);
    }
}
```

#### **Coverage ≥ 80%**

```bash
# Python : pytest-cov
pytest --cov=core --cov=plugins --cov-report=html --cov-report=term

# Rust : tarpaulin
cargo tarpaulin --out Html --output-dir coverage
```

**CI doit bloquer si coverage < 80%**

---

### 17. Input Validation stricte

```python
# shared/validators/input_validator.py
from typing import Any
from shared.errors.domain import ValidationError

class InputValidator:
    """Validateur générique d'inputs"""
    
    @staticmethod
    def validate_string(
        value: Any,
        field_name: str,
        min_length: int = 1,
        max_length: int = 1000
    ) -> str:
        """Valide une chaîne de caractères"""
        if not isinstance(value, str):
            raise ValidationError(
                field=field_name,
                message=f"Expected string, got {type(value).__name__}"
            )
        
        if len(value) < min_length:
            raise ValidationError(
                field=field_name,
                message=f"Minimum length is {min_length}"
            )
        
        if len(value) > max_length:
            raise ValidationError(
                field=field_name,
                message=f"Maximum length is {max_length}"
            )
        
        return value.strip()
    
    @staticmethod
    def validate_int_range(
        value: Any,
        field_name: str,
        min_val: int,
        max_val: int
    ) -> int:
        """Valide un entier dans une plage"""
        if not isinstance(value, int):
            raise ValidationError(
                field=field_name,
                message=f"Expected int, got {type(value).__name__}"
            )
        
        if not min_val <= value <= max_val:
            raise ValidationError(
                field=field_name,
                message=f"Value must be between {min_val} and {max_val}"
            )
        
        return value

# Usage
def create_user(name: str, age: int) -> User:
    validated_name = InputValidator.validate_string(name, "name", min_length=2, max_length=50)
    validated_age = InputValidator.validate_int_range(age, "age", min_val=0, max_val=150)
    
    return User(name=validated_name, age=validated_age)
```

---

### 18. Secrets management

❌ **JAMAIS** :
```python
# ❌ DANGEREUX
API_KEY = "sk-1234567890abcdef"  # Hard-codé dans le code
```

✅ **Correct** :
```python
# Via variables d'environnement
import os
API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY environment variable not set")

# Ou via Pydantic Settings (recommandé)
from config.settings import settings
API_KEY = settings.openweather_api_key
```

**Pour production** :
- Docker secrets
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault

---

### 19. Health Checks

```python
# core/presentation/http/health.py
from fastapi import APIRouter, Response, status
from typing import Dict, Any

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check basique pour orchestration.
    Retourne 200 si le service est vivant.
    """
    return {"status": "healthy"}

@router.get("/ready")
async def readiness_check() -> Response:
    """
    Readiness check pour orchestration.
    Vérifie que toutes les dépendances sont disponibles.
    """
    checks = {
        "redis": await check_redis_connection(),
        "llm_model": await check_llm_loaded(),
        "plugins": await check_plugins_loaded()
    }
    
    if all(checks.values()):
        return Response(
            content=json.dumps({"status": "ready", "checks": checks}),
            status_code=status.HTTP_200_OK
        )
    else:
        return Response(
            content=json.dumps({"status": "not_ready", "checks": checks}),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
```

---

### 20. Correlation IDs

```python
# shared/middleware/correlation_id.py
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Récupérer ou générer correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id_var.set(correlation_id)
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

# Usage dans logger
class StructuredLogger:
    def _log(self, level: str, message: str, **kwargs):
        log_entry = {
            "correlation_id": correlation_id_var.get(),  # Ajouté automatiquement
            "timestamp": datetime.utcnow().isoformat(),
            # ...
        }
        # ...
```

---

### 21. Métriques

```python
# shared/metrics/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Définition des métriques
request_count = Counter(
    "hive_mind_requests_total",
    "Total requests",
    ["endpoint", "method"]
)

request_duration = Histogram(
    "hive_mind_request_duration_seconds",
    "Request duration",
    ["endpoint"]
)

active_connections = Gauge(
    "hive_mind_active_connections",
    "Active WebSocket connections"
)

plugin_calls = Counter(
    "hive_mind_plugin_calls_total",
    "Plugin executions",
    ["plugin_name", "status"]
)

# Décorateur pour mesurer automatiquement
def measure_duration(metric_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                plugin_calls.labels(plugin_name=metric_name, status="success").inc()
                return result
            except Exception as e:
                plugin_calls.labels(plugin_name=metric_name, status="error").inc()
                raise
            finally:
                duration = time.time() - start
                request_duration.labels(endpoint=metric_name).observe(duration)
        return wrapper
    return decorator

# Usage
@measure_duration("weather_plugin")
async def get_weather(location: str):
    ...
```

---

## 🔄 Workflow de développement

### 1. Développement par feature

#### **Branch naming**

```
type/scope-description

Types:
- feat/     : Nouvelle fonctionnalité
- fix/      : Correction de bug
- refactor/ : Refactoring sans changement fonctionnel
- docs/     : Documentation uniquement
- test/     : Ajout/modification de tests
- chore/    : Maintenance (deps, config)

Exemples:
feat/weather-plugin
fix/websocket-reconnect
refactor/llm-service-cleanup
docs/api-endpoints
test/audio-pipeline-coverage
```

#### **Cycle de développement**

```
1. Créer branche feature
   git checkout -b feat/new-feature

2. Développer feature fichier par fichier
   [voir section validation ci-dessous]

3. Ajouter tests
   - Tests unitaires pour chaque fonction
   - Tests d'intégration si nécessaire
   - Vérifier coverage ≥ 80%

4. Commit avec convention semantic
   [voir section commits ci-dessous]

5. Push et PR
   git push origin feat/new-feature
```

---

### 2. Validation fichier par fichier

#### **Processus de génération**

Quand Claude Code génère du code :

1. **Générer UN fichier à la fois**
   ```
   ✅ Correct:
   Claude: "Je vais créer le fichier core/domain/entities/user.py"
   [génère le fichier]
   Claude: "Fichier créé. Voulez-vous que je passe au suivant ?"
   
   ❌ Incorrect:
   [génère 10 fichiers d'un coup sans validation]
   ```

2. **Humain valide le fichier**
   ```
   Options:
   - ✅ "OK, passe au suivant"
   - 🔄 "Modifie [aspect X]"
   - ❌ "Recommence ce fichier"
   ```

3. **Répéter pour chaque fichier de la feature**

4. **Une fois tous les fichiers validés**
   ```
   Claude: "Tous les fichiers de la feature sont créés.
           Je vais maintenant générer les tests."
   ```

5. **Générer les tests (un fichier de test à la fois)**
   - Test unitaire pour chaque module
   - Validation humaine après chaque test

6. **Vérifier coverage**
   ```bash
   pytest --cov=core/domain/entities --cov-report=term
   ```

7. **Si coverage < 80%** : ajouter tests manquants

8. **Commit la feature complète**

---

### 3. Conventional Commits

#### **Format strict**

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

#### **Types autorisés**

| Type | Usage | Emoji |
|------|-------|-------|
| `feat` | Nouvelle fonctionnalité | ✨ |
| `fix` | Correction de bug | 🐛 |
| `docs` | Documentation | 📝 |
| `style` | Formatting, missing semi colons, etc. | 💄 |
| `refactor` | Refactoring sans changement fonctionnel | ♻️ |
| `perf` | Amélioration de performance | ⚡ |
| `test` | Ajout/modification de tests | ✅ |
| `chore` | Maintenance (deps, build, etc.) | 🔧 |
| `ci` | Changements CI/CD | 👷 |
| `revert` | Annulation d'un commit précédent | ⏪ |

#### **Exemples**

```bash
# Feature simple
git commit -m "feat(weather): add OpenWeatherMap integration"

# Feature avec body
git commit -m "feat(llm): integrate Phi-3-mini model

- Add llama-cpp-python wrapper
- Implement streaming responses
- Configure context window of 2048 tokens

Closes #42"

# Fix
git commit -m "fix(websocket): handle disconnection gracefully

Previously, disconnections caused unhandled exceptions.
Now we catch the error and trigger reconnection logic.

Fixes #58"

# Breaking change
git commit -m "feat(api)!: change response format to include metadata

BREAKING CHANGE: Response format changed from:
  { "content": "..." }
To:
  { "content": "...", "metadata": {...} }

Migration guide in docs/migration-v2.md"

# Refactor
git commit -m "refactor(audio): extract STT logic to separate service

No functional changes, just improved code organization."

# Tests
git commit -m "test(plugin-loader): add unit tests for dynamic loading

Increases coverage from 65% to 85%"

# Chore
git commit -m "chore(deps): update fastapi to 0.109.0"
```

#### **Règles**

- **Subject** : 
  - Max 72 caractères
  - Impératif ("add" pas "added")
  - Pas de point final
  - Minuscule après le type

- **Body** (optionnel) :
  - Ligne vide après subject
  - Explique "pourquoi" pas "comment"
  - Max 100 caractères par ligne

- **Footer** (optionnel) :
  - Références issues : `Closes #123`
  - Breaking changes : `BREAKING CHANGE: description`

#### **Validation automatique**

```bash
# .git/hooks/commit-msg
#!/bin/bash
commit_msg=$(cat $1)
pattern="^(feat|fix|docs|style|refactor|perf|test|chore|ci|revert)(\([a-z-]+\))?: .{1,72}$"

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "❌ Commit message invalide"
    echo "Format: <type>(<scope>): <subject>"
    exit 1
fi
```

---

### 4. Pull Request Template

```markdown
## Description
[Décrire la feature/fix en quelques phrases]

## Type de changement
- [ ] 🐛 Bug fix (non-breaking change qui corrige un bug)
- [ ] ✨ Nouvelle feature (non-breaking change qui ajoute une fonctionnalité)
- [ ] 💥 Breaking change (fix ou feature qui casse la compatibilité)
- [ ] 📝 Documentation uniquement

## Checklist
- [ ] Mon code respecte les conventions de style du projet
- [ ] J'ai effectué une auto-revue de mon code
- [ ] J'ai commenté mon code, particulièrement les parties complexes
- [ ] J'ai mis à jour la documentation si nécessaire
- [ ] Mes changements ne génèrent pas de nouveaux warnings
- [ ] J'ai ajouté des tests qui prouvent que ma feature fonctionne
- [ ] Les tests unitaires passent localement (`pytest`)
- [ ] Les tests d'intégration passent si applicable
- [ ] Le coverage reste ≥ 80%

## Tests ajoutés
- [ ] Tests unitaires : [liste des fichiers de test]
- [ ] Tests d'intégration : [si applicable]

## Screenshots / Logs
[Si applicable, ajouter captures d'écran ou logs]

## Issues liées
Closes #[numéro]
Refs #[numéro]

## Notes pour les reviewers
[Informations supplémentaires pour faciliter la revue]
```

---

### 5. Protected main branch

**Configuration GitHub/GitLab** :

- ❌ Pas de push direct sur `main`
- ✅ PR obligatoires
- ✅ Au moins 1 approbation requise
- ✅ CI doit passer (tests + linting)
- ✅ Pas de force-push
- ✅ Commits signés (optionnel mais recommandé)

---

### 6. CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov mypy black flake8
    
    - name: Lint with black
      run: black --check serveur/
    
    - name: Type check with mypy
      run: mypy serveur/
    
    - name: Lint with flake8
      run: flake8 serveur/ --max-line-length=100
    
    - name: Run tests with coverage
      run: |
        pytest --cov=serveur --cov-report=xml --cov-report=term
    
    - name: Check coverage threshold
      run: |
        coverage report --fail-under=80
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

---

## 📊 Métriques de qualité

### Code Quality Gates

| Métrique | Seuil | Outil |
|----------|-------|-------|
| **Test coverage** | ≥ 80% | pytest-cov, tarpaulin |
| **Complexité cyclomatique** | ≤ 10 | radon, cargo-clippy |
| **Duplication** | < 3% | pylint, cargo-clippy |
| **Type safety** | 100% | mypy strict, rustc |
| **Linting** | 0 erreurs | flake8, black, clippy |
| **Documentation** | 100% fonctions publiques | pydocstyle, rustdoc |

### Commandes de vérification

```bash
# Python
black serveur/ --check          # Formatting
flake8 serveur/                 # Linting
mypy serveur/ --strict          # Type checking
pytest --cov=serveur --cov-fail-under=80
radon cc serveur/ -a            # Complexité

# Rust
cargo fmt -- --check            # Formatting
cargo clippy -- -D warnings     # Linting
cargo test                      # Tests
cargo tarpaulin --fail-under 80 # Coverage
```

---

## 🎓 Exemples complets

### Exemple 1 : Création d'une nouvelle feature

**Feature** : Ajouter un plugin calendar

```bash
# 1. Créer branche
git checkout -b feat/calendar-plugin

# 2. Claude génère fichiers un par un

# Fichier 1
Claude: "Je crée plugins/calendar/plugin.json"
[génère le fichier]
Claude: "Fichier créé, voulez-vous valider ?"
Humain: "OK"

# Fichier 2
Claude: "Je crée plugins/calendar/handler.py"
[génère le fichier avec docstrings, types, etc.]
Claude: "Fichier créé, voulez-vous valider ?"
Humain: "Modifie la fonction add_event pour utiliser timezone UTC"
Claude: [modifie]
Humain: "OK"

# Fichier 3
Claude: "Je crée plugins/calendar/__init__.py"
[génère le fichier]
Claude: "Fichier créé, voulez-vous valider ?"
Humain: "OK"

# 3. Génération des tests
Claude: "Tous les fichiers de la feature sont validés. Je génère les tests."

# Test 1
Claude: "Je crée tests/unit/plugins/test_calendar.py"
[génère les tests AAA avec fixtures, mocks, etc.]
Claude: "Tests créés, voulez-vous valider ?"
Humain: "Ajoute un test pour le cas où l'API Google retourne 429"
Claude: [ajoute test]
Humain: "OK"

# 4. Vérifier coverage
$ pytest --cov=plugins/calendar --cov-report=term
----------- coverage: 87% -----------

# 5. Commit
git add plugins/calendar/ tests/unit/plugins/test_calendar.py
git commit -m "feat(calendar): add Google Calendar integration

- Implement OAuth2 authentication
- Add add_event and list_events methods
- Handle API rate limiting with exponential backoff

Closes #42"

# 6. Push et PR
git push origin feat/calendar-plugin
```

---

### Exemple 2 : Refactoring

```bash
git checkout -b refactor/llm-service-cleanup

# Claude identifie code dupliqué
Claude: "J'ai identifié une duplication dans llm_service.py et context_manager.py
        concernant le formatage des prompts. Je propose d'extraire dans
        shared/utils/prompt_formatter.py"

Humain: "OK, fais-le"

# Claude génère le nouveau fichier
Claude: "Je crée shared/utils/prompt_formatter.py"
[génère avec docstrings, types, tests]

# Claude modifie les fichiers existants
Claude: "Je modifie core/application/services/llm_service.py pour utiliser le nouveau formatter"
[modifie]

Claude: "Je modifie core/application/services/context_manager.py"
[modifie]

# Tests
Claude: "J'ajoute les tests pour prompt_formatter.py"
[génère tests]

# Vérification
$ pytest
All tests passed
$ pytest --cov=shared/utils --cov-report=term
----------- coverage: 95% -----------

# Commit
git add shared/utils/prompt_formatter.py
git add core/application/services/
git add tests/unit/shared/utils/test_prompt_formatter.py
git commit -m "refactor(llm): extract prompt formatting to shared utility

No functional changes. Reduces code duplication by 45 lines.
Coverage remains at 85%."

git push origin refactor/llm-service-cleanup
```

---

## 🚨 Anti-patterns à éviter absolument

### ❌ God Classes

```python
# ❌ MAUVAIS
class AppManager:
    """Fait tout à la fois"""
    def handle_websocket(self): ...
    def run_llm(self): ...
    def save_to_database(self): ...
    def send_email(self): ...
    def log(self): ...
    # 500 lignes de code...
```

### ❌ Tight Coupling

```python
# ❌ MAUVAIS
class WeatherService:
    def __init__(self):
        self.api = OpenWeatherMapAPI()  # Couplage fort
        self.db = PostgresDatabase()
```

### ❌ Magic Strings

```python
# ❌ MAUVAIS
if user.role == "admin":  # Qu'est-ce que "admin" ?
    ...
if status == "pending":  # Typo risk
    ...
```

### ❌ Mutable Globals

```python
# ❌ MAUVAIS
CURRENT_USER = None  # Global mutable

def login(user):
    global CURRENT_USER
    CURRENT_USER = user  # État partagé dangereux
```

### ❌ Silent Failures

```python
# ❌ MAUVAIS
try:
    risky_operation()
except:
    pass  # Erreur silencieuse

# OU
def get_user(user_id):
    try:
        return db.find(user_id)
    except:
        return None  # Masque l'erreur réelle
```

---

## 📚 Ressources

### Python
- [PEP 8](https://pep8.org/) - Style guide
- [PEP 257](https://www.python.org/dev/peps/pep-0257/) - Docstring conventions
- [mypy](https://mypy.readthedocs.io/) - Type checking
- [pytest](https://docs.pytest.org/) - Testing framework

### Rust
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [clippy](https://github.com/rust-lang/rust-clippy) - Linter
- [cargo-tarpaulin](https://github.com/xd009642/tarpaulin) - Coverage

### Clean Architecture
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

### Git
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

## ✅ Checklist finale avant commit

- [ ] Code respecte les conventions de nommage
- [ ] Toutes les fonctions ont des docstrings
- [ ] Types annotés partout (Python) ou compile (Rust)
- [ ] Pas de magic numbers/strings
- [ ] Pas de code dupliqué (DRY)
- [ ] Fonctions < 20 lignes (idéalement)
- [ ] Tests unitaires ajoutés (AAA pattern)
- [ ] Coverage ≥ 80%
- [ ] Tous les tests passent (`pytest` / `cargo test`)
- [ ] Linting passe (`black`, `flake8`, `clippy`)
- [ ] Type checking passe (`mypy` / `rustc`)
- [ ] Logs structurés utilisés pour erreurs
- [ ] Pas de secrets dans le code
- [ ] Commit message respecte Conventional Commits
- [ ] Documentation mise à jour si nécessaire

---

**Version** : 1.0.0  
**Dernière mise à jour** : 6 janvier 2026  
**Maintenu par** : Alexandre (Projet Hive Mind)
