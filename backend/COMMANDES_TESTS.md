# 🧪 COMMANDES DE TEST - Tâche 2

Document de référence avec toutes les commandes pour tester le système de tickets et RAG.

---

## 🚀 Commandes Docker (démarrage)

### Démarrer l'application
```bash
cd C:\Users\abbou\Documents\assistant_IA\projet_rag

# Arrêter les services existants
docker-compose down

# Reconstruire l'API (après modification du code)
docker-compose build api

# Démarrer tous les services
docker-compose up -d

# Voir les logs en temps réel
docker-compose logs -f api
```

### Vérifier l'état des services
```bash
# Voir tous les conteneurs
docker-compose ps

# Doit afficher :
# postgres_db       Up
# ollama_service    Up
# fastapi_api       Up
```

---

## 🧪 TEST 1 : Workflow complet automatique ⭐

**Le test le plus important** - Teste tout d'un coup !

```bash
curl -X POST http://localhost:8000/test/complete-workflow
```

**Ce que ça fait** :
1. ✅ Crée un ticket "Problème VPN"
2. ✅ Le résout automatiquement
3. ✅ Ajoute la solution au RAG
4. ✅ Pose une question similaire
5. ✅ Vérifie que le RAG trouve la solution

**Résultat attendu** :
```json
{
  "success": true,
  "conclusion": "✅ Workflow complet fonctionnel !"
}
```

---

## 🧪 TEST 2 : Création de ticket manuel

### Exemple 1 : Problème VPN
```bash
curl -X POST http://localhost:8000/glpi/create-ticket ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 1, \"title\": \"Probleme VPN\", \"description\": \"Je ne peux pas me connecter au VPN depuis ce matin. Message erreur timeout.\"}"
```

**Résultat attendu** :
```json
{
  "success": true,
  "ticket_id": 1,
  "category": "Réseau",
  "priority": "Moyenne",
  "assigned_to": "tech.reseau@univ-corse.fr",
  "status": "Nouveau"
}
```

### Exemple 2 : Problème Imprimante
```bash
curl -X POST http://localhost:8000/glpi/create-ticket ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 1, \"title\": \"Imprimante en panne\", \"description\": \"L'imprimante du bureau 304 ne repond plus du tout. Les voyants sont eteints.\"}"
```

**Catégorie attendue** : "Matériel"

### Exemple 3 : Mot de passe oublié
```bash
curl -X POST http://localhost:8000/glpi/create-ticket ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 2, \"title\": \"Mot de passe oublie\", \"description\": \"J'ai oublie mon mot de passe Windows et je ne peux plus me connecter.\"}"
```

**Catégorie attendue** : "Compte"

### Exemple 4 : Outlook lent
```bash
curl -X POST http://localhost:8000/glpi/create-ticket ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 3, \"title\": \"Outlook tres lent\", \"description\": \"Outlook prend 5 minutes pour demarrer et la reception des emails est tres lente.\"}"
```

**Catégorie attendue** : "Messagerie"

### Exemple 5 : URGENT - Serveur down
```bash
curl -X POST http://localhost:8000/glpi/create-ticket ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 4, \"title\": \"URGENT - Serveur en panne\", \"description\": \"Le serveur de fichiers est completement inaccessible. Toute l'equipe est bloquee.\"}"
```

**Priorité attendue** : "Urgente"

---

## 🧪 TEST 3 : Webhook - Résolution de ticket 🔥

**⚠️ IMPORTANT** : Note le `ticket_id` retourné lors de la création du ticket !

### Résoudre le ticket VPN (ticket_id: 1)
```bash
curl -X POST http://localhost:8000/glpi/webhook/ticket-resolved ^
  -H "Content-Type: application/json" ^
  -d "{\"ticket_id\": 1, \"technician_name\": \"Jean Dupont\", \"solution\": \"Le probleme venait du pare-feu. J'ai ajoute une exception pour le client VPN. Veuillez redemarrer votre ordinateur et reessayer. Le VPN fonctionne maintenant.\"}"
```

### Résoudre le ticket Imprimante (ticket_id: 2)
```bash
curl -X POST http://localhost:8000/glpi/webhook/ticket-resolved ^
  -H "Content-Type: application/json" ^
  -d "{\"ticket_id\": 2, \"technician_name\": \"Marie Dupont\", \"solution\": \"L'imprimante etait simplement debranchee. J'ai rebranche le cable d'alimentation et redemarré l'imprimante. Tout fonctionne correctement maintenant.\"}"
```

