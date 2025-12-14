"""
Module de connexion avec GLPI réel via API REST
Documentation API GLPI : https://github.com/glpi-project/glpi/blob/main/apirest.md
"""

import requests
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Configuration
GLPI_API_URL = os.getenv("GLPI_API_URL", "https://glpi.univ-corse.fr/apirest.php")
GLPI_APP_TOKEN = os.getenv("GLPI_APP_TOKEN")
GLPI_USER_TOKEN = os.getenv("GLPI_USER_TOKEN")


class GLPIConnector:
    """Connecteur pour l'API REST de GLPI"""
    
    def __init__(self):
        self.session_token: Optional[str] = None
        self.base_url = GLPI_API_URL
        
        if not GLPI_APP_TOKEN or not GLPI_USER_TOKEN:
            logger.warning("GLPI tokens not configured. GLPI integration disabled.")
    
    def _get_headers(self, with_session: bool = True) -> Dict[str, str]:
        """Génère les headers pour les requêtes GLPI"""
        headers = {
            "App-Token": GLPI_APP_TOKEN,
            "Content-Type": "application/json"
        }
        if with_session and self.session_token:
            headers["Session-Token"] = self.session_token
        return headers
    
    def login(self) -> str:
        """
        Authentification à GLPI et obtention du session token.
        
        Returns:
            Session token
            
        Raises:
            Exception: Si l'authentification échoue
        """
        try:
            response = requests.get(
                f"{self.base_url}/initSession",
                headers={
                    "App-Token": GLPI_APP_TOKEN,
                    "Authorization": f"user_token {GLPI_USER_TOKEN}"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            self.session_token = data["session_token"]
            
            logger.info(f"✅ Connecté à GLPI : {data.get('session_token')[:10]}...")
            return self.session_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur connexion GLPI : {e}")
            raise Exception(f"Impossible de se connecter à GLPI : {e}")
    
    def create_ticket(
        self, 
        title: str, 
        description: str,
        user_id: int,
        category: str = "Autre",
        priority: str = "Moyenne"
    ) -> int:
        """
        Crée un ticket dans GLPI.
        
        Args:
            title: Titre du ticket (max 255 caractères)
            description: Description complète du problème
            user_id: ID de l'utilisateur dans GLPI
            category: Catégorie (Réseau, Matériel, etc.)
            priority: Priorité (Basse, Moyenne, Haute, Urgente)
            
        Returns:
            ID du ticket créé dans GLPI
            
        Raises:
            Exception: Si la création échoue
        """
        if not self.session_token:
            self.login()
        
        # Convertir priorité en code GLPI
        priority_map = {
            "Basse": 2,
            "Moyenne": 3,
            "Haute": 4,
            "Urgente": 5
        }
        glpi_priority = priority_map.get(priority, 3)
        
        # Convertir catégorie en ID GLPI (à adapter selon votre GLPI)
        # Pour commencer, on laisse vide et GLPI utilisera la catégorie par défaut
        category_id = self._get_category_id(category)
        
        try:
            payload = {
                "input": {
                    "name": title[:255],  # GLPI limite à 255 caractères
                    "content": description,
                    "urgency": glpi_priority,
                    "users_id_recipient": user_id,
                    "type": 1,  # 1 = Incident, 2 = Demande
                    "status": 1  # 1 = Nouveau
                }
            }
            
            # Ajouter la catégorie si trouvée
            if category_id:
                payload["input"]["itilcategories_id"] = category_id
            
            response = requests.post(
                f"{self.base_url}/Ticket",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            
            ticket_data = response.json()
            ticket_id = ticket_data["id"]
            
            logger.info(f"✅ Ticket GLPI créé : #{ticket_id} - {title}")
            return ticket_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur création ticket GLPI : {e}")
            # Si erreur, on retourne 0 pour indiquer l'échec sans bloquer
            return 0
    
    def _get_category_id(self, category: str) -> Optional[int]:
        """
        Récupère l'ID de la catégorie GLPI.
        
        Note: Ces IDs dépendent de votre configuration GLPI.
        À adapter selon les catégories configurées dans votre GLPI.
        
        Args:
            category: Nom de la catégorie
            
        Returns:
            ID de la catégorie ou None
        """
        # Mapping par défaut - À ADAPTER selon votre GLPI
        # Vous pouvez récupérer les IDs en faisant :
        # GET /apirest.php/ITILCategory
        category_map = {
            "Réseau": None,      # Remplacer par l'ID réel
            "Matériel": None,    # Remplacer par l'ID réel
            "Logiciel": None,    # Remplacer par l'ID réel
            "Compte": None,      # Remplacer par l'ID réel
            "Messagerie": None,  # Remplacer par l'ID réel
            "Système": None,     # Remplacer par l'ID réel
        }
        return category_map.get(category)
    
    def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un ticket GLPI.
        
        Args:
            ticket_id: ID du ticket dans GLPI
            
        Returns:
            Dictionnaire avec les données du ticket ou None
        """
        if not self.session_token:
            self.login()
        
        try:
            response = requests.get(
                f"{self.base_url}/Ticket/{ticket_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur récupération ticket GLPI #{ticket_id} : {e}")
            return None
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un utilisateur GLPI.
        
        Args:
            user_id: ID de l'utilisateur dans GLPI
            
        Returns:
            Dictionnaire avec les données utilisateur ou None
        """
        if not self.session_token:
            self.login()
        
        try:
            response = requests.get(
                f"{self.base_url}/User/{user_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur récupération user GLPI #{user_id} : {e}")
            return None
    
    def add_followup(self, ticket_id: int, content: str) -> bool:
        """
        Ajoute un suivi à un ticket GLPI.
        
        Args:
            ticket_id: ID du ticket
            content: Contenu du suivi
            
        Returns:
            True si succès, False sinon
        """
        if not self.session_token:
            self.login()
        
        try:
            response = requests.post(
                f"{self.base_url}/Ticket/{ticket_id}/ITILFollowup",
                headers=self._get_headers(),
                json={
                    "input": {
                        "items_id": ticket_id,
                        "itemtype": "Ticket",
                        "content": content
                    }
                }
            )
            response.raise_for_status()
            logger.info(f"✅ Suivi ajouté au ticket GLPI #{ticket_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur ajout suivi GLPI : {e}")
            return False
    
    def logout(self):
        """Ferme la session GLPI"""
        if self.session_token:
            try:
                requests.get(
                    f"{self.base_url}/killSession",
                    headers=self._get_headers()
                )
                logger.info("✅ Session GLPI fermée")
                self.session_token = None
            except Exception as e:
                logger.error(f"❌ Erreur fermeture session GLPI : {e}")
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à GLPI.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        try:
            self.login()
            logger.info("✅ Test connexion GLPI : OK")
            self.logout()
            return True
        except Exception as e:
            logger.error(f"❌ Test connexion GLPI : ÉCHEC - {e}")
            return False


# Instance globale du connecteur
glpi_connector = GLPIConnector()


# Fonction helper pour vérifier si GLPI est configuré
def is_glpi_enabled() -> bool:
    """Vérifie si GLPI est configuré et activé"""
    return bool(GLPI_APP_TOKEN and GLPI_USER_TOKEN)