# 🎯 Projet RAG GLPI - Assistant IT Helpdesk avec IA

Application web de RAG (Retrieval-Augmented Generation) pour un helpdesk IT avec IA locale.

## 🚀 Installation rapide avec Docker

### Prérequis
- Docker Desktop installé
- Au moins 8 GB de RAM disponibles

### Démarrage

```bash
# Lancer tous les services
docker-compose up -d

# Télécharger les modèles Ollama (première fois)
docker exec -it ollama_service ollama pull mistral
docker exec -it ollama_service ollama pull nomic-embed-text

# Accéder à l'application
open http://localhost:8000
```

---

## 📦 Services

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:8000 | Interface chat |
| **API** | http://localhost:8000/glpi/preview/* | Endpoints REST |
| **PostgreSQL** | localhost:5432 | Base de données |
| **Ollama** | http://localhost:11434 | LLM local |

---

## 💻 Installation manuelle (sans Docker)

### 1. Installer Ollama
```bash
brew install ollama
ollama serve
ollama pull mistral
ollama pull nomic-embed-text
```

### 2. Backend Python
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL="postgresql://user:password@localhost/mydatabase"
export OLLAMA_HOST="http://localhost:11434"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

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

### API REST
```bash
# Aperçu des données GLPI
curl http://localhost:8000/glpi/preview/tickets
curl http://localhost:8000/glpi/preview/kb_articles
curl http://localhost:8000/glpi/preview/faq

# Poser une question
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"user_ad_id": 1, "question": "Comment configurer le VPN ?"}'

# Envoyer un feedback
curl -X POST http://localhost:8000/feedback/ \
  -H "Content-Type: application/json" \
  -d '{"response_id": 1, "is_valid": true}'
```

---

## 🧪 Tests

### Lancer les tests unitaires
```bash
cd backend
pip install pytest pytest-cov httpx
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Résultats attendus
- **54 tests** passés
- **67% de couverture** de code

### Fichiers de tests
| Fichier | Description |
|---------|-------------|
| `test_api.py` | Endpoints API |
| `test_models.py` | Modèles SQLModel |
| `test_glpi_mock.py` | Données GLPI |
| `test_llm.py` | Parsing LLM |
| `test_init_techniciens.py` | Techniciens |

---

## 🔄 CI/CD

Pipeline GitHub Actions automatique sur push vers `main` :
1. **Tests unitaires** avec pytest et coverage

### Configurer Docker Hub (optionnel)
Pour activer le build Docker automatique, ajouter dans GitHub Secrets :
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

---

## 📁 Structure du projet

```
projet_rag/
├── backend/
│   ├── app/
│   │   ├── main.py           
│   │   ├── llm.py            
│   │   ├── database.py       
│   │   ├── models.py         
│   │   ├── glpi_mock.py      
│   │   └── init_techniciens.py 
│   ├── tests/               
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── .github/workflows/
│   └── ci-cd.yml            
├── docker-compose.yml
└── README.md
```

---

## 🏗️ Architecture RAG

```
Question utilisateur
       ↓
   Recherche GLPI mock (scoring mots-clés)
       ↓
   Top 4 sources pertinentes
       ↓
   Contexte + Question → Mistral
       ↓
   Réponse + Sources + [CATEGORY:Technicien]
       ↓
   Sauvegarde PostgreSQL (avec embedding)
```

### Catégories de techniciens
Les questions sont automatiquement assignées à un technicien :
- Techniciens, Réseau, Métier, SharePoint, Exchange
- Campus numérique, Comptes, Cours en ligne
- Audiovisuel, Copieurs, Suivi de commande

---

## 🐛 Dépannage

### Docker ne démarre pas
```bash
docker-compose down -v
docker-compose up --build
```

### Ollama n'a pas les modèles
```bash
docker exec -it ollama_service ollama pull mistral
docker exec -it ollama_service ollama pull nomic-embed-text
```

### Tests échouent
```bash
cd backend
pip install -r requirements.txt pytest pytest-cov httpx
pytest tests/ -v
```

---

## 📝 Variables d'environnement

```bash
DATABASE_URL=postgresql://user:password@db/mydatabase
OLLAMA_HOST=http://ollama:11434
```

---

## 📄 Licence

Projet académique M2 - 2025

**Technologies** : FastAPI, PostgreSQL + pgvector, Ollama (Mistral), SQLModel, Docker
