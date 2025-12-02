"""
Module pour simuler les données GLPI (tickets, FAQ, KB articles)
En attendant la vraie connexion à GLPI
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random


class GLPIMockData:
    """Générateur de données GLPI mockées pour le RAG"""
    
    def __init__(self):
        self.tickets = self._generate_tickets()
        self.kb_articles = self._generate_kb_articles()
        self.faq_items = self._generate_faq_items()
    
    def _generate_tickets(self) -> List[Dict[str, Any]]:
        """Génère des tickets GLPI mockés"""
        ticket_templates = [
            {
                "title": "Problème de connexion VPN",
                "description": "Impossible de se connecter au VPN de l'entreprise depuis ce matin. Message d'erreur: timeout.",
                "solution": "Vérifier que le client VPN est à jour. Réinitialiser les paramètres réseau. Contacter le support si le problème persiste.",
                "category": "Réseau",
                "status": "Résolu",
                "priority": "Haute"
            },
            {
                "title": "Imprimante ne répond pas",
                "description": "L'imprimante du bureau 304 ne répond plus. Aucune impression n'est possible.",
                "solution": "Redémarrer l'imprimante et vérifier la connexion réseau. Réinstaller les pilotes si nécessaire.",
                "category": "Matériel",
                "status": "Résolu",
                "priority": "Moyenne"
            },
            {
                "title": "Mot de passe oublié",
                "description": "Utilisateur a oublié son mot de passe Active Directory et ne peut plus se connecter.",
                "solution": "Utiliser l'outil de réinitialisation en libre-service ou contacter le helpdesk pour un reset manuel.",
                "category": "Compte utilisateur",
                "status": "Résolu",
                "priority": "Haute"
            },
            {
                "title": "Écran bleu Windows",
                "description": "Écran bleu récurrent (BSOD) sur le poste de travail. Erreur MEMORY_MANAGEMENT.",
                "solution": "Tester la mémoire RAM avec memtest86. Remplacer les barrettes défectueuses. Mettre à jour les drivers.",
                "category": "Système",
                "status": "Résolu",
                "priority": "Haute"
            },
            {
                "title": "Demande de nouveau logiciel",
                "description": "Besoin d'installer Adobe Photoshop pour le service communication.",
                "solution": "Vérifier la licence disponible. Installer via le centre logiciel ou manuellement avec clé de licence.",
                "category": "Logiciel",
                "status": "En cours",
                "priority": "Moyenne"
            },
            {
                "title": "Sauvegarde échouée",
                "description": "La sauvegarde automatique du serveur de fichiers a échoué cette nuit.",
                "solution": "Vérifier l'espace disque disponible sur le NAS. Relancer la sauvegarde manuellement. Vérifier les logs.",
                "category": "Infrastructure",
                "status": "Résolu",
                "priority": "Haute"
            },
            {
                "title": "Messagerie lente",
                "description": "Outlook est très lent au démarrage et à la réception des emails.",
                "solution": "Archiver les anciens emails. Vider le cache Outlook. Réparer le profil si nécessaire.",
                "category": "Messagerie",
                "status": "Résolu",
                "priority": "Moyenne"
            },
            {
                "title": "Accès refusé au dossier partagé",
                "description": "Impossible d'accéder au dossier \\\\serveur\\partage\\compta",
                "solution": "Vérifier les permissions NTFS et les partages. Ajouter l'utilisateur au groupe approprié dans Active Directory.",
                "category": "Réseau",
                "status": "Résolu",
                "priority": "Moyenne"
            }
        ]
        
        tickets = []
        for i, template in enumerate(ticket_templates, 1):
            ticket = {
                "id": i,
                "title": template["title"],
                "description": template["description"],
                "solution": template["solution"],
                "category": template["category"],
                "status": template["status"],
                "priority": template["priority"],
                "created_date": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
                "resolved_date": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() if template["status"] == "Résolu" else None,
                "requester": f"user{i}@entreprise.com",
                "technician": f"tech{random.randint(1, 3)}@entreprise.com"
            }
            tickets.append(ticket)
        
        return tickets
    
    def _generate_kb_articles(self) -> List[Dict[str, Any]]:
        """Génère des articles de base de connaissances mockés"""
        articles = [
            {
                "id": 1,
                "title": "Configuration VPN - Guide complet",
                "content": """
# Configuration VPN Entreprise

## Windows
1. Télécharger le client Cisco AnyConnect depuis le portail intranet
2. Installer avec les droits administrateur
3. Configurer avec l'adresse: vpn.entreprise.com
4. Utiliser vos identifiants Active Directory

## macOS
1. Télécharger Cisco AnyConnect pour Mac
2. Installer le package DMG
3. Autoriser l'extension système dans Préférences Système > Sécurité
4. Se connecter avec vpn.entreprise.com

## Troubleshooting
- Vérifier la connexion internet
- Désactiver temporairement l'antivirus
- Vider le cache DNS: ipconfig /flushdns
- Contacter le support si erreur persiste
                """,
                "category": "Réseau",
                "views": 245,
                "last_updated": (datetime.now() - timedelta(days=15)).isoformat()
            },
            {
                "id": 2,
                "title": "Réinitialisation mot de passe",
                "content": """
# Procédure de réinitialisation de mot de passe

## En libre-service
1. Aller sur https://password.entreprise.com
2. Cliquer sur "Mot de passe oublié"
3. Répondre aux questions de sécurité
4. Définir un nouveau mot de passe

