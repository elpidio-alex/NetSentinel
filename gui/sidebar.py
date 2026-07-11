"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# gui/sidebar.py — Menu latéral de navigation
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================

import tkinter as tk
from gui import theme

try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False


class Sidebar(tk.Frame):

    LARGEUR_DEPLIEE = 220
    LARGEUR_REPLIEE = 52

    ITEMS_MENU = [
        ("monitor",   "🖥️",  "Surveillance"),
        ("alerts",    "🚨",  "Alertes"),
        ("blacklist", "⛔",  "Liste noire"),
        ("history",   "📜",  "Historique"),
        ("profile",   "👤",  "Profil"),
    ]

    def __init__(self, parent, utilisateur, on_navigation, on_theme_change):
        super().__init__(parent, width=self.LARGEUR_DEPLIEE)
        self.pack_propagate(False)

        self.utilisateur = utilisateur
        self.on_navigation = on_navigation
        self.on_theme_change = on_theme_change

        self._boutons_menu = {}
        self._replie = False
        self._derniere_selection = "monitor"

        self._construire_interface()
        self.appliquer_theme()

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── Bouton hamburger ──────────────────────────────────
        self.zone_hamburger = tk.Frame(self)
        self.zone_hamburger.pack(fill="x", pady=(12, 0), padx=8)

        self.bouton_hamburger = tk.Button(
            self.zone_hamburger, text="☰",
            command=self._basculer_repli,
            relief="flat", cursor="hand2", bd=0,
            font=("Times New Roman", 16)
        )
        self.bouton_hamburger.pack(anchor="w", padx=4)

        # ── Séparateur ────────────────────────────────────────
        self.separateur_haut = tk.Frame(self, height=1)
        self.separateur_haut.pack(fill="x", padx=8, pady=(8, 6))

        # ── Boutons de navigation ─────────────────────────────
        self.zone_menu = tk.Frame(self)
        self.zone_menu.pack(fill="x", padx=4, pady=(4, 0))

        for nom_vue, icone, libelle in self.ITEMS_MENU:
            bouton = tk.Button(
                self.zone_menu,
                text=f"  {icone}   {libelle}",
                anchor="w",
                relief="flat",
                cursor="hand2",
                command=lambda n=nom_vue: self._selectionner(n)
            )
            bouton.pack(fill="x", pady=2, ipady=6)
            self._boutons_menu[nom_vue] = bouton

        # ── Zone basse : utilisateur + déconnexion ────────────
        self.zone_basse = tk.Frame(self)
        self.zone_basse.pack(side="bottom", fill="x", padx=8, pady=(0, 12))

        self.separateur_bas = tk.Frame(self.zone_basse, height=1)
        self.separateur_bas.pack(fill="x", pady=(0, 10))

        # Infos utilisateur
        self.label_username = tk.Label(
            self.zone_basse,
            text=f"👤  {self.utilisateur.get('username', '')}",
            anchor="w"
        )
        self.label_username.pack(fill="x", pady=(0, 6))

        # Bouton déconnexion (via profile_view, remonte à app.py)
        self.bouton_theme = tk.Button(
            self.zone_basse,
            text="🌙  Mode sombre",
            anchor="w",
            relief="flat",
            cursor="hand2",
            command=self._basculer_theme
        )
        self.bouton_theme.pack(fill="x", pady=(0, 4))

        self.label_version = tk.Label(self.zone_basse, text="v3.0", anchor="w")
        self.label_version.pack(fill="x")

    # ─────────────────────────────────────────────────────────
    # Repliage / dépliage
    # ─────────────────────────────────────────────────────────
    def _basculer_repli(self):
        self._replie = not self._replie

        if self._replie:
            self.config(width=self.LARGEUR_REPLIEE)

            # Boutons : icône seule, centrée
            for nom_vue, icone, _ in self.ITEMS_MENU:
                self._boutons_menu[nom_vue].config(
                    text=icone, anchor="center"
                )

            # Zone basse : icône utilisateur seule
            self.label_username.config(text="👤", anchor="center")
            self.bouton_theme.config(text="🌙" if theme.get_current_mode() == "clair" else "☀️",
                                     anchor="center")
            self.label_version.config(text="")

        else:
            self.config(width=self.LARGEUR_DEPLIEE)

            # Boutons : icône + libellé
            for nom_vue, icone, libelle in self.ITEMS_MENU:
                self._boutons_menu[nom_vue].config(
                    text=f"  {icone}   {libelle}", anchor="w"
                )

            # Zone basse : infos complètes
            self.label_username.config(
                text=f"👤  {self.utilisateur.get('username', '')}",
                anchor="w"
            )
            icone_theme = "🌙  Mode sombre" if theme.get_current_mode() == "clair" else "☀️  Mode clair"
            self.bouton_theme.config(text=icone_theme, anchor="w")
            self.label_version.config(text="v3.0")

        self.mettre_a_jour_selection(self._derniere_selection)

    # ─────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────
    def _selectionner(self, nom_vue):
        self._derniere_selection = nom_vue
        self.on_navigation(nom_vue)

    def mettre_a_jour_selection(self, nom_vue):
        self._derniere_selection = nom_vue
        couleurs = theme.get_colors()
        for nom, bouton in self._boutons_menu.items():
            if nom == nom_vue:
                bouton.config(bg=couleurs["emeraude"], fg="#FFFFFF",
                              activebackground=couleurs["emeraude"])
            else:
                bouton.config(bg=couleurs["fond_carte"], fg=couleurs["texte"],
                              activebackground=couleurs["emeraude"])

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def _basculer_theme(self):
        theme.toggle_theme()
        self.appliquer_theme()
        self.on_theme_change()

    def appliquer_theme(self):
        # Sidebar toujours sombre, indépendante du thème global
        FOND        = "#0f1b2d"
        TEXTE       = "#FFFFFF"
        BORDURE     = "#1e2d3d"
        TEXTE_SEC   = "#8899aa"

        self.config(bg=FOND)

        for zone in (self.zone_hamburger, self.zone_menu, self.zone_basse):
            zone.config(bg=FOND)

        self.bouton_hamburger.config(
            bg=FOND, fg=TEXTE,
            activebackground=FOND
        )

        self.separateur_haut.config(bg=BORDURE)
        self.separateur_bas.config(bg=BORDURE)

        couleurs = theme.get_colors()
        for nom, bouton in self._boutons_menu.items():
            bouton.config(
                bg=FOND, fg=TEXTE,
                activebackground=couleurs["emeraude"],
                font=theme.get_font("texte"), bd=0
            )

        self.mettre_a_jour_selection(self._derniere_selection)

        self.label_username.config(
            bg=FOND, fg=TEXTE,
            font=theme.get_font("texte")
        )

        icone_theme = "🌙  Mode sombre" if theme.get_current_mode() == "clair" else "☀️  Mode clair"
        if self._replie:
            icone_theme = "🌙" if theme.get_current_mode() == "clair" else "☀️"

        self.bouton_theme.config(
            bg=FOND, fg=TEXTE,
            activebackground=FOND,
            font=theme.get_font("texte"),
            text=icone_theme
        )

        self.label_version.config(
            bg=FOND, fg=TEXTE_SEC,
            font=theme.get_font("texte_petit")
        )


if __name__ == "__main__":
    root = tk.Tk()
    root.title("NetSentinel — Test Sidebar")
    root.geometry("300x600")

    utilisateur_test = {"id": 1, "username": "test_admin"}
    sidebar = Sidebar(
        root, utilisateur=utilisateur_test,
        on_navigation=lambda n: print("Navigation vers :", n),
        on_theme_change=lambda: print("Thème changé")
    )
    sidebar.pack(side="left", fill="y")
    root.mainloop()