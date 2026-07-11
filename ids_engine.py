"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# ids_engine.py — Moteur de détection d'intrusion (règles)
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Ce module consomme les paquets extraits par sniffer.py et
# applique des règles de détection : scan de ports, brute-force,
# exfiltration/comportement anormal. Chaque détection génère
# une alerte enregistrée en base (table alerts) et journalisée
# dans history_log, puis transmise à la GUI.
# =============================================================

import time
from collections import defaultdict, deque
from datetime import datetime

from config import CONFIG
from db import executer_requete
from history_log import logger_alerte


class MoteurIDS:
    """
    Analyse les paquets en flux continu et applique des règles
    de détection basées sur des seuils configurables (config.json).

    Utilisation typique (dans app.py ou monitor_view.py) :
        moteur = MoteurIDS(session_id=1)
        moteur.analyser_paquet(paquet_info)   # appelé pour chaque paquet
        alertes = moteur.recuperer_alertes_recentes()
    """

    def __init__(self, session_id):
        self.session_id = session_id

        # ── Paramètres depuis config.json ────────────────────
        params = CONFIG["surveillance"]
        self.seuil_scan_ports = params["seuil_scan_ports"]
        self.fenetre_scan = params["fenetre_temps_scan_secondes"]
        self.seuil_brute_force = params["seuil_brute_force"]
        self.fenetre_brute_force = params["fenetre_temps_brute_force_secondes"]
        self.seuil_exfiltration_mo = params["seuil_exfiltration_mo"]

        # ── États internes pour la détection ────────────────
        # Pour chaque IP source : liste des (horodatage, port) vus récemment
        self._ports_par_ip = defaultdict(lambda: deque())

        # Pour chaque (ip_source, port_destination) : compte de tentatives
        # (utile pour détecter le brute-force sur un service précis, ex: port 22, 3389)
        self._tentatives_par_ip_port = defaultdict(lambda: deque())

        # Volume de données sortantes par IP destination (Mo), pour l'exfiltration
        self._volume_sortant_par_ip = defaultdict(float)

        # Alertes générées durant la session (cache local, en plus de la BDD)
        self._alertes_recentes = deque(maxlen=100)

    # ─────────────────────────────────────────────────────────
    # Point d'entrée principal
    # ─────────────────────────────────────────────────────────
    def analyser_paquet(self, info):
        """
        Analyse un paquet unique et applique toutes les règles.

        Paramètres :
            info (dict) : dictionnaire produit par Sniffer._traiter_paquet()
        """
        self._detecter_scan_ports(info)
        self._detecter_brute_force(info)
        self._detecter_exfiltration(info)

    # ─────────────────────────────────────────────────────────
    # Règle 1 : Scan de ports
    # Un même IP source qui contacte beaucoup de ports différents
    # sur une courte fenêtre de temps = scan probable.
    # ─────────────────────────────────────────────────────────
    def _detecter_scan_ports(self, info):
        if info["port_destination"] is None:
            return

        ip_source = info["ip_source"]
        maintenant = time.time()
        historique = self._ports_par_ip[ip_source]

        historique.append((maintenant, info["port_destination"]))

        # Purge des entrées trop anciennes (hors fenêtre de temps)
        while historique and maintenant - historique[0][0] > self.fenetre_scan:
            historique.popleft()

        ports_distincts = {port for (_, port) in historique}

        if len(ports_distincts) >= self.seuil_scan_ports:
            self._creer_alerte(
                ip_source=ip_source,
                type_menace="Scan de ports",
                criticite="warning",
                details=(
                    f"{len(ports_distincts)} ports distincts contactés "
                    f"en {self.fenetre_scan}s depuis {ip_source}"
                )
            )
            historique.clear()  # évite le spam d'alertes répétées

    # ─────────────────────────────────────────────────────────
    # Règle 2 : Brute-force
    # Beaucoup de tentatives de connexion vers le même port
    # (ex: 22=SSH, 3389=RDP, 21=FTP) depuis la même IP.
    # ─────────────────────────────────────────────────────────
    def _detecter_brute_force(self, info):
        if info["protocole"] != "tcp" or info["port_destination"] is None:
            return

        ports_sensibles = {21, 22, 23, 3389, 3306, 5432}
        if info["port_destination"] not in ports_sensibles:
            return

        # Une tentative = paquet avec flag SYN (nouvelle connexion)
        if info["flags_tcp"] is None or "S" not in info["flags_tcp"]:
            return

        cle = (info["ip_source"], info["port_destination"])
        maintenant = time.time()
        historique = self._tentatives_par_ip_port[cle]

        historique.append(maintenant)

        while historique and maintenant - historique[0] > self.fenetre_brute_force:
            historique.popleft()

        if len(historique) >= self.seuil_brute_force:
            self._creer_alerte(
                ip_source=info["ip_source"],
                type_menace="Tentative de brute-force",
                criticite="critique",
                details=(
                    f"{len(historique)} tentatives de connexion vers le port "
                    f"{info['port_destination']} en {self.fenetre_brute_force}s "
                    f"depuis {info['ip_source']}"
                )
            )
            historique.clear()

    # ─────────────────────────────────────────────────────────
    # Règle 3 : Exfiltration / volume anormal
    # Volume de données sortantes anormalement élevé vers une
    # même IP destination (fuite de données potentielle).
    # ─────────────────────────────────────────────────────────
    def _detecter_exfiltration(self, info):
        ip_destination = info["ip_destination"]
        taille_mo = info["taille"] / (1024 * 1024)

        self._volume_sortant_par_ip[ip_destination] += taille_mo

        if self._volume_sortant_par_ip[ip_destination] >= self.seuil_exfiltration_mo:
            self._creer_alerte(
                ip_source=ip_destination,  # ici l'IP "suspecte" est la destination
                type_menace="Volume de données anormal (exfiltration possible)",
                criticite="critique",
                details=(
                    f"{self._volume_sortant_par_ip[ip_destination]:.1f} Mo envoyés "
                    f"vers {ip_destination} durant la session"
                )
            )
            self._volume_sortant_par_ip[ip_destination] = 0.0  # reset après alerte

    # ─────────────────────────────────────────────────────────
    # Création et journalisation des alertes
    # ─────────────────────────────────────────────────────────
    def _creer_alerte(self, ip_source, type_menace, criticite, details):
        """
        Enregistre une alerte en base (table alerts, liée à la session),
        la journalise dans history_log (visible dans HistoryView), et
        l'ajoute au cache local pour affichage temps réel.
        """
        executer_requete(
            """INSERT INTO alerts (session_id, ip_source, type_menace, criticite, details)
               VALUES (%s, %s, %s, %s, %s)""",
            (self.session_id, ip_source, type_menace, criticite, details),
            commit=True
        )

        logger_alerte(ip_source, type_menace, criticite, details)

        alerte = {
            "horodatage": datetime.now(),
            "ip_source": ip_source,
            "type_menace": type_menace,
            "criticite": criticite,
            "details": details,
        }
        self._alertes_recentes.append(alerte)
        return alerte

    def recuperer_alertes_recentes(self):
        """
        Retourne les alertes générées durant cette session (cache
        local, pour affichage temps réel dans la GUI sans requêter
        la base à chaque rafraîchissement).

        Retourne :
            list[dict] : alertes les plus récentes en premier
        """
        return list(reversed(self._alertes_recentes))


if __name__ == "__main__":
    # Test manuel simplifié (sans vraie capture réseau)
    moteur = MoteurIDS(session_id=1)

    # Simulation d'un scan de ports
    for port in range(1, 20):
        moteur.analyser_paquet({
            "ip_source": "192.168.1.50",
            "ip_destination": "192.168.1.10",
            "port_destination": port,
            "protocole": "tcp",
            "flags_tcp": "S",
            "taille": 60,
        })

    for alerte in moteur.recuperer_alertes_recentes():
        print(alerte)