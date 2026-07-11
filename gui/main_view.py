# =============================================================
# gui/main_view.py — Conteneur principal post-connexion
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Cette vue s'affiche après connexion réussie. Elle assemble la
# sidebar (menu latéral) et une zone de contenu dynamique où
# s'affichent les différentes sous-vues (monitor, alerts,
# blacklist, history, profile) selon le bouton cliqué.
# =============================================================

import tkinter as tk

from gui import theme
from gui.sidebar import Sidebar
from gui.monitor_view import MonitorView
from gui.alerts_view import AlertsView
from gui.blacklist_view import BlacklistView
from gui.history_view import HistoryView
from gui.profile_view import ProfileView


class MainView(tk.Frame):
    """
    Conteneur principal de l'application après connexion.

    Utilisation typique (dans app.py) :
        main_view = MainView(parent, utilisateur=utilisateur_connecte,
                              on_deconnexion=self._deconnexion)
        main_view.pack(fill="both", expand=True)
    """

    def __init__(self, parent, utilisateur, on_deconnexion):
        """
        Paramètres :
            parent : conteneur Tkinter parent
            utilisateur (dict) : {"id", "username", "email"} — retourné par auth.py
            on_deconnexion (callable) : appelé quand l'utilisateur se déconnecte
                (transmis jusqu'à ProfileView, remonté jusqu'à app.py)
        """
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.on_deconnexion = on_deconnexion

        # ── Sous-vues disponibles, créées une seule fois ─────
        self._sous_vues = {}
        self._vue_active = None

        self._construire_interface()
        self.appliquer_theme()
        self.afficher_sous_vue("monitor")

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── Sidebar (menu latéral gauche) ────────────────────
        self.sidebar = Sidebar(
            self,
            utilisateur=self.utilisateur,
            on_navigation=self.afficher_sous_vue,
            on_theme_change=self._rafraichir_toutes_les_vues
        )
        self.sidebar.pack(side="left", fill="y")

        # ── Zone de contenu dynamique (droite) ───────────────
        self.zone_contenu = tk.Frame(self)
        self.zone_contenu.pack(side="right", fill="both", expand=True)

        # ── Instanciation des sous-vues (une seule fois, réutilisées) ──
        self._sous_vues["monitor"] = MonitorView(self.zone_contenu, utilisateur=self.utilisateur)
        self._sous_vues["alerts"] = AlertsView(self.zone_contenu, utilisateur=self.utilisateur)
        self._sous_vues["blacklist"] = BlacklistView(self.zone_contenu, utilisateur=self.utilisateur)
        self._sous_vues["history"] = HistoryView(self.zone_contenu, utilisateur=self.utilisateur)
        self._sous_vues["profile"] = ProfileView(
            self.zone_contenu, utilisateur=self.utilisateur,
            on_deconnexion=self.on_deconnexion
        )

    # ─────────────────────────────────────────────────────────
    # Navigation entre sous-vues
    # ─────────────────────────────────────────────────────────
    def afficher_sous_vue(self, nom_vue):
        """
        Affiche la sous-vue demandée et masque la précédente.

        Paramètres :
            nom_vue (str) : "monitor", "alerts", "blacklist", "history", "profile"
        """
        if nom_vue not in self._sous_vues:
            return

        if self._vue_active is not None:
            self._sous_vues[self._vue_active].pack_forget()

        vue = self._sous_vues[nom_vue]
        vue.pack(fill="both", expand=True)
        self._vue_active = nom_vue

        self.sidebar.mettre_a_jour_selection(nom_vue)

        # Rafraîchit les données de la vue à chaque affichage
        # (ex: alerts_view recharge les dernières alertes depuis la BDD)
        if hasattr(vue, "rafraichir_donnees"):
            vue.rafraichir_donnees()

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def _rafraichir_toutes_les_vues(self):
        """
        Appelée par la sidebar quand l'utilisateur bascule le thème.
        Reconstruit les couleurs de toutes les vues (actives ou non),
        pour que le changement soit instantané partout, même en
        naviguant ensuite vers une vue non encore affichée.
        """
        self.appliquer_theme()
        for vue in self._sous_vues.values():
            vue.appliquer_theme()

    def appliquer_theme(self):
        couleurs = theme.get_colors()
        self.config(bg=couleurs["fond"])
        self.zone_contenu.config(bg=couleurs["fond"])
        self.sidebar.appliquer_theme()


if __name__ == "__main__":
    # Test manuel : python -m gui.main_view
    root = tk.Tk()
    root.title("NetSentinel — Test MainView")
    root.geometry("1100x650")

    utilisateur_test = {"id": 1, "username": "test_admin", "email": "test@netsentinel.local"}
    vue = MainView(
        root, utilisateur=utilisateur_test,
        on_deconnexion=lambda: print("Déconnexion demandée")
    )
    vue.pack(fill="both", expand=True)

    root.mainloop()