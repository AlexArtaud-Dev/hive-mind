# 🤖 Hive Mind - Assistant Vocal Distribué

Système d'assistant vocal avec architecture client-serveur, IA locale (Phi-3) et intégrations tierces.

## 📁 Structure du projet

```
hive-mind/
├── serveur/              # Serveur Python (FastAPI + LLM + Plugins)
│   ├── core/             # Clean Architecture (domain, application, infrastructure, presentation)
│   ├── plugins/          # Système de plugins dynamiques
│   ├── shared/           # Code partagé (errors, logging, validators)
│   └── tests/            # Tests unitaires et d'intégration
├── client/               # Client Rust (Audio pipeline + UI) - À venir
├── Claude.md             # Guide de développement et standards
└── hive-mind-specs.md    # Spécifications complètes du projet
```

## 🎯 Vue d'ensemble

**Hive Mind** est un assistant vocal où:
- **Serveur** : Cerveau central avec IA (Phi-3-mini) et intégrations (météo, calendar, etc.)
- **Clients** : Interfaces vocales légères partageant le même contexte conversationnel
- **Mode dégradé** : Commandes offline (heure, chronomètre, minuteur) quand serveur indisponible

### Stack technique
- **Serveur** : Python 3.11+ • FastAPI • llama-cpp-python • Redis
- **Client** : Rust • Whisper.cpp (STT) • Piper (TTS) • egui (UI)
- **Déploiement** : Docker Compose • Proxmox

## 🚀 Démarrage rapide

### Serveur Python

```bash
cd serveur/

# Installation
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# Télécharger le modèle Phi-3-mini
mkdir -p models
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf \
  -O models/phi3-mini-q4.gguf

# Démarrage avec Docker
docker-compose up -d

# Ou sans Docker
python main.py
```

### Client Rust (à venir)

```bash
cd client/
cargo build --release
cargo run --release
```

## 📖 Documentation

- [Claude.md](./Claude.md) - Guide complet de développement (architecture, standards, workflow)
- [hive-mind-specs.md](./hive-mind-specs.md) - Spécifications techniques détaillées
- [serveur/README.md](./serveur/README.md) - Documentation du serveur Python

## 🧪 Tests

```bash
cd serveur/
pytest --cov=core --cov=plugins --cov=shared --cov-report=html
```

## 📅 Roadmap

- [x] Phase 1a : Structure serveur + configuration
- [ ] Phase 1b : LLM, Redis, Plugins, WebSocket
- [ ] Phase 1c : Client Rust (audio pipeline)
- [ ] Phase 2 : Wake word, Google Calendar, optimisations
- [ ] Phase 3 : Portage embarqué (ESP32, Raspberry Pi)

## 🤝 Contribution

Voir [Claude.md](./Claude.md) pour les standards de code et le workflow Git.

### Conventional Commits
```bash
feat(scope): description
fix(scope): description
docs(scope): description
```

## 📄 License

À définir (usage personnel / recherche académique)

---

**Développeur** : Alexandre
**Contexte** : Projet ALISON++ / SINERGIES Lab (UTBM)
**Localisation** : Belfort, France
