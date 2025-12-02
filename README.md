# 🎯 Projet RAG GLPI - Assistant IT Helpdesk avec IA

Application web complète de RAG (Retrieval-Augmented Generation) pour un helpdesk IT :
- 🤖 **IA locale** : Mistral via Ollama (génération) + nomic-embed-text (embeddings 768D)
## 🚀 Installation rapide avec Docker (recommandé)

### Prérequis
- Docker Desktop installé et lancé
- Au moins 8 GB de RAM disponibles pour Docker

### Démarrage en 3 étapes

```zsh
# 1. Lancer tous les services
docker-compose up -d

# 2. Télécharger les modèles Ollama (première fois seulement)
docker exec -it ollama_service ollama pull mistral
docker exec -it ollama_service ollama pull nomic-embed-text

# 3. Accéder à l'application
open http://localhost:8000
```

**C'est tout ! L'application est prête.** 🎉

---

## 📦 Services Docker

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:8000 | Interface chat |
| **API** | http://localhost:8000/docs | Documentation Swagger |
| **PostgreSQL** | localhost:5432 | Base de données (user/password) |
| **Ollama** | http://localhost:11434 | Service LLM local |

---

## 💻 Installation manuelle (sans Docker)

### 1. Installer Ollama
```zsh
# macOS
brew install ollama
ollama serve  # Dans un terminal séparé

# Télécharger les modèles
ollama pull mistral
ollama pull nomic-embed-text
```

### 2. PostgreSQL avec pgvector
```sql
CREATE DATABASE mydatabase;
\c mydatabase
CREATE EXTENSION vector;
```

### 3. Backend Python
```zsh
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Variables d'environnement
export DATABASE_URL="postgresql://user:password@localhost/mydatabase"
export OLLAMA_HOST="http://localhost:11434"

# Lancer
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Le frontend sera accessible sur http://localhost:8000

---

## 🎯 Utilisation

### Interface web
1. Ouvrir http://localhost:8000
2. Entrer un User AD ID (ex: 1)
3. Poser une question IT

### Questions de test
- "Comment me connecter au VPN ?"
- "Mon imprimante ne fonctionne pas"
- "J'ai oublié mon mot de passe"
- "Outlook est très lent"
- "Comment accéder au dossier partagé ?"

### API REST
```zsh
# Statistiques GLPI
curl http://localhost:8000/glpi/stats

# Poser une question
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"user_ad_id": 1, "question": "Comment configurer le VPN ?"}'
```

**Réponse attendue :**
```json
{
  "question": "Comment configurer le VPN ?",
  "answer": "Pour configurer le VPN, suivez...",
  "sources": [
    {"type": "kb_article", "id": 1, "title": "Configuration VPN - Guide complet"},
    {"type": "faq", "id": 3, "title": "Comment accéder au VPN en télétravail ?"}
  ]
}
```

---

## 📚 Données GLPI mockées

Le système contient des données de démonstration réalistes :
- ✅ **8 tickets** IT résolus (VPN, imprimante, mots de passe, Outlook, etc.)
- ✅ **3 articles** de base de connaissances (guides détaillés)
- ✅ **5 items FAQ** (questions fréquentes)

Fichier : `backend/app/glpi_mock.py`

### Endpoints disponibles
```zsh
# Stats globales
curl http://localhost:8000/glpi/stats

# Aperçu par type
curl http://localhost:8000/glpi/preview/tickets
curl http://localhost:8000/glpi/preview/kb_articles
curl http://localhost:8000/glpi/preview/faq
```

---

## 🏗️ Architecture RAG

```
Question utilisateur
       ↓
   Recherche GLPI mock
   (scoring par mots-clés)
       ↓
   Top 4 sources pertinentes
       ↓
   Contexte + Question → Mistral
       ↓
   Réponse + Sources
       ↓
   Sauvegarde PostgreSQL (avec embedding)