### Résoudre le ticket Mot de passe (ticket_id: 3)
```bash
curl -X POST http://localhost:8000/glpi/webhook/ticket-resolved ^
  -H "Content-Type: application/json" ^
  -d "{\"ticket_id\": 3, \"technician_name\": \"Pierre Martin\", \"solution\": \"Mot de passe reinitialise via Active Directory. L'utilisateur peut maintenant se connecter avec le nouveau mot de passe temporaire envoye par email.\"}"
```

### Résoudre le ticket Outlook (ticket_id: 4)
```bash
curl -X POST http://localhost:8000/glpi/webhook/ticket-resolved ^
  -H "Content-Type: application/json" ^
  -d "{\"ticket_id\": 4, \"technician_name\": \"Sophie Lefebvre\", \"solution\": \"Probleme de cache Outlook trop volumineux. J'ai vide le cache, archive les anciens emails et optimise le fichier PST. Outlook demarre maintenant en 10 secondes.\"}"
```

**Résultat attendu** :
```json
{
  "success": true,
  "message": "Ticket résolu et solution ajoutée à la base RAG",
  "rag_entry": {
    "question_id": 5,
    "response_id": 5,
    "embedding_generated": true
  }
}
```

---

## 🧪 TEST 4 : Vérifier que le RAG trouve les solutions

**Après avoir résolu les tickets, teste si le RAG les trouve !**

### Question similaire au VPN
```bash
curl -X POST http://localhost:8000/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 10, \"question\": \"Mon VPN ne se connecte pas, j'ai un message d'erreur\"}"
```

**Résultat attendu** : Le RAG devrait trouver la solution de Jean Dupont

### Question similaire à l'imprimante
```bash
curl -X POST http://localhost:8000/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 11, \"question\": \"Mon imprimante ne marche plus, elle est eteinte\"}"
```

**Résultat attendu** : Le RAG devrait trouver la solution de Marie Dupont

### Question similaire au mot de passe
```bash
curl -X POST http://localhost:8000/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 12, \"question\": \"J'ai oublie mon mot de passe, comment le reinitialiser\"}"
```

**Résultat attendu** : Le RAG devrait trouver la solution de Pierre Martin

### Question similaire à Outlook
```bash
curl -X POST http://localhost:8000/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 13, \"question\": \"Outlook est tres lent au demarrage\"}"
```

**Résultat attendu** : Le RAG devrait trouver la solution de Sophie Lefebvre

---

## 🧪 TEST 5 : Consultation des tickets

### Voir tous les tickets d'un utilisateur
```bash
curl http://localhost:8000/glpi/tickets/1
```

**Résultat** : Liste de tous les tickets créés par user_ad_id: 1

### Voir les détails d'un ticket spécifique
```bash
curl http://localhost:8000/glpi/ticket/1
```

**Résultat** : Détails complets du ticket #1 (titre, description, solution, technicien, dates...)

### Voir tous les tickets (peu importe l'utilisateur)
```bash
# Via l'interface Swagger
http://localhost:8000/docs
```

---

## 🧪 TEST 6 : Statistiques

### Statistiques globales
```bash
curl http://localhost:8000/glpi/stats
```

**Résultat attendu** :
```json
{
  "total_tickets": 5,
  "resolved_tickets": 4,
  "pending_tickets": 1,
  "by_status": {
    "Nouveau": 1,
    "Résolu": 4
  },
  "by_category": {
    "Réseau": 2,
    "Matériel": 1,
    "Compte": 1,
    "Messagerie": 1
  },
  "rag_entries": 10
}
```

### Statistiques d'impact du RAG
```bash
curl http://localhost:8000/rag/impact-stats
```

**Résultat** : Taux de résolution automatique, tickets qui ont enrichi le RAG, etc.

---

## 🧪 TEST 7 : Aperçu des données GLPI mockées

### Voir les tickets mockés
```bash
curl http://localhost:8000/glpi/preview/tickets
```

### Voir les articles de base de connaissances
```bash
curl http://localhost:8000/glpi/preview/kb_articles
```

### Voir la FAQ
```bash
curl http://localhost:8000/glpi/preview/faq
```

---

## 🌐 TEST 8 : Interface Swagger (plus facile !)

**Ouvre dans ton navigateur** :
```
http://localhost:8000/docs
```

**Avantages** :
- ✅ Interface graphique
- ✅ Tester tous les endpoints en cliquant
- ✅ Voir les schémas de données
- ✅ Pas besoin de taper les commandes curl

---

## 🔄 SCÉNARIO COMPLET - Cycle de vie d'un ticket

**Copie-colle ces commandes une par une** :

