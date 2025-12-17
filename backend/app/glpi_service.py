"""Service d'intégration GLPI réel."""
import base64
import logging
from typing import Dict, List, Optional
import requests

from .config import settings

logger = logging.getLogger(__name__)
TIMEOUT = 10

class GLPIService:
    """Service pour interagir avec GLPI API.  """
    
    def __init__(self):
        self.url = settings.GLPI_URL
        self.app_token = settings.GLPI_APP_TOKEN
        self.user = settings.GLPI_USER
        self.password = settings.GLPI_PASSWORD
        self._session_token = None
    
    def _get_session(self) -> Optional[str]:
        """Ouvre une session GLPI."""
        if self._session_token:
            return self._session_token
        
        creds = base64.b64encode(f"{self.user}:{self.password}".encode()).decode()
        headers = {
            "App-Token": self.app_token,
            "Authorization": f"Basic {creds}"
        }
        
        try:
            r = requests.get(f"{self.url}/initSession", headers=headers, timeout=TIMEOUT)
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
                f"{self.url}/killSession",
                headers={"App-Token": self.app_token, "Session-Token": self._session_token},
                timeout=5
            )
        except:
            pass
        finally:
            self._session_token = None
    
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[dict]:
        """Fait une requête à l'API GLPI."""
        session = self._get_session()
        if not session:
            return None
        
        headers = {"App-Token": self.app_token, "Session-Token": session}
        
        try:
            url = f"{self.url}/{endpoint}"
            r = requests.request(method, url, headers=headers, timeout=TIMEOUT, **kwargs)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"❌ GLPI {endpoint}: {e}")
            return None
    
    def search_tickets(self, query: str, limit: int = 10) -> List[Dict]:
        """Récupère les derniers tickets résolus avec solution."""
        # Liste simple des tickets
        data = self._make_request("Ticket", params={"range": f"0-{limit*3-1}"})
        if not data:
            return []
        
        results = []
        for ticket in data:
            # Seulement les tickets résolus (status 5 ou 6)
            if ticket.get("status") not in [5, 6]:
                continue
            
            ticket_id = ticket.get("id")
            solution = self._get_ticket_solution(ticket_id)
            
            if solution and len(solution) > 20:
                results.append({
                    "id": ticket_id,
                    "title": ticket.get("name", "Sans titre"),
                    "content": f"{ticket.get('content', '')}\n\nSolution: {solution}",
                    "source": "ticket",
                    "metadata": {"status": ticket.get("status"), "date": ticket.get("date")}
                })
            
            if len(results) >= limit:
                break
        
        return results
    
    def _get_ticket_solution(self, ticket_id: int) -> Optional[str]:
        """Récupère la solution d'un ticket."""
        # TicketFollowup
        followups = self._make_request(f"Ticket/{ticket_id}/TicketFollowup")
        if followups and isinstance(followups, list):
            for f in reversed(followups):
                content = f.get("content", "").strip()
                if content and len(content) > 10:
                    return content
        
        # ITILSolution
        solutions = self._make_request(f"Ticket/{ticket_id}/ITILSolution")
        if solutions and isinstance(solutions, list) and solutions:
            return solutions[-1].get("content", "").strip()
        
        return None
    
    def search_kb(self, query: str, limit: int = 5) -> List[Dict]:
        """Récupère les articles de la base de connaissances."""
        data = self._make_request("KnowbaseItem", params={"range": f"0-{limit-1}"})
        if not data:
            return []
        
        results = []
        for item in data:
            if item.get("answer"):
                results.append({
                    "id": item.get("id"),
                    "title": item.get("name", "Sans titre"),
                    "content": item.get("answer", ""),
                    "source": "kb_article",
                    "metadata": {"date": item.get("date")}
                })
        
        return results
    
    def search_all(self, query: str, limit: int = 4) -> List[Dict]:
        """Recherche dans toutes les sources GLPI."""
        results = []
        
        # Tickets
        tickets = self.search_tickets(query, limit=limit//2)
        results.extend(tickets)
        
        # Base de connaissances
        kb = self.search_kb(query, limit=limit//2)
        results.extend(kb)
        
        logger.info(f"📊 GLPI: {len(results)} résultats trouvés")
        return results[:limit]
    
    def __del__(self):
        self._close_session()

# Instance globale
glpi_service = GLPIService()