```

### Composants
1. **Frontend** : HTML/CSS/JS épuré, chat synchrone
2. **Backend** : FastAPI avec endpoints `/ask/` et `/glpi/*`
3. **RAG** : Recherche dans données GLPI + génération Mistral
4. **Base** : PostgreSQL avec pgvector (embeddings 768D)
5. **LLM** : Ollama local (mistral + nomic-embed-text)

---

## 🔧 Commandes Docker utiles

```zsh
# Voir les logs
docker-compose logs -f api      # Backend
docker-compose logs -f ollama   # Ollama
docker-compose logs -f db       # PostgreSQL

# Redémarrer un service
docker-compose restart api

# Arrêter tout
docker-compose down

# Tout supprimer (y compris volumes)
docker-compose down -v

# Reconstruire après modification
docker-compose up --build

# Accéder à un conteneur
docker exec -it fastapi_api bash
docker exec -it postgres_db psql -U user -d mydatabase
docker exec -it ollama_service ollama list
```

---

## 🧪 Tests

### Script de test automatisé
```zsh
python3 test_rag.py
```

### Tests manuels
```zsh
# 1. Vérifier PostgreSQL
docker exec -it postgres_db psql -U user -d mydatabase -c "SELECT version();"

# 2. Vérifier Ollama
docker exec -it ollama_service ollama list

# 3. Tester l'API
curl http://localhost:8000/glpi/stats

# 4. Tester une question
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"user_ad_id": 1, "question": "Comment configurer le VPN ?"}'
```

---

## 📁 Structure du projet

```
projet_rag/
├── backend/
│   ├── app/
│   │   ├── main.py           # API FastAPI
│   │   ├── llm.py            # Intégration Ollama + RAG
│   │   ├── database.py       # PostgreSQL
│   │   ├── models.py         # SQLModel (Question, Reponse)
│   │   └── glpi_mock.py      # Données GLPI mockées
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── docker-compose.yml
├── test_rag.py               # Tests automatisés
└── README.md                 # Ce fichier
```

---

## 🔄 Migration vers GLPI réel

Actuellement, les données sont mockées. Pour connecter une vraie instance GLPI :

### 1. Créer le connecteur
```python
# backend/app/glpi_connector.py
import requests

class GLPIConnector:
    def __init__(self, api_url, app_token, user_token):
        self.api_url = api_url
        self.headers = {
            "App-Token": app_token,
            "Session-Token": user_token
        }
    
    def search_tickets(self, query):
        # Utiliser l'API REST GLPI
        # GET /search/Ticket
        pass
```

### 2. Remplacer dans llm.py
```python
# Avant
from .glpi_mock import glpi_mock

# Après
from .glpi_connector import GLPIConnector
glpi = GLPIConnector(api_url, app_token, user_token)
```

### 3. Configuration
Ajouter dans `docker-compose.yml` :
```yaml
environment:
  - GLPI_API_URL=https://your-glpi.com/apirest.php
  - GLPI_APP_TOKEN=your_app_token
  - GLPI_USER_TOKEN=your_user_token
```

**Documentation API GLPI** : https://github.com/glpi-project/glpi/blob/main/apirest.md

---

## 🐛 Dépannage

### Docker ne démarre pas
```zsh
# Vérifier que Docker Desktop est lancé
docker ps

# Nettoyer et redémarrer
docker-compose down -v
docker-compose up --build
```

### Erreur "expected 384 dimensions, not 768"
```zsh
# Recréer la base avec les bonnes dimensions
docker-compose down -v
docker-compose up
```

### Frontend ne s'affiche pas
Le frontend est servi par FastAPI. Vérifier :
```zsh
# Logs du backend
docker-compose logs api

# Le dossier frontend est bien monté ?
docker exec -it fastapi_api ls /app/frontend
```

### Ollama n'a pas les modèles
```zsh
docker exec -it ollama_service ollama pull mistral
docker exec -it ollama_service ollama pull nomic-embed-text
```

### API lente ou timeout
Première requête plus lente (chargement modèle). Ensuite normal. Ollama garde les modèles en cache.

---

## 🚀 Améliorations possibles

1. **Embeddings vectoriels** : Remplacer le scoring par mots-clés par une vraie recherche vectorielle
2. **Streaming** : Ajouter le streaming des réponses pour une meilleure UX
3. **API GLPI réelle** : Connecter à une vraie instance GLPI
4. **Recherche sémantique** : Utiliser pgvector pour chercher dans l'historique
5. **Interface admin** : Dashboard pour visualiser les données GLPI
6. **Feedback** : Système de notation des réponses pour améliorer le modèle
7. **Multi-langues** : Support anglais/français
8. **Auth** : Authentification utilisateur SSO/LDAP

---

## 📝 Variables d'environnement

### Docker (docker-compose.yml)
```yaml
DATABASE_URL: postgresql://user:password@db/mydatabase
OLLAMA_HOST: http://ollama:11434
```

### Manuel (backend/.env)
```bash
DATABASE_URL=postgresql://user:password@localhost/mydatabase
OLLAMA_HOST=http://localhost:11434
# Optionnel pour GLPI réel :
# GLPI_API_URL=https://your-glpi.com/apirest.php
# GLPI_APP_TOKEN=...
# GLPI_USER_TOKEN=...
```

---

## 📄 Licence & Contact

Projet académique M2 - 2025

**Technologies :**
- FastAPI 0.119.0
- PostgreSQL 16 + pgvector 0.4.1
- Ollama 0.13.0 (Mistral + nomic-embed-text)
- SQLModel 0.0.27
- Docker Compose

---

## ✨ Résumé rapide

**Démarrer l'application :**
```zsh
docker-compose up -d
docker exec -it ollama_service ollama pull mistral
docker exec -it ollama_service ollama pull nomic-embed-text
open http://localhost:8000
```

**Tester :**
```zsh
curl http://localhost:8000/glpi/stats
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"user_ad_id": 1, "question": "Comment configurer le VPN ?"}'
```

**Stopper :**
```zsh
docker-compose down
```

Voilà ! Vous avez un assistant IT helpdesk intelligent avec RAG fonctionnel ! 🎉 d'échec).

## Dépannage rapide
- Vérifier que `MISTRAL_API_KEY` est valide.
- Activer les logs (si disponible) pour tracer les requêtes.
- S'assurer que la branche locale est à jour: `git pull --rebase origin test_api_mistral`
