"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# gui/app.py — Classe principale de l'application NetSentinel
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Cette classe encapsule la fenêtre racine Tkinter et gère la
# bascule entre l'écran de connexion (LoginView) et le conteneur
# principal post-connexion (MainView), y compris la déconnexion
# (retour à l'écran de login). Aucune logique métier ici —
# uniquement l'assemblage et la navigation au plus haut niveau.
# =============================================================

import tkinter as tk
from tkinter import messagebox

from gui import theme
from gui.login_view import LoginView
from gui.main_view import MainView
from db import tester_connexion


class App:
    """
    Point d'assemblage principal de NetSentinel.

    Utilisation typique (dans main.py) :
        app = App()
        app.run()
    """

    LARGEUR_FENETRE = 1100
    HAUTEUR_FENETRE = 650

    def __init__(self):
        self.root = tk.Tk()
        try:
            self.root.iconbitmap("assets/netsentinel.ico")
        except Exception:
            pass
        self.root.title("NetSentinel — Surveillance réseau et défense automatisée")
        self.root.geometry(f"{self.LARGEUR_FENETRE}x{self.HAUTEUR_FENETRE}")
        self.root.minsize(900, 550)

        self._vue_actuelle = None

        self._verifier_base_de_donnees()
        self._afficher_login()

    # ─────────────────────────────────────────────────────────
    # Vérification de la base de données au démarrage
    # ─────────────────────────────────────────────────────────
    def _verifier_base_de_donnees(self):
        """
        Vérifie que la connexion à netsentinel_db fonctionne avant
        d'afficher quoi que ce soit. Affiche un message clair et
        bloquant si la base n'est pas accessible, plutôt que de
        laisser l'application planter plus tard sans explication.
        """
        if not tester_connexion():
            messagebox.showerror(
                "Erreur de connexion",
                "Impossible de se connecter à la base de données netsentinel_db.\n\n"
                "Vérifiez que MySQL est démarré et que le fichier .env contient "
                "les bons identifiants (MYSQL_USER, MYSQL_PASSWORD)."
            )

    # ─────────────────────────────────────────────────────────
    # Navigation entre écrans (login <-> main)
    # ─────────────────────────────────────────────────────────
    def _afficher_login(self):
        """Affiche l'écran de connexion/inscription."""
        self._changer_vue(
            LoginView(self.root, on_connexion_reussie=self._afficher_main_view)
        )

    def _afficher_main_view(self, utilisateur):
        """
        Appelée par LoginView après une connexion réussie.

        Paramètres :
            utilisateur (dict) : {"id", "username", "email"}
        """
        self._changer_vue(
            MainView(self.root, utilisateur=utilisateur, on_deconnexion=self._deconnexion)
        )

    def _deconnexion(self):
        """
        Appelée par MainView (via ProfileView) lors d'une déconnexion.
        Revient à l'écran de login sans fermer l'application.
        """
        self._afficher_login()

    def _changer_vue(self, nouvelle_vue):
        """Détruit la vue actuelle (si présente) et affiche la nouvelle."""
        if self._vue_actuelle is not None:
            self._vue_actuelle.destroy()

        self._vue_actuelle = nouvelle_vue
        self._vue_actuelle.pack(fill="both", expand=True)

    # ─────────────────────────────────────────────────────────
    # Lancement
    # ─────────────────────────────────────────────────────────
    def run(self):
        """Démarre la boucle principale Tkinter."""
        self.root.mainloop()