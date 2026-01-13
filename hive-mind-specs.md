# 🤖 Hive Mind - Assistant Vocal Distribué

## 📋 Vue d'ensemble du projet

**Hive Mind** est un système d'assistant vocal distribué avec une architecture client-serveur où :
- **Serveur "Hive Mind"** : Cerveau central hébergeant l'IA et les intégrations
- **Clients** : Interfaces vocales légères (PC, puis robots embarqués) partageant le même contexte conversationnel
- **Mode dégradé** : Fonctionnalités offline pour commandes basiques

---

## 🎯 Objectifs et contraintes

### Performances
- **Latence maximale** : 3 secondes (question → début de réponse)
- **IA** : CPU-only, lightweight (pas de GPU dédié)
- **Matériel cible** : Du PC au matériel embarqué (ESP32/Raspberry Pi Zero)

### Fonctionnalités
#### Mode connecté (serveur disponible)
- Compréhension vocale (STT) en français
- Réponses conversationnelles via IA
- Intégrations tierces (météo, Google Calendar, etc.)
- Actions multi-appareils
- Synthèse vocale (TTS)

#### Mode dégradé (serveur indisponible)
- Heure et date
- Chronomètre
- Minuteur
- Indicateur visuel (yeux jaunes vs blancs)

### Wake Word
- Activation vocale configurable : "Hey [nom du robot]"
- Par défaut paramétrable

---

## 🏗️ Architecture technique

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVEUR PYTHON (Hive Mind)               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  FastAPI Core                                           │ │
│  │  • WebSocket bidirectionnel                             │ │
│  │  • Context Manager (Redis)                              │ │
│  │  • Plugin Loader dynamique                              │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  LLM Engine                                             │ │
│  │  • Phi-3-mini-4k (3.8B params, Q4_K_M, ~2.3GB)         │ │
│  │  • llama-cpp-python (optimisations CPU AVX2)            │ │
│  │  • Streaming responses                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Plugin System                                          │ │
│  │  ├── weather/        (OpenWeatherMap API)               │ │
│  │  ├── calendar/       (Google Calendar OAuth2)           │ │
│  │  └── [plugin-template]/                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ WebSocket (Protocol JSON)
                          │
┌─────────────────────────┼─────────────────────────────────┐
│                    CLIENT RUST                             │
│  ┌───────────────────────────────────────────────────────┐│
│  │  Audio Pipeline                                        ││
│  │  • cpal (capture microphone cross-platform)            ││
│  │  • whisper.cpp (STT local, modèle base 74MB)          ││
│  │  • piper (TTS local haute qualité)                     ││
│  │  • porcupine (wake word "Hey [nom]")                   ││
│  └───────────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────────┐│
│  │  Core Logic                                            ││
│  │  • State Machine (connected/degraded)                  ││
│  │  • WebSocket client (tokio-tungstenite)                ││
│  │  • Local commands handler (time, timer, chrono)        ││
│  └───────────────────────────────────────────────────────┘│
│  ┌───────────────────────────────────────────────────────┐│
│  │  UI Layer                                              ││
│  │  • Desktop: egui (fenêtre avec yeux animés)            ││
│  │  • Embedded: embedded-graphics (futur)                 ││
│  │  • Eye colors: blanc=connecté, jaune=dégradé           ││
│  └───────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
```

### Réseau
- **Phase 1** : LAN uniquement (clients et serveur sur même réseau local)
- **Phase 2+** : Possibilité d'accès Internet via reverse proxy (optionnel)

### Contexte conversationnel
- **Scope** : Partagé entre tous les clients (single user)
- **Persistance** : Redis (7 jours rolling window)
- **Nettoyage** : Automatique chaque semaine
- **Format** : Historique messages + métadonnées (timestamp, client_id, intent)

---

## 🛠️ Stack technologique

### Serveur Python

#### Dépendances principales
```python
fastapi==0.109.0              # Framework web async
uvicorn[standard]==0.27.0     # ASGI server
llama-cpp-python==0.2.27      # Bindings llama.cpp optimisé CPU
pydantic==2.5.0               # Validation + schémas
redis==5.0.1                  # Context store
httpx==0.26.0                 # HTTP client async pour APIs
google-auth==2.27.0           # Google Calendar OAuth2
python-dotenv==1.0.0          # Config environment
```

#### Modèle IA : Phi-3-mini
- **Modèle** : `microsoft/Phi-3-mini-4k-instruct-gguf`
- **Quantification** : Q4_K_M (2.3 GB)
- **RAM nécessaire** : 4-6 GB
- **Latence CPU** : ~1-2s pour 50 tokens (8 threads)
- **Raisons du choix** :
  - Optimisé pour edge computing
  - Excellent instruction-following
  - Support conversations multi-tours
  - Performance CPU exceptionnelle

#### Hébergement
- **Infrastructure** : Proxmox (serveur domestique)
- **Déploiement** : Docker Compose
  - Container serveur Python
  - Container Redis
  - Volume persistant pour modèles IA
- **Réseau** : Bridge Docker avec exposition port WebSocket

#### Architecture serveur

```
serveur/
├── core/
│   ├── __init__.py
│   ├── llm.py                 # Wrapper llama-cpp-python
│   ├── context.py             # Context manager (Redis)
│   ├── websocket.py           # Handler WebSocket
│   ├── plugin.py              # Base class Plugin
│   └── plugin_loader.py       # Dynamic plugin loading
├── plugins/
│   ├── __init__.py
│   ├── weather/
│   │   ├── __init__.py
│   │   ├── plugin.json        # Manifest
│   │   ├── handler.py         # Logique métier
│   │   └── tests/
│   ├── calendar/
│   │   └── ...
│   └── _template/             # Template pour nouveaux plugins
│       ├── plugin.json
│       └── handler.py
├── main.py                    # Point d'entrée FastAPI
├── config.py                  # Configuration centralisée
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── tests/
    └── ...
