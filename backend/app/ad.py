from ldap3 import Server
from ldap3 import Connection
from ldap3 import ALL
from dotenv import load_dotenv
import os

load_dotenv()

AD_SERVER = os.getenv("AD_SERVER")
AD_USER = os.getenv("AD_USER")
AD_PASSWORD = os.getenv("AD_PASSWORD")
AD_BASE_DN = os.getenv("AD_BASE_DN")

server = Server(AD_SERVER, get_info=ALL)
conn = Connection(server, AD_USER, AD_PASSWORD, auto_bind=True)


def get_user_info(login):

    search_filter = f"(sAMAccountName={login})"
    conn.search(AD_BASE_DN, search_filter, attributes=["displayName", "mail"])

    if conn.entries:
        entry = conn.entries[0]
        return {
            "displayName": str(entry.displayName),
            "mail": str(entry.mail)
        }

    return {"displayName": login, "mail": None}
