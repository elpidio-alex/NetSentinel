"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# history_log.py — Journalisation centralisée (table history_log)
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Point d'entrée unique pour écrire dans l'historique consultable
# par history_view.py. Tout module qui produit un événement notable
# (connexion, alerte, blocage, déblocage) appelle une fonction
# d'ici plutôt que d'insérer directement dans history_log.
# =============================================================

from db import executer_requete


def _enregistrer(type_evenement, description, ip=None, username=None, user_id=None):
    """
    Insère une ligne dans history_log. Ne lève jamais d'exception
    vers l'appelant — un échec de journalisation ne doit jamais
    bloquer l'action métier (connexion, blocage, etc.) qui l'a
    déclenché.
    """
    executer_requete(
        """INSERT INTO history_log (type, ip, description, username, user_id)
           VALUES (%s, %s, %s, %s, %s)""",
        (type_evenement, ip, description, username, user_id),
        commit=True
    )


def logger_connexion(username, user_id):
    """Journalise une connexion réussie."""
    _enregistrer(
        "connexion",
        description=f"Connexion réussie de {username}",
        username=username, user_id=user_id
    )


def logger_inscription(username, user_id):
    """Journalise la création d'un nouveau compte."""
    _enregistrer(
        "inscription",
        description=f"Création du compte {username}",
        username=username, user_id=user_id
    )


def logger_alerte(ip_source, type_menace, criticite, details):
    """Journalise une alerte générée par le moteur IDS."""
    _enregistrer(
        "alerte",
        description=f"[{criticite}] {type_menace} — {details}",
        ip=ip_source
    )


def logger_blocage(ip, mode, raison):
    """Journalise le blocage d'une IP."""
    _enregistrer(
        "blocage",
        description=f"IP bloquée ({mode}) — {raison}",
        ip=ip
    )


def logger_deblocage(ip):
    """Journalise le déblocage d'une IP."""
    _enregistrer(
        "deblocage",
        description="IP débloquée",
        ip=ip
    )