```

---

### Client Rust

#### Dépendances Cargo
```toml
[dependencies]
# Async runtime
tokio = { version = "1.35", features = ["full"] }
tokio-tungstenite = "0.21"

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Audio pipeline
cpal = "0.15"                  # Cross-platform audio I/O
whisper-rs = "0.10"            # Bindings whisper.cpp
hound = "3.5"                  # WAV encoding/decoding

# Wake word detection
pv-porcupine = "2.2"           # Picovoice wake word

# TTS
tts = "0.26"                   # Rust TTS wrapper (espeak backend)
# Note: Migration vers piper prévue en Phase 2

# UI Desktop
eframe = "0.25"                # egui framework
egui = "0.25"

# Logging & errors
tracing = "0.1"
tracing-subscriber = "0.3"
anyhow = "1.0"
thiserror = "1.0"

# Configuration
config = "0.13"
dotenv = "0.15"
```

#### Architecture client

```
client/
├── src/
│   ├── main.rs                # Entry point
│   ├── core/
│   │   ├── mod.rs
│   │   ├── audio.rs           # Audio pipeline (STT/TTS/wake word)
│   │   ├── websocket.rs       # Client WebSocket
│   │   ├── state.rs           # State machine (connected/degraded)
│   │   └── commands.rs        # Local commands (time, timer, etc.)
│   ├── ui/
│   │   ├── mod.rs
│   │   ├── desktop.rs         # Desktop UI (egui)
│   │   ├── eyes.rs            # Eye animation component
│   │   └── embedded.rs        # Futur: embedded displays
│   ├── platform/
│   │   ├── mod.rs
│   │   ├── desktop.rs         # Platform-specific (Windows/Linux)
│   │   └── embedded.rs        # Futur: ESP32/RasPi
│   └── config.rs              # Configuration
├── assets/
│   ├── whisper-base.bin       # Modèle Whisper (74MB)
│   ├── porcupine_params.pv    # Wake word model
│   └── config.toml
├── Cargo.toml
└── tests/
    └── ...
```

---

## 🔌 Système de plugins (Serveur)

### Convention standardisée

Chaque plugin doit respecter :

#### 1. Structure de dossier
```
plugins/<nom_plugin>/
├── __init__.py
├── plugin.json           # Manifest (métadonnées)
├── handler.py            # Classe héritant de Plugin
└── tests/
    └── test_<nom>.py
