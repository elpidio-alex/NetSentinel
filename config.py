# =============================================================
# config.py — Chargement de la configuration NetSentinel
# Outil de surveillance réseau et défense automatisée
# =============================================================
# Ce module charge config.json, fusionne les secrets depuis .env,
# et résout dynamiquement la whitelist automatique (IP locale,
# passerelle, IP MySQL) pour éviter tout auto-blocage.
# =============================================================

import json
import os
import socket
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# ── Chargement des variables d'environnement (.env) ─────────
load_dotenv()

# ── Chemin du fichier de configuration ──────────────────────
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def _charger_json():
    """Lit et retourne le contenu brut de config.json."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _obtenir_ip_locale():
    """
    Retourne l'IP locale de la machine (celle utilisée pour sortir
    sur le réseau), sans dépendre d'une vraie connexion sortante.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Astuce classique : on "prétend" se connecter (aucun paquet
        # n'est réellement envoyé avec UDP + connect()), juste pour
        # forcer l'OS à choisir la bonne interface réseau.
        s.connect(("8.8.8.8", 80))
        ip_locale = s.getsockname()[0]
    except Exception:
        ip_locale = "127.0.0.1"
    finally:
        s.close()
    return ip_locale


def _obtenir_passerelle_par_defaut():
    """
    Retourne l'IP de la passerelle par défaut (gateway) sous Windows,
    en interrogeant la table de routage via 'route print'.
    """
    try:
        resultat = subprocess.run(
            ["route", "print", "0.0.0.0"],
            capture_output=True, text=True, timeout=5
        )
        for ligne in resultat.stdout.splitlines():
            if "0.0.0.0" in ligne:
                parties = ligne.split()
                # Format typique : Network  Netmask  Gateway  Interface  Metric
                if len(parties) >= 3:
                    candidat = parties[2]
                    if candidat.count(".") == 3:
                        return candidat
    except Exception:
        pass
    return None


def _resoudre_whitelist(config):
    """
    Remplace les placeholders de whitelist_automatique par les
    vraies valeurs calculées dynamiquement. Exigence critique :
    ne jamais bloquer accidentellement la machine locale, la
    passerelle, ou le serveur MySQL local.
    """
    whitelist_brute = config["defense"]["whitelist_automatique"]
    whitelist_resolue = []

    ip_locale = _obtenir_ip_locale()
    passerelle = _obtenir_passerelle_par_defaut()
    ip_mysql = config["database"]["host"]
    if ip_mysql == "localhost":
        ip_mysql = "127.0.0.1"

    for entree in whitelist_brute:
        if entree == "ip_locale_auto":
            whitelist_resolue.append(ip_locale)
        elif entree == "passerelle_par_defaut_auto":
            if passerelle:
                whitelist_resolue.append(passerelle)
        elif entree == "ip_mysql_local":
            whitelist_resolue.append(ip_mysql)
        else:
            whitelist_resolue.append(entree)

    # Suppression des doublons tout en gardant l'ordre
    vus = set()
    whitelist_finale = []
    for ip in whitelist_resolue:
        if ip not in vus:
            vus.add(ip)
            whitelist_finale.append(ip)

    return whitelist_finale


def charger_configuration():
    """
    Point d'entrée principal. Charge config.json, injecte le mot
    de passe MySQL depuis .env, et résout la whitelist dynamique.

    Retourne :
        dict : configuration complète prête à l'emploi
    """
    config = _charger_json()

    # ── Injection des secrets depuis .env ───────────────────
    config["database"]["mot_de_passe"] = os.getenv("MYSQL_PASSWORD", "")
    config["database"]["utilisateur"] = os.getenv(
        "MYSQL_USER", config["database"]["utilisateur"]
    )

    # ── Résolution de la whitelist automatique ──────────────
    config["defense"]["whitelist_automatique"] = _resoudre_whitelist(config)

    return config


# ── Instance unique chargée au démarrage de l'application ───
# Les autres modules font : from config import CONFIG
CONFIG = charger_configuration()


if __name__ == "__main__":
    # Test manuel : python config.py
    import pprint
    pprint.pprint(CONFIG)