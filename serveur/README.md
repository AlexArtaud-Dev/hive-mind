# Hive Mind - Serveur Python

Assistant vocal distribué - Serveur central avec IA et intégrations

## Structure du projet

```
serveur/
├── core/                           # Coeur de l'application
│   ├── domain/                     # Couche domaine (logique métier)
│   │   ├── entities/               # Entités métier
│   │   ├── value_objects/          # Value objects immutables
│   │   └── interfaces/             # Interfaces (abstractions)
│   ├── application/                # Couche application (use cases)
│   │   ├── services/               # Services applicatifs
│   │   ├── commands/               # Commandes (CQRS)
│   │   └── queries/                # Requêtes (CQRS)
│   ├── infrastructure/             # Couche infrastructure (implémentations)
│   │   ├── repositories/           # Accès données
│   │   ├── external_apis/          # APIs externes
│   │   ├── database/               # Base de données
│   │   ├── llm/                    # Wrapper LLM (llama-cpp-python)
│   │   └── redis/                  # Context manager Redis
│   └── presentation/               # Couche présentation (interfaces externes)
│       ├── websocket/              # Handler WebSocket
│       └── http/                   # Routes HTTP (health checks)
├── shared/                         # Code partagé entre couches
│   ├── constants/                  # Constantes
│   ├── enums/                      # Énumérations
│   ├── dtos/                       # Data Transfer Objects
│   ├── errors/                     # Erreurs personnalisées
│   ├── logging/                    # Logger structuré
│   ├── validators/                 # Validateurs d'input
│   └── utils/                      # Utilitaires
├── plugins/                        # Système de plugins dynamiques
│   └── _template/                  # Template pour nouveaux plugins
├── tests/                          # Tests
│   ├── unit/                       # Tests unitaires
│   │   ├── core/
│   │   ├── plugins/
│   │   └── shared/
│   └── integration/                # Tests d'intégration
├── models/                         # Modèles IA (Phi-3-mini)
├── main.py                         # Point d'entrée FastAPI
├── config.py                       # Configuration centralisée
├── requirements.txt                # Dépendances Python
├── Dockerfile                      # Image Docker
└── docker-compose.yml              # Orchestration (Python + Redis)
```

## Principes d'architecture

Cette architecture suit les principes **Clean Architecture** et **SOLID** :

- **Séparation des responsabilités** : Chaque couche a une responsabilité claire
- **Dependency Inversion** : Les couches internes ne dépendent pas des couches externes
- **Testabilité** : Code découplé, facilement testable
- **Extensibilité** : Ajout de plugins sans modification du core

## Installation

```bash
# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos clés API
```

## Démarrage

### Mode développement
```bash
python main.py
```

### Mode production (Docker)
```bash
docker-compose up -d
```

## Tests

```bash
# Tests unitaires
pytest tests/unit/

# Tests avec coverage
pytest --cov=core --cov=plugins --cov=shared --cov-report=html

# Vérifier coverage ≥ 80%
pytest --cov-fail-under=80
```

## Standards de code

Voir [Claude.md](../Claude.md) pour les conventions détaillées.

### Checklist avant commit
- [ ] Types annotés partout
- [ ] Docstrings Google Style
- [ ] Tests unitaires (AAA pattern)
- [ ] Coverage ≥ 80%
- [ ] `black --check serveur/`
- [ ] `mypy serveur/ --strict`
- [ ] `flake8 serveur/`

## License

À définir