```

#### 2. Manifest `plugin.json`
```json
{
  "name": "weather",
  "version": "1.0.0",
  "description": "Récupère les informations météorologiques",
  "triggers": ["météo", "weather", "température", "temps qu'il fait"],
  "intents": ["get_weather", "get_forecast"],
  "config": {
    "api_key_env": "OPENWEATHER_API_KEY",
    "default_location": "Belfort, FR"
  },
  "dependencies": ["httpx"],
  "enabled": true
}
```

#### 3. Interface Python (base class)
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class Plugin(ABC):
    """Base class pour tous les plugins Hive Mind"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def execute(self, intent: str, params: Dict) -> Dict:
        """
        Exécute l'action du plugin
        
        Args:
            intent: Nom de l'intent (ex: "get_weather")
            params: Paramètres extraits par l'IA
        
        Returns:
            Dict contenant le résultat de l'action
        """
        pass
    
    @abstractmethod
    def get_prompt_context(self) -> str:
        """
        Retourne le contexte à injecter dans le prompt LLM
        Décrit les capabilities du plugin à l'IA
        """
        pass
    
    async def on_load(self) -> None:
        """Hook appelé au chargement du plugin"""
        pass
    
    async def on_unload(self) -> None:
        """Hook appelé au déchargement du plugin"""
        pass
```

#### 4. Exemple concret : Plugin météo

```python
# plugins/weather/handler.py
import httpx
from core.plugin import Plugin

class WeatherPlugin(Plugin):
    async def execute(self, intent: str, params: Dict) -> Dict:
        if intent == "get_weather":
            location = params.get("location", self.config["default_location"])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": location,
                        "appid": self.config["api_key"],
                        "units": "metric",
                        "lang": "fr"
                    }
                )
                data = response.json()
                
                return {
                    "success": True,
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "location": location
                }
        
        elif intent == "get_forecast":
            # Implémentation forecast 5 jours
            pass
    
    def get_prompt_context(self) -> str:
        return """Tu as accès à la fonction 'get_weather' pour obtenir la météo actuelle.
        Paramètres :
        - location (optionnel) : ville, défaut = Belfort, FR
        
        Retourne : température, ressenti, description, humidité
        
        Exemple d'appel : {"intent": "get_weather", "params": {"location": "Paris"}}
        """
```

### Chargement dynamique des plugins

Le serveur scanne `plugins/` au démarrage et hot-reload si fichier modifié :
```python
# core/plugin_loader.py
import importlib
import json
from pathlib import Path
from typing import Dict
from core.plugin import Plugin

class PluginLoader:
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self.loaded_plugins: Dict[str, Plugin] = {}
    
    async def load_all(self):
        """Charge tous les plugins depuis plugins/"""
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith("_"):
                await self.load_plugin(plugin_dir.name)
    
    async def load_plugin(self, name: str):
        """Charge un plugin spécifique"""
        plugin_path = self.plugins_dir / name
        manifest_path = plugin_path / "plugin.json"
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        if not manifest.get("enabled", True):
            return
        
        # Import dynamique
        module = importlib.import_module(f"plugins.{name}.handler")
        plugin_class = getattr(module, f"{name.title()}Plugin")
        
        # Instanciation
        config = self._load_config(manifest)
        plugin_instance = plugin_class(config)
        await plugin_instance.on_load()
        
        self.loaded_plugins[name] = plugin_instance
```

---

## 🔄 Protocole de communication WebSocket

### Format des messages (JSON)

#### Client → Serveur

**1. Input vocal (transcription)**
```json
{
  "type": "voice_input",
  "transcription": "Quelle est la météo à Belfort ?",
  "timestamp": "2025-01-06T14:30:00Z",
  "client_id": "desktop-pc-001",
  "language": "fr"
}
```

**2. Heartbeat**
```json
{
  "type": "ping",
  "client_id": "desktop-pc-001",
  "state": "connected",  // ou "degraded"
  "timestamp": "2025-01-06T14:30:05Z"
}
```

**3. Confirmation d'action**
```json
{
  "type": "action_confirm",
  "action_id": "calendar_add_12345",
  "status": "success",
  "client_id": "desktop-pc-001"
}
```

#### Serveur → Client

**1. Réponse streaming (chunks)**
```json
{
  "type": "response_chunk",
  "content": "Il fait actuellement 8°C à Belfort",
  "is_final": false,
  "chunk_index": 0
}
```

