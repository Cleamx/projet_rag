"""Module de clustering pour catégoriser automatiquement les tickets GLPI.

Ce module analyse le contenu d'un ticket (titre + description) et détermine
automatiquement sa catégorie pour l'assigner au bon technicien.
"""


def determine_category(text: str) -> str:
    """
    Détermine la catégorie d'un ticket basé sur son contenu.
    
    Utilise un système de scoring par mots-clés pour identifier
    la catégorie la plus probable.
    
    Args:
        text: Description complète du problème (titre + description)
        
    Returns:
        Catégorie détectée (ex: "Réseau", "Matériel", "Logiciel", etc.)
        
    Examples:
        >>> determine_category("Je ne peux pas me connecter au VPN")
        'Réseau'
        >>> determine_category("Mon imprimante HP ne répond plus")
        'Matériel'
        >>> determine_category("Word plante au démarrage")
        'Logiciel'
    """
    text_lower = text.lower()
    
    # Dictionnaire de mots-clés par catégorie
    categories = {
        "Réseau": [
            "vpn", "wifi", "wi-fi", "connexion", "internet", "réseau", 
            "proxy", "ethernet", "routeur", "switch", "lan", "wan",
            "ip", "dns", "ping", "accès réseau", "partage réseau",
            "serveur", "pare-feu", "firewall", "connexion internet"
        ],
        "Matériel": [
            "imprimante", "écran", "clavier", "souris", "ordinateur","vidéoprojecteur", 
            "pc", "laptop", "portable", "moniteur", "scanner", "webcam", 
            "casque", "micro", "enceinte", "usb", "hdmi", "câble", 
            "batterie", "chargeur", "disque dur", "ssd", "ram", "mémoire"
        ],
        "Logiciel": [
            "word", "excel", "powerpoint", "office", "teams", "zoom",
            "logiciel", "application", "programme", "installer",
            "installation", "mise à jour", "update", "licence", 
            "activation", "adobe", "chrome", "firefox", "edge"
        ],
        "Compte": [
            "mot de passe", "password", "login", "connexion", "compte",
            "authentification", "identifiant", "accès", "session",
            "oublié", "bloqué", "verrouillé", "reset", "réinitialiser",
            "active directory", "ad", "utilisateur"
        ],
        "Messagerie": [
            "email", "e-mail", "mail", "outlook", "messagerie", "courrier",
            "boîte", "inbox", "spam", "envoyer", "recevoir", 
            "pièce jointe", "calendrier", "rendez-vous", "meeting"
        ],
        "Système": [
            "windows", "mac", "linux", "système", "démarrage", "boot",
            "écran bleu", "bsod", "crash", "plantage", "lent", "ralenti",
            "virus", "antivirus", "malware", "mise à jour système",
            "redémarrage", "erreur système"
        ],
        "Accès": [
            "droits", "permissions", "accès refusé", "access denied",
            "dossier partagé", "partage", "lecteur", "drive", "onedrive",
            "sharepoint", "lecture seule", "écriture", "autorisation"
        ],
        "Téléphonie": [
            "téléphone", "mobile", "smartphone", "appel", "voip", 
            "standard", "numéro", "ligne", "sonnerie", "transfert",
            "messagerie vocale", "répondeur"
        ],
        "Base de données": [
            "base de données", "database", "sql", "mysql", "postgresql",
            "oracle", "requête", "table", "données", "backup", 
            "sauvegarde", "restauration"
        ]
    }
    
    # Score par catégorie (nombre de mots-clés trouvés)
    scores = {}
    for category, keywords in categories.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            scores[category] = score
    
    # Retourner la catégorie avec le meilleur score
    if scores:
        best_category = max(scores, key=scores.get)
        return best_category
    
    # Aucun mot-clé trouvé → catégorie par défaut
    return "Autre"


def get_technician_email(category: str) -> str:
    """
    Retourne l'email du technicien assigné selon la catégorie.
    
    Chaque catégorie est gérée par un technicien ou une équipe spécialisée.
    
    Args:
        category: Catégorie du ticket (ex: "Réseau", "Matériel")
        
    Returns:
        Email du technicien ou de l'équipe responsable
        
    Examples:
        >>> get_technician_email("Réseau")
        'tech.reseau@univ-corse.fr'
        >>> get_technician_email("Autre")
        'helpdesk@univ-corse.fr'
    """
    technician_mapping = {
        "Réseau": "tech.reseau@univ-corse.fr",
        "Matériel": "tech.materiel@univ-corse.fr",
        "Logiciel": "tech.logiciel@univ-corse.fr",
        "Compte": "tech.comptes@univ-corse.fr",
        "Messagerie": "tech.messagerie@univ-corse.fr",
        "Système": "tech.systeme@univ-corse.fr",
        "Accès": "tech.acces@univ-corse.fr",
        "Téléphonie": "tech.telephonie@univ-corse.fr",
        "Base de données": "tech.database@univ-corse.fr",
        "Autre": "helpdesk@univ-corse.fr"
    }
    
    return technician_mapping.get(category, "helpdesk@univ-corse.fr")


def get_priority(text: str) -> str:
    """
    Détermine la priorité d'un ticket basé sur des mots-clés d'urgence.
    
    Args:
        text: Description du problème
        
    Returns:
        Priorité: "Urgente", "Haute", "Moyenne", ou "Basse"
        
    Examples:
        >>> get_priority("URGENT : Serveur en panne !")
        'Urgente'
        >>> get_priority("Mon écran clignote de temps en temps")
        'Basse'
    """
    text_lower = text.lower()
    
    # Mots-clés par niveau de priorité
    urgent_keywords = [
        "urgent", "critique", "bloquant", "panne", "serveur down",
        "tout le monde", "production", "client", "immédiat"
    ]
    
    high_keywords = [
        "important", "rapidement", "asap", "prioritaire", "ne fonctionne plus",
        "complètement cassé", "impossible de travailler"
    ]
    
    low_keywords = [
        "quand vous pouvez", "pas urgent", "de temps en temps",
        "occasionnel", "mineur", "suggestion"
    ]
    
    # Vérifier la présence de mots-clés
    if any(kw in text_lower for kw in urgent_keywords):
        return "Urgente"
    
    if any(kw in text_lower for kw in high_keywords):
        return "Haute"
    
    if any(kw in text_lower for kw in low_keywords):
        return "Basse"
    
    # Par défaut : Moyenne
    return "Moyenne"


# Tests unitaires (optionnel, pour vérifier que ça marche)
if __name__ == "__main__":
    # Test des catégories
    test_cases = [
        ("Je ne peux pas me connecter au VPN", "Réseau"),
        ("Mon imprimante HP ne répond plus", "Matériel"),
        ("Word plante au démarrage", "Logiciel"),
        ("J'ai oublié mon mot de passe", "Compte"),
        ("Outlook ne reçoit plus mes emails", "Messagerie"),
        ("Écran bleu au démarrage de Windows", "Système"),
        ("Accès refusé au dossier partagé", "Accès"),
    ]
    
    print("🧪 Tests de catégorisation :")
    print("-" * 60)
    
    for description, expected_category in test_cases:
        detected = determine_category(description)
        status = "✅" if detected == expected_category else "❌"
        print(f"{status} '{description[:40]}...'")
        print(f"   Attendu: {expected_category}, Détecté: {detected}")
        print(f"   Technicien: {get_technician_email(detected)}")
        print(f"   Priorité: {get_priority(description)}")
        print()
