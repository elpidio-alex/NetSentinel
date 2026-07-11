"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# db.py — Connexion et opérations base de données NetSentinel
# Outil de surveillance réseau et défense automatisée
# =============================================================

import mysql.connector
from mysql.connector import Error
from config import CONFIG

# ── Connexion persistante pour les insertions en masse ───────
# Utilisée uniquement par executer_requete_rapide() pendant la
# capture réseau (évite d'ouvrir une nouvelle connexion SSL
# pour chaque paquet, ce qui bloquait le thread Tkinter).
_connexion_persistante = None


def obtenir_connexion():
    """
    Ouvre et retourne une nouvelle connexion MySQL vers netsentinel_db.
    SSL désactivé (connexion locale uniquement).
    """
    try:
        connexion = mysql.connector.connect(
            host=CONFIG["database"]["host"],
            port=CONFIG["database"]["port"],
            database=CONFIG["database"]["nom"],
            user=CONFIG["database"]["utilisateur"],
            password=CONFIG["database"]["mot_de_passe"],
            ssl_disabled=True,
            use_pure=True
        )
        return connexion
    except Error as e:
        print(f"[ERREUR DB] Connexion échouée : {e}")
        return None


def obtenir_connexion_persistante():
    """
    Retourne une connexion réutilisable (ouverte une seule fois).
    Utilisée pendant la capture pour éviter le coût SSL à chaque paquet.
    """
    global _connexion_persistante
    try:
        if _connexion_persistante is None or not _connexion_persistante.is_connected():
            _connexion_persistante = obtenir_connexion()
        return _connexion_persistante
    except Exception:
        _connexion_persistante = None
        return None


def executer_requete(requete, valeurs=None, commit=False, retour_id=False):
    """
    Exécute une requête SQL générique (INSERT/UPDATE/DELETE).
    Ouvre et ferme une connexion à chaque appel — ne pas utiliser
    pendant la boucle de capture (utiliser executer_requete_rapide).
    """
    connexion = obtenir_connexion()
    if connexion is None:
        return False

    try:
        curseur = connexion.cursor()
        curseur.execute(requete, valeurs or ())
        if commit:
            connexion.commit()
        if retour_id:
            return curseur.lastrowid
        return True
    except Error as e:
        print(f"[ERREUR DB] Requête échouée : {e}")
        return False
    finally:
        curseur.close()
        connexion.close()


def executer_requete_rapide(requete, valeurs=None):
    """
    Variante d'executer_requete utilisant la connexion persistante.
    Conçue pour les insertions à haute fréquence (un paquet toutes
    les ~300ms ou moins) sans overhead SSL à chaque appel.
    Pas de retour_id — uniquement pour INSERT sans besoin du lastrowid.
    """
    connexion = obtenir_connexion_persistante()
    if connexion is None:
        return False

    try:
        curseur = connexion.cursor()
        curseur.execute(requete, valeurs or ())
        connexion.commit()
        curseur.close()
        return True
    except Error as e:
        print(f"[ERREUR DB] Requête rapide échouée : {e}")
        # Connexion peut être corrompue — on la réinitialise
        global _connexion_persistante
        _connexion_persistante = None
        return False


def recuperer_un(requete, valeurs=None):
    """
    Exécute une requête SELECT et retourne une seule ligne.
    """
    connexion = obtenir_connexion()
    if connexion is None:
        return None

    try:
        curseur = connexion.cursor(dictionary=True)
        curseur.execute(requete, valeurs or ())
        return curseur.fetchone()
    except Error as e:
        print(f"[ERREUR DB] Requête échouée : {e}")
        return None
    finally:
        curseur.close()
        connexion.close()


def recuperer_plusieurs(requete, valeurs=None):
    """
    Exécute une requête SELECT et retourne toutes les lignes.
    """
    connexion = obtenir_connexion()
    if connexion is None:
        return []

    try:
        curseur = connexion.cursor(dictionary=True)
        curseur.execute(requete, valeurs or ())
        return curseur.fetchall()
    except Error as e:
        print(f"[ERREUR DB] Requête échouée : {e}")
        return []
    finally:
        curseur.close()
        connexion.close()


def tester_connexion():
    """
    Vérifie que la connexion à netsentinel_db fonctionne.
    """
    connexion = obtenir_connexion()
    if connexion is not None and connexion.is_connected():
        connexion.close()
        return True
    return False


if __name__ == "__main__":
    if tester_connexion():
        print("✅ Connexion à netsentinel_db réussie.")
    else:
        print("❌ Échec de connexion à netsentinel_db.")