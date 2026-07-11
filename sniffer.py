"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# sniffer.py — Capture réseau en temps réel (Scapy)
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Ce module capture les paquets réseau dans un thread séparé
# (pour ne jamais bloquer l'interface Tkinter) et transmet
# chaque paquet pertinent à ids_engine.py via une file (Queue)
# thread-safe.
# =============================================================

import threading
import queue
from datetime import datetime
from scapy.all import sniff, IP, TCP, UDP, get_if_list


class Sniffer:
    """
    Gère la capture réseau en arrière-plan.

    Utilisation typique (dans app.py ou monitor_view.py) :
        sniffer = Sniffer()
        sniffer.demarrer()
        ...
        paquet_info = sniffer.file_paquets.get_nowait()  # non-bloquant
        ...
        sniffer.arreter()
    """

    def __init__(self, interface=None):
        """
        Paramètres :
            interface (str|None) : nom de l'interface réseau à écouter.
                                    None = interface par défaut (auto).
        """
        self.interface = interface
        self.file_paquets = queue.Queue()
        self._thread = None
        self._en_cours = threading.Event()

    def _traiter_paquet(self, paquet):
        """
        Callback appelé par Scapy pour chaque paquet capturé.
        Extrait uniquement les informations utiles et les place
        dans la file — jamais de traitement lourd ici (le thread
        de capture doit rester rapide pour ne rater aucun paquet).
        """
        if not paquet.haslayer(IP):
            return

        info = {
            "horodatage": datetime.now(),
            "ip_source": paquet[IP].src,
            "ip_destination": paquet[IP].dst,
            "taille": len(paquet),
            "protocole": None,
            "port_source": None,
            "port_destination": None,
            "flags_tcp": None,
        }

        if paquet.haslayer(TCP):
            info["protocole"] = "tcp"
            info["port_source"] = paquet[TCP].sport
            info["port_destination"] = paquet[TCP].dport
            info["flags_tcp"] = str(paquet[TCP].flags)
        elif paquet.haslayer(UDP):
            info["protocole"] = "udp"
            info["port_source"] = paquet[UDP].sport
            info["port_destination"] = paquet[UDP].dport
        else:
            info["protocole"] = "autre"

        self.file_paquets.put(info)

    def _boucle_capture(self):
        """
        Boucle exécutée dans le thread de capture. sniff() est
        bloquant, donc on utilise stop_filter pour pouvoir
        l'arrêter proprement via l'Event _en_cours.
        """
        sniff(
            iface=self.interface,
            prn=self._traiter_paquet,
            store=False,
            stop_filter=lambda pkt: not self._en_cours.is_set()
        )

    def demarrer(self):
        """Démarre la capture dans un thread daemon séparé."""
        if self._thread is not None and self._thread.is_alive():
            return  # déjà en cours

        self._en_cours.set()
        self._thread = threading.Thread(target=self._boucle_capture, daemon=True)
        self._thread.start()

    def arreter(self):
        """
        Signale l'arrêt de la capture. Note : sniff() ne vérifie
        stop_filter qu'à la réception d'un nouveau paquet, donc
        l'arrêt peut prendre quelques secondes sur un réseau calme.
        """
        self._en_cours.clear()

    def est_actif(self):
        """Retourne True si la capture est actuellement en cours."""
        return self._en_cours.is_set()

    @staticmethod
    def lister_interfaces():
        """
        Retourne la liste des interfaces réseau disponibles sur
        la machine (utile pour un menu déroulant dans monitor_view.py).
        """
        try:
            return get_if_list()
        except Exception:
            return []


if __name__ == "__main__":
    # Test manuel : python sniffer.py (nécessite droits administrateur)
    import time

    print("Interfaces disponibles :", Sniffer.lister_interfaces())

    s = Sniffer()
    s.demarrer()
    print("Capture démarrée pendant 5 secondes...")
    time.sleep(5)
    s.arreter()

    print(f"Paquets capturés : {s.file_paquets.qsize()}")
    while not s.file_paquets.empty():
        print(s.file_paquets.get())