```json
{
  "type": "response_chunk",
  "content": " avec un ciel nuageux et une humidité de 75%.",
  "is_final": true,
  "chunk_index": 1
}
```

**2. Demande d'action (plugin)**
```json
{
  "type": "action",
  "action_id": "calendar_add_12345",
  "plugin": "calendar",
  "action": "add_reminder",
  "params": {
    "title": "Appeler le dentiste",
    "datetime": "2025-01-08T10:00:00Z",
    "description": "Prendre RDV détartrage"
  },
  "response_text": "J'ai ajouté un rappel pour appeler le dentiste le 8 janvier à 10h."
}
```

**3. Notification d'erreur**
```json
{
  "type": "error",
  "code": "PLUGIN_UNAVAILABLE",
  "message": "Le plugin météo est temporairement indisponible",
  "recoverable": true
}
```

**4. Pong (heartbeat response)**
```json
{
  "type": "pong",
  "timestamp": "2025-01-06T14:30:05Z"
}
```

### Flow de communication typique

```
CLIENT                          SERVEUR
  │                                │
  │──────── connect ──────────────>│
  │<────── connected ──────────────│
  │                                │
  │── voice_input: "météo?" ──────>│
  │                                │──> LLM inference
  │                                │──> Détecte intent: get_weather
  │                                │──> Appel plugin weather
  │<─ response_chunk (streaming) ──│
  │<─ response_chunk (final) ──────│
  │                                │
  │──── ping (every 30s) ─────────>│
  │<─── pong ──────────────────────│
```

---

## 🎮 Commandes locales (Mode dégradé)

### Liste des commandes offline

Le client Rust doit gérer ces commandes sans connexion serveur :

| Commande | Exemples de déclenchement | Réponse |
|----------|---------------------------|---------|
| **Heure** | "Quelle heure est-il ?", "Il est quelle heure ?" | "Il est 14h30" |
| **Date** | "On est quel jour ?", "Quelle est la date ?" | "Nous sommes le mardi 6 janvier 2026" |
| **Chronomètre** | "Lance un chrono", "Démarre le chronomètre" | Démarre + affichage temps écoulé |
| **Stop chrono** | "Stop le chrono", "Arrête" | "Chronomètre arrêté à 2 minutes 34 secondes" |
| **Minuteur** | "Mets un minuteur de 5 minutes", "Timer 10 minutes" | Compte à rebours + alerte |
| **Annuler minuteur** | "Annule le minuteur", "Stop timer" | "Minuteur annulé" |

### Détection de pattern (Regex simplifiés)

```rust
// Exemples de patterns à implémenter
const PATTERNS: &[(&str, Command)] = &[
    (r"(?i)(quelle heure|il est quelle heure)", Command::GetTime),
    (r"(?i)(quel jour|quelle.*date)", Command::GetDate),
    (r"(?i)(lance|démarre|start).*chrono", Command::StartChrono),
    (r"(?i)(stop|arrête).*chrono", Command::StopChrono),
    (r"(?i)(minuteur|timer).*(\d+)\s*(minute|min)", Command::SetTimer),
];
```

### Indicateurs visuels

**États du client** (reflétés dans les "yeux") :
- 🟢 **Blanc** : Connecté au serveur, prêt
- 🟡 **Jaune** : Mode dégradé (serveur indisponible)
- 🔵 **Bleu pulsé** : En train d'écouter
- 🟣 **Violet** : Traitement en cours (STT ou attente réponse)
- 🔴 **Rouge** : Erreur critique

---

## 📅 Plan de développement

### Phase 1 : MVP Fonctionnel (2-3 semaines)

#### Semaine 1 : Serveur
- [ ] Setup Docker Compose (Python + Redis)
- [ ] FastAPI skeleton + WebSocket handler
- [ ] Intégration llama-cpp-python + téléchargement Phi-3-mini
- [ ] Context manager basique (Redis)
- [ ] Plugin loader + plugin météo (OpenWeatherMap)
- [ ] Tests unitaires core + plugin

**Livrable** : Serveur répond via WebSocket à des inputs texte simulés

