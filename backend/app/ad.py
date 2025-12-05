from ldap3 import Server, Connection, ALL, NTLM

# -------------------- FONCTIONS UTILISATEUR AD --------------------


# -------------------- CONFIGURATION AD --------------------
AD_SERVER = "34.201.92.124"        # IP du serveur AD
AD_USER = "a2s@m2data.local"  # compte admin pour lecture LDAP
AD_PASSWORD = "12345678aS"
AD_BASE_DN = "DC=M2DATA,DC=LOCAL" 

server = Server(AD_SERVER, get_info=ALL)
conn = Connection(server, AD_USER, AD_PASSWORD, auto_bind=True)


def get_user_info(login):
    #Récupère le nom et email depuis AD pour un login donné
    search_filter = f"(sAMAccountName={login})"
    conn.search(AD_BASE_DN, search_filter, attributes=["displayName", "mail"])
    if conn.entries:
        entry = conn.entries[0]
        return {"displayName": str(entry.displayName), "mail": str(entry.mail)}
    return {"displayName": login, "mail": None}
