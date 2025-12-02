# Guide de test - RAG GLPI

## Comment tester le système

### 1. Vérifier qu'Ollama fonctionne

```zsh
# Vérifier les modèles installés
ollama list

# Si mistral ou nomic-embed-text ne sont pas là :
ollama pull mistral
ollama pull nomic-embed-text
```

### 2. Lancer le backend

```zsh
cd backend
source .venv/bin/activate  # ou .venv\Scripts\activate sur Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Tester les endpoints GLPI

```zsh
# Statistiques
curl http://localhost:8000/glpi/stats

# Exemple de réponse :
# {
#   "tickets_count": 8,
#   "kb_articles_count": 3,
#   "faq_items_count": 5,
#   "total_entries": 16
# }

# Voir les tickets mockés
curl http://localhost:8000/glpi/preview/tickets | python3 -m json.tool

# Voir les articles KB
curl http://localhost:8000/glpi/preview/kb_articles | python3 -m json.tool

# Voir la FAQ
curl http://localhost:8000/glpi/preview/faq | python3 -m json.tool
```

### 4. Tester une question avec RAG

```zsh
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_ad_id": 1,
    "question": "Comment configurer le VPN ?"
  }' | python3 -m json.tool
```

Réponse attendue :
```json
{
  "question": "Comment configurer le VPN ?",
  "answer": "Pour configurer le VPN...",
  "sources": [
    {
      "type": "kb_article",
      "id": 1,
      "title": "Configuration VPN - Guide complet",
      "metadata": {...}
    }
  ]
}
```

### 5. Questions de test recommandées

Ces questions devraient matcher avec les données GLPI mockées :

1. **VPN**
   - "Comment me connecter au VPN ?"
   - "Problème de connexion VPN"
   - "Le VPN ne fonctionne pas"

2. **Imprimante**
   - "Mon imprimante ne répond pas"
   - "L'imprimante ne marche pas"

3. **Mot de passe**
   - "J'ai oublié mon mot de passe"
   - "Comment changer mon mot de passe ?"
   - "Reset mot de passe"

4. **Outlook / Messagerie**
   - "Outlook est lent"
   - "Ma messagerie est lente"
   - "Comment optimiser Outlook ?"

5. **Accès réseau**
   - "Je n'arrive pas à accéder au dossier partagé"
   - "Accès refusé au partage réseau"

### 6. Vérifier les sources retournées

Chaque réponse devrait inclure les sources GLPI utilisées :
- Type de source (ticket, kb_article, faq)
- ID de la source
- Titre de la source
- Métadonnées (catégorie, statut, etc.)

### 7. Vérifier la base de données

Les questions et réponses sont enregistrées dans PostgreSQL :

```sql
-- Se connecter à la base
psql -U user -d mydatabase

-- Voir les questions
SELECT id, user_ad_id, question_label, created_at 
FROM question 
ORDER BY id DESC 
LIMIT 5;

-- Voir les réponses
SELECT r.id, q.question_label, r.reponse_label 
FROM reponse r 
JOIN question q ON r.question_id = q.id 
ORDER BY r.id DESC 
LIMIT 5;
```

### Dépannage

#### Erreur : "Impossible de résoudre l'importation"
Solution : Installer les dépendances
```zsh
pip install -r backend/requirements.txt
```

#### Erreur : Ollama non accessible
Solution : Vérifier qu'Ollama tourne
```zsh
ollama serve
```

#### Erreur : PostgreSQL connection refused
Solution : Vérifier que PostgreSQL est lancé et accessible
```zsh
# macOS avec Homebrew
brew services start postgresql

# Ou avec Docker
docker-compose up db
```

#### Pas de réponse GLPI
Vérifier que `backend/app/glpi_mock.py` existe et contient les données mockées.

### Logs utiles

Le backend affiche des logs pour le debugging :
- Requêtes entrantes
- Temps de réponse Ollama
- Sources GLPI trouvées
- Erreurs SQL

### Prochaines étapes

1. Tester toutes les questions d'exemple
2. Vérifier que les sources sont pertinentes
3. Ajuster le scoring si nécessaire dans `glpi_mock.py`
4. Préparer la migration vers la vraie API GLPI
