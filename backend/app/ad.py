from ldap3 import Server, Connection, ALL
from dotenv import load_dotenv
import os

# Charger le fichier .env
load_dotenv()

# -------------------- CONFIGURATION AD --------------------


AD_SERVER = os.getenv("AD_SERVER")
AD_USER = os.getenv("AD_USER")
AD_PASSWORD = os.getenv("AD_PASSWORD")
AD_BASE_DN = os.getenv("AD_BASE_DN")


server = Server(AD_SERVER, get_info=ALL)
conn = Connection(server, AD_USER, AD_PASSWORD, auto_bind=True)

# -------------------- FONCTIONS UTILISATEUR AD --------------------

def get_user_info(login):

    """Récupère le nom et email depuis AD pour un login donné."""

    search_filter = f"(sAMAccountName={login})"
    conn.search(AD_BASE_DN, search_filter, attributes=["displayName", "mail"])
    
    if conn.entries:
        entry = conn.entries[0]
        return {
            "displayName": str(entry.displayName),
            "mail": str(entry.mail)
        }
    
    return {"displayName": login, "mail": None}