#### Semaine 2 : Client Rust (partie 1)
- [ ] Setup projet Cargo + dépendances
- [ ] Audio pipeline : capture micro (cpal)
- [ ] Intégration Whisper (modèle base)
- [ ] WebSocket client (tokio-tungstenite)
- [ ] State machine (connected/degraded)
- [ ] Commandes locales (time, date, chrono, timer)

**Livrable** : Client capture voix, transcrit, envoie au serveur

#### Semaine 3 : Client Rust (partie 2) + Intégration
- [ ] TTS basique (espeak)
- [ ] UI desktop egui (fenêtre + yeux)
- [ ] Gestion reconnexion automatique
- [ ] Tests end-to-end complets
- [ ] Documentation déploiement

**Livrable** : Système fonctionnel bout-en-bout (vocal → réponse vocale)

---

### Phase 2 : Enrichissement (2 semaines)

#### Semaine 4 : Features avancées
- [ ] Plugin Google Calendar (OAuth2)
- [ ] Wake word detection (Porcupine)
- [ ] Amélioration TTS (migration vers piper)
- [ ] Logging structuré (tracing)
- [ ] Métriques performance (latence, uptime)

#### Semaine 5 : Polish & Optimisation
- [ ] Tests de charge (multiple clients)
- [ ] Optimisation latence LLM
- [ ] Interface configuration (UI settings)
- [ ] Documentation utilisateur finale

---

### Phase 3 : Embarqué (futur)

- [ ] Port client pour ESP32
- [ ] Port client pour Raspberry Pi
- [ ] Intégration écran physique (e-ink ou LCD)
- [ ] Boîtier robot imprimé 3D
- [ ] Alimentation batterie + gestion énergie
- [ ] Nouvelles intégrations (YouTube, Spotify, etc.)

---

## 🔧 Configuration requise

### Serveur (Proxmox VM/Container)
- **CPU** : 4 cores minimum (8 threads recommandé pour Phi-3)
- **RAM** : 8 GB minimum (6 GB pour modèle + 2 GB OS/services)
- **Stockage** : 10 GB (modèles + logs + Redis)
- **OS** : Ubuntu 22.04 LTS (Docker)

### Client Desktop (Phase 1)
- **OS** : Windows 10+ ou Linux (Ubuntu 22.04+)
- **RAM** : 2 GB minimum
- **Audio** : Microphone + haut-parleurs/casque
- **Stockage** : 200 MB (binaire + modèles)

### Client Embarqué (Phase 3)
- **Hardware** : ESP32 (4MB RAM) ou Raspberry Pi Zero 2 W
- **Audio** : Module I2S (INMP441 mic + MAX98357A amp)
- **Display** : e-ink 2.13" ou LCD 128x64
- **Alimentation** : 5V 2A minimum

---

## 🔐 Sécurité & Vie privée

