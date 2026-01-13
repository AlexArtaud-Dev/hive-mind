# Template de Plugin Hive Mind

Ce dossier sert de template pour créer de nouveaux plugins.

## Comment créer un nouveau plugin

1. **Copier le template**
   ```bash
   cp -r plugins/_template plugins/mon_plugin
   ```

2. **Éditer plugin.json**
   - Changer `name`, `description`, `triggers`, `intents`
   - Configurer les dépendances si nécessaire
   - Mettre `enabled: true`

3. **Éditer handler.py**
   - Renommer la classe (ex: `MonPlugin`)
   - Implémenter `execute()` avec votre logique
   - Mettre à jour `get_prompt_context()` pour décrire les capacités
   - Implémenter `on_load()` et `on_unload()` si nécessaire

4. **Tester le plugin**
   ```python
   from plugins.mon_plugin.handler import MonPlugin

   plugin = MonPlugin()
   result = await plugin.execute("mon_intent", {"param": "value"})
   print(result)
   ```

5. **Redémarrer le serveur**
   Le plugin sera chargé automatiquement au démarrage.

## Structure requise

```
plugins/mon_plugin/
├── plugin.json      # Manifest (obligatoire)
├── handler.py       # Implémentation (obligatoire)
├── README.md        # Documentation (optionnel)
└── tests/           # Tests (recommandé)
    └── test_mon_plugin.py
```

## Exemple : plugin.json

```json
{
  "name": "mon_plugin",
  "version": "1.0.0",
  "description": "Description de mon plugin",
  "triggers": ["mot-clé1", "mot-clé2"],
  "intents": ["action1", "action2"],
  "config": {
    "api_key_env": "MON_API_KEY",
    "timeout": 30
  },
  "dependencies": ["httpx", "beautifulsoup4"],
  "enabled": true
}
```

## Exemple : handler.py

```python
from core.domain.interfaces import PluginInterface

class MonPlugin(PluginInterface):
    async def execute(self, intent: str, params: dict) -> dict:
        if intent == "action1":
            # Votre logique ici
            return {"success": True, "data": "résultat"}

        return {"success": False, "error": "Intent inconnu"}

    def get_prompt_context(self) -> str:
        return "Description des capacités pour le LLM"

    def get_manifest(self) -> dict:
        # Retourner le contenu de plugin.json
        pass
```

## Bonnes pratiques

- ✅ Gérer les erreurs proprement (lever `PluginExecutionError`)
- ✅ Valider les paramètres d'entrée
- ✅ Retourner toujours `{"success": bool, ...}`
- ✅ Documenter les intents dans `get_prompt_context()`
- ✅ Tester le plugin avant de l'activer
- ✅ Utiliser des variables d'environnement pour les secrets (API keys)
- ❌ Ne jamais stocker de secrets dans le code

## Support

Voir la documentation complète dans `Claude.md`.
