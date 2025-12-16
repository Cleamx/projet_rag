"""
Module d'intégration GLPI.
Gère l'authentification, la création de tickets
et la récupération du statut et des solutions.
"""
import os
import base64
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Configuration
GLPI_URL = os.getenv("GLPI_URL", "http://localhost:8083/apirest.php")
GLPI_USER = os.getenv("GLPI_USER", "glpi")
GLPI_PASSWORD = os.getenv("GLPI_PASSWORD", "glpi")
APP_TOKEN = os.getenv("GLPI_APP_TOKEN")

TIMEOUT = 10


def get_glpi_session() -> Optional[str]:
    """Ouvre une session GLPI et retourne le token."""
    url = f"{GLPI_URL}/initSession"
    creds = base64.b64encode(f"{GLPI_USER}:{GLPI_PASSWORD}".encode()).decode()
    
    headers = {
        "App-Token": APP_TOKEN,
        "Authorization": f"Basic {creds}"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json().get("session_token")
    except Exception as e:
        logger.error(f"❌ GLPI session: {e}")
        return None


def close_glpi_session(token: Optional[str]) -> None:
    """Ferme une session GLPI."""
    if not token:
        return
    
    try:
        requests.get(
            f"{GLPI_URL}/killSession",
            headers={"App-Token": APP_TOKEN, "Session-Token": token},
            timeout=5
        )
    except Exception:
        pass


def create_ticket(username: str, question: str) -> Optional[Dict[str, Any]]:
    """Crée un ticket GLPI et retourne les infos du ticket."""
    session = get_glpi_session()
    if not session:
        logger.error("❌ Impossible de créer session GLPI")
        return None
    
    try:
        r = requests.post(
            f"{GLPI_URL}/Ticket",
            headers={
                "App-Token": APP_TOKEN,
                "Session-Token": session,
                "Content-Type": "application/json"
            },
            json={
                "input": {
                    "name": f"[Support IA] {username}",
                    "content": question,
                    "type": 1,
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
            logger.info(f"✅ Ticket #{result['id']} créé")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Création ticket: {e}")
        return None
    finally:
        close_glpi_session(session)


def get_ticket_details(ticket_id: int) -> Optional[Dict[str, Any]]:
    """
    Retourne le statut et la solution d'un ticket GLPI.
    
    Cherche la solution dans l'ordre:
    1. TicketFollowup (dernier followup)
    2. ITILSolution (solution officielle)
    3. Champ solution du ticket
    """
    session = get_glpi_session()
    if not session:
        return None
    
    headers = {"App-Token": APP_TOKEN, "Session-Token": session}
    
    try:
        # Récupérer le ticket
        r = requests.get(f"{GLPI_URL}/Ticket/{ticket_id}", headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        ticket = r.json()
        
        solution = None
        
        # 1. TicketFollowup
        try:
            r = requests.get(
                f"{GLPI_URL}/Ticket/{ticket_id}/TicketFollowup",
                headers=headers,
                timeout=TIMEOUT
            )
            if r.status_code == 200:
                followups = r.json() or []
                for f in reversed(followups):
                    content = f.get("content", "").strip()
                    if content and len(content) > 10:
                        solution = content
                        break
        except Exception as e:
            logger.warning(f"⚠️ Followups: {e}")
        
        # 2. ITILSolution
        if not solution:
            try:
                r = requests.get(
                    f"{GLPI_URL}/Ticket/{ticket_id}/ITILSolution",
                    headers=headers,
                    timeout=TIMEOUT
                )
                if r.status_code == 200:
                    solutions = r.json() or []
                    if solutions:
                        solution = solutions[-1].get("content", "").strip()
            except Exception as e:
                logger.warning(f"⚠️ ITILSolution: {e}")
        
        # 3. Champ solution direct
        if not solution and ticket.get("solution"):
            solution = ticket["solution"].strip()
        
        return {
            "id": ticket.get("id"),
            "status": ticket.get("status"),
            "name": ticket.get("name"),
            "content": ticket.get("content"),
            "solution": solution
        }
        
    except Exception as e:
        logger.error(f"❌ Détails ticket #{ticket_id}: {e}")
        return None
    finally:
        close_glpi_session(session)


def get_ticket_status(ticket_id: int) -> Optional[int]:
    """Retourne uniquement le statut d'un ticket (rapide)."""
    details = get_ticket_details(ticket_id)
    return details.get("status") if details else None