```bash
# 1. Créer un ticket
curl -X POST http://localhost:8000/glpi/create-ticket ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 100, \"title\": \"Wifi ne marche pas\", \"description\": \"Le wifi est instable, deconnexions frequentes dans la salle B204\"}"

# Note le ticket_id retourné (exemple: 10)

# 2. Voir les détails du ticket créé
curl http://localhost:8000/glpi/ticket/10

# 3. Le technicien résout le ticket
curl -X POST http://localhost:8000/glpi/webhook/ticket-resolved ^
  -H "Content-Type: application/json" ^
  -d "{\"ticket_id\": 10, \"technician_name\": \"Alice Technicienne\", \"solution\": \"Point d'acces wifi defectueux en B204. J'ai remplace le materiel. Signal maintenant stable.\"}"

# 4. Vérifier que le ticket est résolu
curl http://localhost:8000/glpi/ticket/10

# 5. Poser une question similaire (nouveau utilisateur)
curl -X POST http://localhost:8000/ask/ ^
  -H "Content-Type: application/json" ^
  -d "{\"user_ad_id\": 200, \"question\": \"Le wifi ne marche pas en salle B204\"}"

# 6. Le RAG devrait trouver la solution d'Alice ! ✅
```

---

## 🧹 NETTOYAGE - Réinitialiser la base de données

**Si tu veux tout effacer et recommencer** :

```bash
# Arrêter et supprimer TOUT (y compris les volumes)
docker-compose down -v

# Relancer proprement
docker-compose build
docker-compose up -d

# La base de données est maintenant vide
```

---

## 📊 VÉRIFICATIONS RAPIDES

### Vérifier que Docker tourne
```bash
docker-compose ps
```

### Vérifier que l'API est accessible
```bash
curl http://localhost:8000/docs
```

### Vérifier que PostgreSQL fonctionne
```bash
docker exec -it postgres_db psql -U user -d mydatabase -c "SELECT COUNT(*) FROM glpiticket;"
```

### Vérifier que Ollama fonctionne
```bash
docker exec -it ollama_service ollama list
```

---

## 🐛 DÉPANNAGE

### L'API ne démarre pas
```bash
# Voir les logs d'erreur
docker-compose logs api

# Reconstruire proprement
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

### Erreur "ticket not found"
```bash
# Vérifier les tickets existants
curl http://localhost:8000/glpi/stats
```

### PostgreSQL connection error
```bash
# Vérifier que PostgreSQL est démarré
docker-compose ps
docker-compose logs db
```

---

## 📝 NOTES

### Format des commandes

**Windows CMD** : Utilise `^` pour les sauts de ligne
```bash
curl -X POST http://localhost:8000/endpoint ^
  -H "Content-Type: application/json" ^
  -d "{\"key\": \"value\"}"
```

**PowerShell** : Utilise `` ` `` pour les sauts de ligne
```powershell
curl -X POST http://localhost:8000/endpoint `
  -H "Content-Type: application/json" `
  -d "{\"key\": \"value\"}"
```

**Linux/Mac** : Utilise `\` pour les sauts de ligne
```bash
curl -X POST http://localhost:8000/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

---

## ⚡ COMMANDES RAPIDES - COPIE-COLLE

### Test complet en 30 secondes
```bash
# 1. Démarrer
docker-compose up -d

# 2. Tester tout
curl -X POST http://localhost:8000/test/complete-workflow

# 3. Voir les stats
curl http://localhost:8000/glpi/stats
```

### Créer + Résoudre + Tester (exemple VPN)
```bash
# Créer
curl -X POST http://localhost:8000/glpi/create-ticket -H "Content-Type: application/json" -d "{\"user_ad_id\": 1, \"title\": \"VPN KO\", \"description\": \"VPN ne marche pas timeout\"}"

# Résoudre (remplace ticket_id par celui retourné)
curl -X POST http://localhost:8000/glpi/webhook/ticket-resolved -H "Content-Type: application/json" -d "{\"ticket_id\": 1, \"technician_name\": \"Tech\", \"solution\": \"Pare-feu configure. Redemarrer PC.\"}"

# Tester RAG
curl -X POST http://localhost:8000/ask/ -H "Content-Type: application/json" -d "{\"user_ad_id\": 2, \"question\": \"VPN probleme\"}"
```

---

## 🎯 CHECKLIST DE TEST

Avant de présenter, vérifie que tous ces tests passent :

- [ ] `docker-compose ps` montre 3 services "Up"
- [ ] `http://localhost:8000/docs` s'ouvre
- [ ] Test workflow complet retourne `"success": true`
- [ ] Création de ticket retourne un `ticket_id`
- [ ] Webhook retourne `"embedding_generated": true`
- [ ] Question similaire trouve des sources
- [ ] Stats montrent le bon nombre de tickets

---

**Document créé le 9 décembre 2025**  
**Projet : Assistant IA - Helpdesk Université de Corse**  
**Développeur : Hafsa Abbou**