## Politique de mot de passe
- Minimum 12 caractères
- Au moins une majuscule, une minuscule, un chiffre
- Au moins un caractère spécial
- Pas de mots du dictionnaire
- Ne pas réutiliser les 5 derniers mots de passe

## Contact helpdesk
Si le reset en libre-service échoue, contacter:
- Email: helpdesk@entreprise.com
- Téléphone: +33 1 23 45 67 89
- Interne: poste 1234
                """,
                "category": "Compte utilisateur",
                "views": 523,
                "last_updated": (datetime.now() - timedelta(days=5)).isoformat()
            },
            {
                "id": 3,
                "title": "Optimisation Outlook",
                "content": """
# Guide d'optimisation d'Outlook

## Archivage automatique
1. Fichier > Outils > Nettoyer la boîte aux lettres
2. Configurer l'archivage automatique (6 mois recommandé)
3. Créer un fichier PST d'archive local

## Réduction de la taille
- Supprimer les pièces jointes volumineuses
- Vider les éléments supprimés régulièrement
- Utiliser OneDrive pour les gros fichiers

## Performance
- Désactiver les compléments inutiles
- Mode cache Exchange: 3 mois recommandé
- Compacter régulièrement le fichier OST

## Problèmes courants
- Outlook lent: Réparer le profil
- Erreurs de synchronisation: Recréer le profil
- Crash au démarrage: Démarrer en mode sans échec
                """,
                "category": "Messagerie",
                "views": 187,
                "last_updated": (datetime.now() - timedelta(days=30)).isoformat()
            }
        ]
        return articles
    
    def _generate_faq_items(self) -> List[Dict[str, Any]]:
        """Génère des items FAQ mockés"""
        faq = [
            {
                "id": 1,
                "question": "Comment changer mon mot de passe Windows ?",
                "answer": "Appuyez sur Ctrl+Alt+Suppr et sélectionnez 'Modifier le mot de passe'. Ou utilisez le portail en libre-service: https://password.entreprise.com",
                "category": "Compte",
                "popularity": 95
            },
            {
                "id": 2,
                "question": "Où trouver les pilotes d'imprimante ?",
                "answer": "Les pilotes sont disponibles sur l'intranet dans la section 'Ressources IT' ou sur \\\\serveur\\drivers\\imprimantes",
                "category": "Matériel",
                "popularity": 78
            },
            {
                "id": 3,
                "question": "Comment accéder au VPN en télétravail ?",
                "answer": "Utilisez Cisco AnyConnect avec l'adresse vpn.entreprise.com et vos identifiants habituels. Guide complet disponible sur l'intranet.",
                "category": "Réseau",
                "popularity": 89
            },
            {
                "id": 4,
                "question": "Quelle est la procédure pour demander un nouveau logiciel ?",
                "answer": "Créez un ticket dans GLPI en précisant le logiciel souhaité, l'usage prévu et la validation de votre manager.",
                "category": "Logiciel",
                "popularity": 65
            },
            {
                "id": 5,
                "question": "Comment configurer ma messagerie sur mobile ?",
                "answer": "Installez Microsoft Outlook sur votre mobile. Ajoutez votre adresse email professionnelle. Le profil Exchange se configurera automatiquement.",
                "category": "Messagerie",
                "popularity": 72
            }
        ]
        return faq
    
    def search_all(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche dans toutes les sources GLPI mockées
        Retourne une liste de documents avec leur contenu et métadonnées
        """
        results = []
        
        # Recherche dans les tickets
        for ticket in self.tickets:
            score = self._simple_score(query, ticket["title"] + " " + ticket["description"] + " " + ticket.get("solution", ""))
            if score > 0:
                results.append({
                    "source": "ticket",
                    "id": ticket["id"],
                    "title": ticket["title"],
                    "content": f"**Problème**: {ticket['description']}\n\n**Solution**: {ticket['solution']}",
                    "metadata": {
                        "category": ticket["category"],
                        "status": ticket["status"],
                        "priority": ticket["priority"]
                    },
                    "score": score
                })
        
        # Recherche dans les articles KB
        for article in self.kb_articles:
            score = self._simple_score(query, article["title"] + " " + article["content"])
            if score > 0:
                results.append({
                    "source": "kb_article",
                    "id": article["id"],
                    "title": article["title"],
                    "content": article["content"],
                    "metadata": {
                        "category": article["category"],
                        "views": article["views"]
                    },
                    "score": score
                })
        
        # Recherche dans la FAQ
        for faq in self.faq_items:
            score = self._simple_score(query, faq["question"] + " " + faq["answer"])
            if score > 0:
                results.append({
                    "source": "faq",
                    "id": faq["id"],
                    "title": faq["question"],
                    "content": f"**Question**: {faq['question']}\n\n**Réponse**: {faq['answer']}",
                    "metadata": {
                        "category": faq["category"],
                        "popularity": faq["popularity"]
                    },
                    "score": score
                })
        
        # Trier par score et limiter
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _simple_score(self, query: str, text: str) -> float:
        """Scoring simple basé sur la présence de mots-clés"""
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Score de base si le texte contient la requête complète
        if query_lower in text_lower:
            return 1.0
        
        # Score basé sur les mots individuels
        query_words = query_lower.split()
        matches = sum(1 for word in query_words if len(word) > 2 and word in text_lower)
        
        if len(query_words) == 0:
            return 0.0
        
        return matches / len(query_words)


# Instance globale pour réutilisation
glpi_mock = GLPIMockData()