### Principes
- **Données vocales** : Jamais stockées, traitement en mémoire uniquement
- **Contexte** : Chiffré au repos dans Redis (TLS)
- **APIs tierces** : Credentials en variables d'environnement
- **Réseau** : Phase 1 = LAN only (pas d'exposition Internet)

### Authentification (Phase 2+)
- Token JWT pour authentifier les clients
- Rotation automatique tous les 7 jours

---

## 📊 Métriques & Monitoring

### KPIs à tracker
- **Latence end-to-end** : Temps entre fin de parole et début réponse
- **Uptime serveur** : Disponibilité du Hive Mind
- **Taux de reconnexion** : Fréquence passage mode dégradé
- **Précision STT** : Word Error Rate (manuel sampling)
- **Usage plugins** : Fréquence appels par plugin

### Outils
- Logs structurés (JSON) vers stdout
- Optionnel : Grafana + Prometheus (Phase 2)

---

## 🤝 Contribution & Extension

### Ajouter un nouveau plugin

1. Copier le template : `cp -r plugins/_template plugins/mon_plugin`
2. Éditer `plugin.json` (name, triggers, config)
3. Implémenter `handler.py` (hériter de `Plugin`)
4. Ajouter tests dans `tests/test_mon_plugin.py`
5. Restart serveur (hot-reload automatique)

### Adapter pour nouveau matériel

1. Créer module dans `client/src/platform/nouveau.rs`
2. Implémenter trait `Platform` :
   - `init_audio()` : Config I2S/ALSA
   - `init_display()` : Config écran
   - `power_management()` : Gestion veille
3. Compiler avec feature flag : `cargo build --features=nouveau`

---

## 📚 Ressources & Documentation

### Modèles IA
- [Phi-3 sur Hugging Face](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)
- [llama.cpp documentation](https://github.com/ggerganov/llama.cpp)

### Audio
- [Whisper modèles](https://github.com/openai/whisper#available-models-and-languages)
- [Piper TTS](https://github.com/rhasspy/piper)
- [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/)

### APIs
- [OpenWeatherMap API](https://openweathermap.org/api)
- [Google Calendar API](https://developers.google.com/calendar/api/guides/overview)

---

## 🐛 Troubleshooting commun

### Serveur ne démarre pas
- Vérifier RAM disponible : `free -h` (besoin 6GB+)
- Vérifier modèle téléchargé : `ls -lh models/`
- Logs Docker : `docker-compose logs -f`

### Client ne se connecte pas
- Vérifier serveur accessible : `telnet <server_ip> 8000`
- Vérifier WebSocket endpoint dans config client
- Logs client : niveau `RUST_LOG=debug`

### Latence élevée (>3s)
- Vérifier CPU usage serveur : `htop`
- Réduire `n_ctx` dans config LLM (4096 → 2048)
- Vérifier pas de swap : `swapon --show`

### STT imprécis
- Vérifier qualité micro (SNR > 20dB)
- Augmenter modèle Whisper (base → small)
- Ajuster paramètres VAD (Voice Activity Detection)

---

## 📝 Notes de design importantes

### Pourquoi Python pour le serveur ?
- Écosystème IA mature (transformers, llama-cpp-python)
- Itération rapide sur prompts et plugins
- Bindings performants vers C++ (llama.cpp)

### Pourquoi Rust pour les clients ?
- Binaire unique, zéro dépendances runtime
- Performance critique pour STT/TTS en temps réel
- Écosystème embarqué mature (embedded-hal)
- Safety garanties (pas de crashes aléatoires)

### Pourquoi Redis et pas SQLite ?
- Persistence + performance pour contexte partagé
- Pub/Sub natif (futur : broadcast entre clients)
- TTL automatique (nettoyage contexte)
- Scalabilité (futur : multiple serveurs)

### Pourquoi Phi-3 et pas Llama/Mistral ?
- Optimisé spécifiquement pour edge computing
- Meilleur instruction-following à taille équivalente
- Support natif llama.cpp (GGUF)
- Latence CPU mesurée plus faible

---

## 🎯 Checklist démarrage projet

### Avant de commencer
- [ ] Proxmox opérationnel (VM ou LXC préparée)
- [ ] Docker + Docker Compose installés
- [ ] Rust toolchain installé (rustup)
- [ ] Compte OpenWeatherMap (API key gratuite)
- [ ] Credentials Google Cloud (Calendar API)

### Fichiers à créer en priorité
1. `docker-compose.yml` (serveur + Redis)
2. `serveur/requirements.txt`
3. `serveur/main.py` (skeleton FastAPI)
4. `client/Cargo.toml`
5. `client/src/main.rs` (skeleton)

### Première validation
- [ ] Serveur répond sur `http://localhost:8000/health`
- [ ] WebSocket accepte connexion : `ws://localhost:8000/ws`
- [ ] Client compile : `cargo build --release`
- [ ] Whisper transcrit audio : test avec fichier WAV

---

## 🚀 Commande de démarrage rapide

### Serveur (Docker)
```bash
cd serveur/
docker-compose up -d
docker-compose logs -f  # Voir les logs
```

### Client (Rust)
```bash
cd client/
cargo run --release
```

### Télécharger modèles
```bash
# Serveur : Phi-3-mini
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf \
  -O serveur/models/phi3-mini-q4.gguf

# Client : Whisper base
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin \
  -O client/assets/whisper-base.bin
```

---

## 📞 Contact & Support

**Développeur principal** : Alexandre  
**Contexte** : Projet ALISON++ / SINERGIES Lab (UTBM)  
**Localisation** : Belfort, France

---

## 📄 License

À définir (usage personnel / recherche académique pour l'instant)

---

**Dernière mise à jour** : 6 janvier 2026  
**Version du document** : 1.0.0
