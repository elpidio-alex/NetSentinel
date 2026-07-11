"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# defense.py — Blocage IP, coupure TCP et gestion whitelist
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Ce module exécute les actions de défense : blocage d'IP (mode
# passif = simulation/log, mode actif = vrai netsh), coupure TCP
# RST, et protection stricte contre l'auto-blocage via whitelist.
# Chaque blocage/déblocage réussi est journalisé dans history_log.
#
# SÉCURITÉ CRITIQUE : aucune IP de la whitelist ne peut être
# bloquée, même en mode actif, même par erreur d'appel.
# =============================================================

import subprocess
import threading
import time
from datetime import datetime, timedelta

from scapy.all import send, IP, TCP
from config import CONFIG
from db import executer_requete, recuperer_un, recuperer_plusieurs
from history_log import logger_blocage, logger_deblocage


class ModuleDefense:
    """
    Gère le blocage des IP et la coupure de connexions suspectes.

    Utilisation typique :
        defense = ModuleDefense()
        resultat = defense.bloquer_ip("203.0.113.42", raison="Scan de ports",
                                        mode="actif", confirme_par_utilisateur=True)
    """

    def __init__(self):
        self.mode_defaut = CONFIG["defense"]["mode_defaut"]
        self.duree_blocage_minutes = CONFIG["defense"]["duree_blocage_minutes"]
        self.blocage_permanent_autorise = CONFIG["defense"]["blocage_permanent_autorise"]
        self.confirmation_requise = CONFIG["defense"]["confirmation_requise_mode_actif"]
        self.whitelist = set(CONFIG["defense"]["whitelist_automatique"])

        self._synchroniser_whitelist_db()
        self._demarrer_nettoyage_automatique()

    # ─────────────────────────────────────────────────────────
    # Whitelist
    # ─────────────────────────────────────────────────────────
    def _synchroniser_whitelist_db(self):
        """
        Charge en mémoire la whitelist depuis la base (table
        whitelist_ips) en plus de celle auto-calculée par config.py,
        et enregistre les IP auto-calculées en base si absentes.
        """
        lignes = recuperer_plusieurs("SELECT ip FROM whitelist_ips")
        for ligne in lignes:
            self.whitelist.add(ligne["ip"])

        for ip in CONFIG["defense"]["whitelist_automatique"]:
            existe = recuperer_un("SELECT id FROM whitelist_ips WHERE ip = %s", (ip,))
            if not existe:
                executer_requete(
                    "INSERT INTO whitelist_ips (ip, raison) VALUES (%s, %s)",
                    (ip, "Ajout automatique (protection anti-auto-blocage)"),
                    commit=True
                )

    def est_dans_whitelist(self, ip):
        """Vérifie si une IP est protégée (jamais bloquable)."""
        return ip in self.whitelist

    def ajouter_a_whitelist(self, ip, raison=""):
        """Ajoute manuellement une IP à la whitelist (ex: depuis blacklist_view.py)."""
        if ip in self.whitelist:
            return {"succes": False, "message": "IP déjà dans la whitelist."}

        executer_requete(
            "INSERT INTO whitelist_ips (ip, raison) VALUES (%s, %s)",
            (ip, raison), commit=True
        )
        self.whitelist.add(ip)
        return {"succes": True, "message": f"{ip} ajoutée à la whitelist."}

    # ─────────────────────────────────────────────────────────
    # Blocage IP
    # ─────────────────────────────────────────────────────────
    def bloquer_ip(self, ip, raison, mode=None, confirme_par_utilisateur=False, permanent=False):
        """
        Bloque une IP en mode passif (log/GUI uniquement) ou actif
        (vraie règle pare-feu Windows via netsh).

        Paramètres :
            ip (str)
            raison (str)
            mode (str|None)  : "passif" ou "actif" — défaut = config
            confirme_par_utilisateur (bool) : requis en mode actif
            permanent (bool) : ignoré si blocage_permanent_autorise = False

        Retourne :
            dict : {"succes": bool, "message": str}
        """
        mode = mode or self.mode_defaut

        # ── Protection anti-auto-blocage (prioritaire, non contournable) ──
        if self.est_dans_whitelist(ip):
            return {
                "succes": False,
                "message": f"⛔ Blocage refusé : {ip} est dans la whitelist (protection anti-auto-blocage)."
            }

        deja_bloquee = recuperer_un(
            "SELECT id FROM blocked_ips WHERE ip = %s AND active = TRUE", (ip,)
        )
        if deja_bloquee:
            return {"succes": False, "message": f"{ip} est déjà bloquée."}

        # ── Mode actif : confirmation obligatoire ──
        if mode == "actif":
            if self.confirmation_requise and not confirme_par_utilisateur:
                return {
                    "succes": False,
                    "message": "Confirmation utilisateur requise avant blocage réel (mode actif)."
                }
            resultat_pare_feu = self._appliquer_regle_pare_feu(ip)
            if not resultat_pare_feu["succes"]:
                return resultat_pare_feu

        # ── Calcul de l'expiration ──
        permanent_effectif = permanent and self.blocage_permanent_autorise
        date_expiration = None
        if not permanent_effectif:
            date_expiration = datetime.now() + timedelta(minutes=self.duree_blocage_minutes)

        executer_requete(
            """INSERT INTO blocked_ips (ip, raison, mode, expires_at, active)
               VALUES (%s, %s, %s, %s, TRUE)""",
            (ip, raison, mode, date_expiration),
            commit=True
        )

        logger_blocage(ip, mode, raison)

        type_message = "permanent" if permanent_effectif else f"temporaire ({self.duree_blocage_minutes} min)"
        return {
            "succes": True,
            "message": f"IP {ip} bloquée en mode {mode} ({type_message})."
        }

    def _appliquer_regle_pare_feu(self, ip):
        """
        Ajoute une vraie règle de blocage Windows Firewall via netsh.
        Nécessite les droits administrateur.
        """
        nom_regle = f"NetSentinel_Block_{ip}"
        try:
            resultat = subprocess.run(
                [
                    "netsh", "advfirewall", "firewall", "add", "rule",
                    f"name={nom_regle}",
                    "dir=in", "action=block",
                    f"remoteip={ip}"
                ],
                capture_output=True, text=True, timeout=10
            )
            if resultat.returncode == 0:
                return {"succes": True, "message": "Règle pare-feu ajoutée."}
            return {
                "succes": False,
                "message": f"Échec netsh (droits admin requis ?) : {resultat.stderr.strip()}"
            }
        except Exception as e:
            return {"succes": False, "message": f"Erreur lors de l'appel netsh : {e}"}

    def _supprimer_regle_pare_feu(self, ip):
        """Retire la règle Windows Firewall associée à une IP."""
        nom_regle = f"NetSentinel_Block_{ip}"
        try:
            subprocess.run(
                ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={nom_regle}"],
                capture_output=True, text=True, timeout=10
            )
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────
    # Déblocage
    # ─────────────────────────────────────────────────────────
    def debloquer_ip(self, ip):
        """Débloque une IP spécifique (retire la règle pare-feu si présente)."""
        self._supprimer_regle_pare_feu(ip)
        executer_requete(
            "UPDATE blocked_ips SET active = FALSE WHERE ip = %s AND active = TRUE",
            (ip,), commit=True
        )
        logger_deblocage(ip)
        return {"succes": True, "message": f"{ip} débloquée."}

    def debloquer_tout(self):
        """
        Débloque toutes les IP actives. Utilisé par le bouton
        "Débloquer tout" dans blacklist_view.py (garde-fou manuel).
        """
        lignes = recuperer_plusieurs("SELECT ip FROM blocked_ips WHERE active = TRUE")
        for ligne in lignes:
            self._supprimer_regle_pare_feu(ligne["ip"])

        executer_requete(
            "UPDATE blocked_ips SET active = FALSE WHERE active = TRUE",
            commit=True
        )

        for ligne in lignes:
            logger_deblocage(ligne["ip"])

        return {"succes": True, "message": f"{len(lignes)} IP débloquées."}

    def lister_ip_bloquees(self):
        """Retourne la liste des IP actuellement bloquées (pour blacklist_view.py)."""
        return recuperer_plusieurs(
            "SELECT * FROM blocked_ips WHERE active = TRUE ORDER BY blocked_at DESC"
        )

    # ─────────────────────────────────────────────────────────
    # Nettoyage automatique des blocages expirés
    # ─────────────────────────────────────────────────────────
    def _demarrer_nettoyage_automatique(self):
        """Lance un thread daemon qui débloque automatiquement les IP expirées."""
        def boucle():
            while True:
                self._nettoyer_blocages_expires()
                time.sleep(30)

        thread = threading.Thread(target=boucle, daemon=True)
        thread.start()

    def _nettoyer_blocages_expires(self):
        expirees = recuperer_plusieurs(
            """SELECT ip FROM blocked_ips
               WHERE active = TRUE AND expires_at IS NOT NULL AND expires_at <= NOW()"""
        )
        for ligne in expirees:
            self.debloquer_ip(ligne["ip"])

    # ─────────────────────────────────────────────────────────
    # Coupure TCP (RST spoofé) — indépendante du blocage pare-feu
    # ─────────────────────────────────────────────────────────
    def couper_connexion_tcp(self, ip_source, port_source, ip_destination, port_destination, seq=0):
        """
        Envoie un paquet TCP RST pour interrompre immédiatement
        une connexion suspecte, sans attendre la règle pare-feu.

        Nécessite les droits administrateur (Scapy).
        """
        if self.est_dans_whitelist(ip_source) or self.est_dans_whitelist(ip_destination):
            return {"succes": False, "message": "⛔ Coupure refusée : IP protégée (whitelist)."}

        try:
            paquet = (
                IP(src=ip_destination, dst=ip_source) /
                TCP(sport=port_destination, dport=port_source, flags="R", seq=seq)
            )
            send(paquet, verbose=False)
            return {"succes": True, "message": "Connexion coupée (RST envoyé)."}
        except Exception as e:
            return {"succes": False, "message": f"Erreur lors de l'envoi du RST : {e}"}


if __name__ == "__main__":
    # Test manuel : python defense.py
    defense = ModuleDefense()
    print("Whitelist active :", defense.whitelist)

    # Test blocage passif (sans danger)
    resultat = defense.bloquer_ip("203.0.113.42", raison="Test manuel", mode="passif")
    print(resultat)

    print("IP bloquées :", defense.lister_ip_bloquees())