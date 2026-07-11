# =============================================================
# gui/monitor_view.py — Surveillance réseau en temps réel
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Cette vue affiche le trafic réseau capturé en direct (via
# sniffer.py / Scapy), un compteur de paquets par protocole, et
# un bouton Start/Stop pour la capture. Chaque paquet capturé est
# transmis à ids_engine.py (MoteurIDS) qui applique les règles de
# détection et enregistre les alertes en base (remontées ensuite
# dans alerts_view.py). Au démarrage de la capture, une nouvelle
# ligne est créée dans la table sessions ; elle est clôturée à
# l'arrêt de la capture.
# =============================================================

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from gui import theme
from sniffer import Sniffer
from ids_engine import MoteurIDS
from db import executer_requete, executer_requete_rapide


class MonitorView(tk.Frame):
    """
    Vue de surveillance réseau en temps réel.

    Utilisation typique (dans main_view.py) :
        monitor_view = MonitorView(parent, utilisateur=utilisateur)
        monitor_view.pack(fill="both", expand=True)
    """

    INTERVALLE_RAFRAICHISSEMENT_MS = 300  # fréquence de lecture de la file de paquets

    def __init__(self, parent, utilisateur):
        super().__init__(parent)
        self.utilisateur = utilisateur

        self.sniffer = None
        self.moteur_ids = None
        self.session_id = None
        self.capture_active = False
        self._tache_rafraichissement = None

        self.compteurs_protocole = {"tcp": 0, "udp": 0, "autre": 0}
        self.total_paquets = 0

        self._construire_interface()
        self.appliquer_theme()

        # ── Arrêt propre de la capture si la vue est détruite ──
        # (ex: déconnexion via ProfileView -> app.py détruit MainView
        # -> détruit toutes les sous-vues, dont celle-ci)
        self.bind("<Destroy>", self._sur_destruction)

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── En-tête : titre + bouton start/stop ──────────────
        self.zone_entete = tk.Frame(self)
        self.zone_entete.pack(fill="x", padx=25, pady=(20, 10))

        self.label_titre = tk.Label(self.zone_entete, text="Surveillance réseau")
        self.label_titre.pack(side="left")

        self.bouton_capture = tk.Button(
            self.zone_entete, text="▶ Démarrer la capture",
            command=self._basculer_capture, relief="flat", cursor="hand2"
        )
        self.bouton_capture.pack(side="right")

        self.label_statut = tk.Label(self.zone_entete, text="● Arrêtée")
        self.label_statut.pack(side="right", padx=(0, 15))

        # ── Cartes de compteurs par protocole ────────────────
        self.zone_compteurs = tk.Frame(self)
        self.zone_compteurs.pack(fill="x", padx=25, pady=(0, 15))

        self._cartes_protocole = {}
        for cle, libelle in (("tcp", "TCP"), ("udp", "UDP"), ("autre", "Autre")):
            carte = tk.Frame(self.zone_compteurs)
            carte.pack(side="left", fill="x", expand=True, padx=5)

            label_nom = tk.Label(carte, text=libelle)
            label_nom.pack(pady=(10, 0))

            label_valeur = tk.Label(carte, text="0")
            label_valeur.pack(pady=(0, 10))

            self._cartes_protocole[cle] = {"carte": carte, "nom": label_nom, "valeur": label_valeur}

        # ── Tableau du flux de paquets en direct ─────────────
        self.zone_tableau = tk.Frame(self)
        self.zone_tableau.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        colonnes = ("heure", "source", "destination", "protocole", "taille", "info")
        self.tableau_paquets = ttk.Treeview(
            self.zone_tableau, columns=colonnes, show="headings", height=18
        )

        entetes = {
            "heure": "Heure", "source": "Source", "destination": "Destination",
            "protocole": "Protocole", "taille": "Taille", "info": "Info"
        }
        largeurs = {
            "heure": 90, "source": 150, "destination": 150,
            "protocole": 90, "taille": 80, "info": 250
        }
        for col in colonnes:
            self.tableau_paquets.heading(col, text=entetes[col])
            self.tableau_paquets.column(col, width=largeurs[col], anchor="w")

        barre_defilement = ttk.Scrollbar(
            self.zone_tableau, orient="vertical", command=self.tableau_paquets.yview
        )
        self.tableau_paquets.configure(yscrollcommand=barre_defilement.set)

        self.tableau_paquets.pack(side="left", fill="both", expand=True)
        barre_defilement.pack(side="right", fill="y")

    # ─────────────────────────────────────────────────────────
    # Capture start/stop
    # ─────────────────────────────────────────────────────────
    def _basculer_capture(self):
        if self.capture_active:
            self._arreter_capture()
        else:
            self._demarrer_capture()

        self._appliquer_couleur_statut()

    def _demarrer_capture(self):
        """Crée une nouvelle session en base, démarre le sniffer et le moteur IDS."""
        self.session_id = executer_requete(
            "INSERT INTO sessions (user_id, mode) VALUES (%s, %s)",
            (self.utilisateur.get("id"), "passif"),
            commit=True,
            retour_id=True
        )

        self.moteur_ids = MoteurIDS(session_id=self.session_id)
        self.sniffer = Sniffer()
        self.sniffer.demarrer()

        self.capture_active = True
        self.bouton_capture.config(text="⏹ Arrêter la capture")
        self.label_statut.config(text="● En cours")

        self._planifier_rafraichissement()

    def _arreter_capture(self):
        """Arrête le sniffer, annule le rafraîchissement, clôture la session."""
        if self.sniffer is not None:
            self.sniffer.arreter()

        if self._tache_rafraichissement is not None:
            self.after_cancel(self._tache_rafraichissement)
            self._tache_rafraichissement = None

        if self.session_id is not None:
            executer_requete(
                "UPDATE sessions SET ended_at = NOW() WHERE id = %s",
                (self.session_id,),
                commit=True
            )

        self.capture_active = False
        self.bouton_capture.config(text="▶ Démarrer la capture")
        self.label_statut.config(text="● Arrêtée")

    def _sur_destruction(self, event):
        """
        Appelée automatiquement quand ce widget est détruit (ex: à la
        déconnexion). Garantit que la capture et le thread associé
        s'arrêtent proprement plutôt que de continuer en arrière-plan.
        """
        if event.widget is self and self.capture_active:
            self._arreter_capture()

    # ─────────────────────────────────────────────────────────
    # Boucle de lecture de la file de paquets (thread-safe via after())
    # ─────────────────────────────────────────────────────────
    def _planifier_rafraichissement(self):
        self._lire_file_paquets()
        self._tache_rafraichissement = self.after(
            self.INTERVALLE_RAFRAICHISSEMENT_MS, self._planifier_rafraichissement
        )

    def _lire_file_paquets(self):
        """
        Vide la file de paquets remplie par Sniffer (thread séparé) et
        traite chaque paquet : affichage dans le tableau + analyse IDS.
        Sniffer.file_paquets est une queue.Queue thread-safe, donc
        get_nowait() ici (dans le thread principal Tkinter) est sûr.
        """
        if self.sniffer is None:
            return

        while True:
            try:
                paquet_info = self.sniffer.file_paquets.get_nowait()
            except Exception:
                break
            self._traiter_paquet(paquet_info)

    def _traiter_paquet(self, info):
        """
        Paramètres :
            info (dict) : format produit par Sniffer._traiter_paquet()
                {"horodatage", "ip_source", "ip_destination", "taille",
                "protocole", "port_source", "port_destination", "flags_tcp"}
        """
        # ── Affichage dans le tableau ─────────────────────────
        heure = info["horodatage"].strftime("%H:%M:%S") if info.get("horodatage") else ""
        protocole = info.get("protocole") or "autre"
        info_detail = ""
        if info.get("port_source") is not None and info.get("port_destination") is not None:
            info_detail = f"{info['port_source']} → {info['port_destination']}"

        self.tableau_paquets.insert("", 0, values=(
            heure,
            info.get("ip_source", ""),
            info.get("ip_destination", ""),
            protocole.upper(),
            info.get("taille", ""),
            info_detail,
        ))

        enfants = self.tableau_paquets.get_children()
        if len(enfants) > 500:
            self.tableau_paquets.delete(enfants[-1])

        if protocole not in self.compteurs_protocole:
            protocole = "autre"
        self.compteurs_protocole[protocole] += 1
        self.total_paquets += 1
        self._cartes_protocole[protocole]["valeur"].config(text=str(self.compteurs_protocole[protocole]))

        # ── Sauvegarde en base ────────────────────────────────
        # ── Sauvegarde en base ────────────────────────────────
        if self.session_id is not None:
            executer_requete_rapide(
                """INSERT INTO captured_packets
                (session_id, horodatage, ip_source, ip_destination,
                    protocole, port_source, port_destination, taille, flags_tcp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    self.session_id,
                    info.get("horodatage"),
                    info.get("ip_source"),
                    info.get("ip_destination"),
                    info.get("protocole"),
                    info.get("port_source"),
                    info.get("port_destination"),
                    info.get("taille"),
                    info.get("flags_tcp"),
                )
            )

        # ── Analyse IDS ────────────────────────────────────────
        if self.moteur_ids is not None:
            self.moteur_ids.analyser_paquet(info)

        # ─────────────────────────────────────────────────────────
        # Statut visuel
    # ─────────────────────────────────────────────────────────
    def _appliquer_couleur_statut(self):
        couleurs = theme.get_colors()
        couleur = couleurs["emeraude"] if self.capture_active else couleurs["texte_secondaire"]
        self.label_statut.config(fg=couleur)

    # ─────────────────────────────────────────────────────────
    # Rafraîchissement (appelé par main_view.py à chaque affichage)
    # ─────────────────────────────────────────────────────────
    def rafraichir_donnees(self):
        """
        Rien à recharger depuis la BDD ici — le flux est déjà en
        direct via la file de paquets. Présente uniquement pour
        respecter l'interface attendue par main_view.py (hasattr check).
        """
        pass

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def appliquer_theme(self):
        couleurs = theme.get_colors()

        self.config(bg=couleurs["fond"])
        self.zone_entete.config(bg=couleurs["fond"])
        self.zone_compteurs.config(bg=couleurs["fond"])
        self.zone_tableau.config(bg=couleurs["fond"])

        self.label_titre.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("titre_petit"))
        self.label_statut.config(bg=couleurs["fond"], font=theme.get_font("texte_petit"))

        self.bouton_capture.config(
            bg=couleurs["emeraude"], fg="#FFFFFF",
            activebackground=couleurs["emeraude"], font=theme.get_font("bouton")
        )

        for infos in self._cartes_protocole.values():
            infos["carte"].config(bg=couleurs["fond_carte"], highlightbackground=couleurs["bordure"], highlightthickness=1)
            infos["nom"].config(bg=couleurs["fond_carte"], fg=couleurs["texte_secondaire"], font=theme.get_font("texte_petit"))
            infos["valeur"].config(bg=couleurs["fond_carte"], fg=couleurs["emeraude"], font=theme.get_font("titre_petit"))

        self._appliquer_couleur_statut()

        # Style ttk (Treeview) — nécessite un objet Style, pas de .config direct
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=couleurs["fond_carte"], foreground=couleurs["texte"],
            fieldbackground=couleurs["fond_carte"], rowheight=26,
            font=theme.get_font("texte_petit")
        )
        style.configure(
            "Treeview.Heading",
            background=couleurs["fond"], foreground=couleurs["texte"],
            font=theme.get_font("texte")
        )
        style.map("Treeview", background=[("selected", couleurs["emeraude"])])


if __name__ == "__main__":
    # Test manuel : python -m gui.monitor_view (nécessite droits administrateur)
    root = tk.Tk()
    root.title("NetSentinel — Test MonitorView")
    root.geometry("1000x650")

    utilisateur_test = {"id": 1, "username": "test_admin"}
    vue = MonitorView(root, utilisateur=utilisateur_test)
    vue.pack(fill="both", expand=True)

    root.mainloop()