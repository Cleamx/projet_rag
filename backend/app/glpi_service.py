"""
Service d'infrastructure : GLPI + Active Directory
Gère uniquement l'interaction avec les systèmes externes.
"""
import os
import base64
import logging
import requests
from typing import Dict, Optional
from ldap3 import Server, Connection, ALL

logger = logging.getLogger(__name__)

# ================================================================================
# CONFIGURATION
# ================================================================================

# GLPI
GLPI_URL = os.getenv("GLPI_URL", "http://glpi:80/apirest.php")
GLPI_USER = os.getenv("GLPI_USER", "glpi")
GLPI_PASSWORD = os.getenv("GLPI_PASSWORD", "glpi")
GLPI_APP_TOKEN = os.getenv("GLPI_APP_TOKEN", "")

# Active Directory
AD_SERVER = os.getenv("AD_SERVER", "34.201.92.124")
AD_USER = os.getenv("AD_USER", "a2s@m2data.local")
AD_PASSWORD = os.getenv("AD_PASSWORD", "12345678aS")
AD_BASE_DN = os.getenv("AD_BASE_DN", "DC=M2DATA,DC=LOCAL")

TIMEOUT = 10

# ================================================================================
# GLPI SERVICE
# ================================================================================

class GLPIService:
    """Gestion des interactions avec GLPI."""
    
    def __init__(self):
        self._session_token = None
    
    def _get_session(self) -> Optional[str]:
        """Ouvre une session GLPI."""
        if self._session_token:
            return self._session_token
        
        creds = base64.b64encode(f"{GLPI_USER}:{GLPI_PASSWORD}".encode()).decode()
        headers = {
            "App-Token": GLPI_APP_TOKEN,
            "Authorization": f"Basic {creds}"
        }
        
        try:
            r = requests.get(f"{GLPI_URL}/initSession", headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            self._session_token = r.json().get("session_token")
            logger.info("✅ GLPI session créée")
            return self._session_token
        except Exception as e:
            logger.error(f"❌ GLPI session: {e}")
            return None
    
    def _close_session(self):
        """Ferme la session GLPI."""
        if not self._session_token:
            return
        try:
            requests.get(
                f"{GLPI_URL}/killSession",
                headers={"App-Token": GLPI_APP_TOKEN, "Session-Token": self._session_token},
                timeout=5
            )
        except:
            pass
        finally:
            self._session_token = None
    
    def create_ticket(self, username: str, question: str, user_info: Dict = None) -> Optional[Dict]:
        """
        Crée un ticket dans GLPI.
        
        Args:
            username: Login utilisateur
            question: Contenu de la question
            user_info: Infos optionnelles de l'AD (displayName, mail, etc.)
        
        Returns:
            Dict avec id, message ou None si erreur
        """
        session = self._get_session()
        if not session:
            return None
        
        # Prépare le nom du ticket avec les infos AD si disponibles
        display_name = user_info.get('displayName', username) if user_info else username
        user_email = user_info.get('mail', '') if user_info else ''
        
        ticket_name = f"[Support IA] {display_name}"
        ticket_content = f"Utilisateur: {username}"
        if user_email:
            ticket_content += f"\nEmail: {user_email}"
        ticket_content += f"\n\nQuestion:\n{question}"
        
        try:
            r = requests.post(
                f"{GLPI_URL}/Ticket",
                headers={
                    "App-Token": GLPI_APP_TOKEN,
                    "Session-Token": session,
                    "Content-Type": "application/json"
                },
                json={
                    "input": {
                        "name": ticket_name,
                        "content": ticket_content,
                        "type": 1,  # Incident
                        "urgency": 3,
                        "impact": 3,
                        "priority": 3
                    }
                },
                timeout=TIMEOUT
            )
            r.raise_for_status()
            result = r.json()
            
            if result.get('id'):
                logger.info(f"✅ Ticket #{result['id']} créé pour {username}")
                return {
                    "id": result['id'],
                    "message": f"Ticket #{result['id']} créé",
                    "ticket_id": result['id']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Création ticket: {e}")
            return None
        finally:
            self._close_session()
    
    def get_ticket_details(self, ticket_id: int) -> Optional[Dict]:
        """
        Récupère les détails d'un ticket.
        
        Returns:
            Dict avec id, status, solution ou None
        """
        session = self._get_session()
        if not session:
            return None
        
        headers = {"App-Token": GLPI_APP_TOKEN, "Session-Token": session}
        
        try:
            # Ticket principal
            r = requests.get(f"{GLPI_URL}/Ticket/{ticket_id}", headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            ticket = r.json()
            
            solution = None
            
            # 1. TicketFollowup (le plus courant)
            try:
                r2 = requests.get(f"{GLPI_URL}/Ticket/{ticket_id}/TicketFollowup", headers=headers, timeout=TIMEOUT)
                if r2.status_code == 200:
                    followups = r2.json() or []
                    for followup in reversed(followups):
                        content = followup.get('content', '').strip()
                        if content and len(content) > 10:
                            solution = content
                            break
            except Exception as e:
                logger.warning(f"⚠️ Followups: {e}")
            
            # 2. ITILSolution
            if not solution:
                try:
                    r3 = requests.get(f"{GLPI_URL}/Ticket/{ticket_id}/ITILSolution", headers=headers, timeout=TIMEOUT)
                    if r3.status_code == 200:
                        solutions = r3.json() or []
                        if solutions:
                            solution = solutions[-1].get('content', '').strip()
                except Exception as e:
                    logger.warning(f"⚠️ ITILSolution: {e}")
            
            # 3. Champ solution direct
            if not solution and ticket.get('solution'):
                solution = ticket['solution'].strip()
            
            return {
                "id": ticket.get("id"),
                "status": ticket.get("status"),
                "name": ticket.get("name"),
                "content": ticket.get("content"),
                "solution": solution,
                "date": ticket.get("date"),
                "date_mod": ticket.get("date_mod")
            }
            
        except Exception as e:
            logger.error(f"❌ Détails ticket #{ticket_id}: {e}")
            return None
        finally:
            self._close_session()
    
    def get_user_tickets(self, username: str, limit: int = 20) -> list:
        """
        Récupère les tickets d'un utilisateur (recherche dans le contenu).
        
        Returns:
            Liste de tickets
        """
        session = self._get_session()
        if not session:
            return []
        
        try:
            # Note: GLPI search API est complexe, ici on récupère les derniers tickets
            # et on filtre côté application (pas optimal mais simple)
            r = requests.get(
                f"{GLPI_URL}/Ticket",
                headers={"App-Token": GLPI_APP_TOKEN, "Session-Token": session},
                params={"range": f"0-{limit*2-1}"},
                timeout=TIMEOUT
            )
            r.raise_for_status()
            tickets = r.json() or []
            
            # Filtre par username dans le contenu
            user_tickets = []
            for ticket in tickets:
                if username.lower() in ticket.get('content', '').lower():
                    user_tickets.append({
                        "id": ticket.get("id"),
                        "name": ticket.get("name"),
                        "status": ticket.get("status"),
                        "date": ticket.get("date")
                    })
            
            return user_tickets[:limit]
            
        except Exception as e:
            logger.error(f"❌ Tickets user {username}: {e}")
            return []
        finally:
            self._close_session()

# ================================================================================
# ACTIVE DIRECTORY SERVICE
# ================================================================================

class ADService:
    """Gestion des interactions avec Active Directory."""
    
    def __init__(self):
        self.server = Server(AD_SERVER, get_info=ALL)
        self.user = AD_USER
        self.password = AD_PASSWORD
        self.base_dn = AD_BASE_DN
    
    def get_user_info(self, login: str) -> Optional[Dict]:
        """
        Récupère les informations d'un utilisateur depuis l'AD.
        
        Args:
            login: sAMAccountName (login utilisateur)
        
        Returns:
            Dict avec displayName, mail, department, etc. ou None
        """
        try:
            conn = Connection(
                self.server,
                user=self.user,
                password=self.password,
                auto_bind=True
            )
            
            search_filter = f"(sAMAccountName={login})"
            attributes = [
                "displayName",
                "mail",
                "department",
                "title",
                "telephoneNumber",
                "distinguishedName"
            ]
            
            conn.search(
                self.base_dn,
                search_filter,
                attributes=attributes
            )
            
            if conn.entries:
                entry = conn.entries[0]
                user_info = {
                    "username": login,
                    "displayName": str(entry.displayName) if entry.displayName else login,
                    "mail": str(entry.mail) if entry.mail else None,
                    "department": str(entry.department) if entry.department else None,
                    "title": str(entry.title) if entry.title else None,
                    "phone": str(entry.telephoneNumber) if entry.telephoneNumber else None,
                    "dn": str(entry.distinguishedName) if entry.distinguishedName else None
                }
                
                logger.info(f"✅ AD info pour {login}: {user_info['displayName']}")
                return user_info
            
            logger.warning(f"⚠️ Utilisateur {login} non trouvé dans l'AD")
            return None
            
        except Exception as e:
            logger.error(f"❌ AD lookup pour {login}: {e}")
            return None

# ================================================================================
# INSTANCES GLOBALES
# ================================================================================

glpi_service = GLPIService()
ad_service = ADService()