# =============================================================
# gui/sidebar.py — Menu latéral de navigation
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Ce module affiche le menu latéral gauche : logo, infos
# utilisateur, boutons de navigation vers les sous-vues, et
# bouton de bascule de thème. Ne contient aucune logique métier
# — uniquement de la navigation et de l'affichage.
# =============================================================

import tkinter as tk

from gui import theme


class Sidebar(tk.Frame):
    """
    Menu latéral affiché en permanence dans MainView.

    Utilisation typique (dans main_view.py) :
        sidebar = Sidebar(parent, utilisateur=utilisateur,
                           on_navigation=self.afficher_sous_vue,
                           on_theme_change=self._rafraichir_toutes_les_vues)
        sidebar.pack(side="left", fill="y")
    """

    ITEMS_MENU = [
        ("monitor", "🖥️", "Surveillance"),
        ("alerts", "🚨", "Alertes"),
        ("blacklist", "⛔", "Liste noire"),
        ("history", "📜", "Historique"),
        ("profile", "👤", "Profil"),
    ]

    def __init__(self, parent, utilisateur, on_navigation, on_theme_change):
        """
        Paramètres :
            parent : conteneur Tkinter parent
            utilisateur (dict) : {"id", "username", "email"}
            on_navigation (callable) : appelé avec nom_vue (str) au clic sur un item
            on_theme_change (callable) : appelé après bascule du thème
        """
        super().__init__(parent, width=220)
        self.pack_propagate(False)

        self.utilisateur = utilisateur
        self.on_navigation = on_navigation
        self.on_theme_change = on_theme_change

        self._boutons_menu = {}

        self._construire_interface()
        self.appliquer_theme()

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── En-tête : logo + nom de l'app ────────────────────
        self.zone_entete = tk.Frame(self)
        self.zone_entete.pack(fill="x", pady=(20, 10), padx=15)

        self.label_logo = tk.Label(self.zone_entete, text="🛡️ NetSentinel")
        self.label_logo.pack(anchor="w")

        # ── Bloc utilisateur ──────────────────────────────────
        self.zone_utilisateur = tk.Frame(self)
        self.zone_utilisateur.pack(fill="x", pady=(0, 20), padx=15)

        self.label_username = tk.Label(
            self.zone_utilisateur,
            text=f"👋 {self.utilisateur.get('username', '')}"
        )
        self.label_username.pack(anchor="w")

        # ── Séparateur ────────────────────────────────────────
        self.separateur_haut = tk.Frame(self, height=1)
        self.separateur_haut.pack(fill="x", padx=15, pady=(0, 10))

        # ── Boutons de navigation ─────────────────────────────
        self.zone_menu = tk.Frame(self)
        self.zone_menu.pack(fill="x", padx=10)

        for nom_vue, icone, libelle in self.ITEMS_MENU:
            bouton = tk.Button(
                self.zone_menu,
                text=f"  {icone}   {libelle}",
                anchor="w",
                relief="flat",
                cursor="hand2",
                command=lambda n=nom_vue: self._selectionner(n)
            )
            bouton.pack(fill="x", pady=2)
            self._boutons_menu[nom_vue] = bouton

        # ── Zone basse : thème + version ─────────────────────
        self.zone_basse = tk.Frame(self)
        self.zone_basse.pack(side="bottom", fill="x", padx=15, pady=15)

        self.separateur_bas = tk.Frame(self.zone_basse, height=1)
        self.separateur_bas.pack(fill="x", pady=(0, 10))

        self.bouton_theme = tk.Button(
            self.zone_basse,
            text="🌙  Mode sombre",
            anchor="w",
            relief="flat",
            cursor="hand2",
            command=self._basculer_theme
        )
        self.bouton_theme.pack(fill="x")

        self.label_version = tk.Label(self.zone_basse, text="v1.0")
        self.label_version.pack(anchor="w", pady=(8, 0))

    # ─────────────────────────────────────────────────────────
    # Navigation
    # ─────────────────────────────────────────────────────────
    def _selectionner(self, nom_vue):
        """Appelé au clic sur un item de menu — délègue à MainView."""
        self.on_navigation(nom_vue)

    def mettre_a_jour_selection(self, nom_vue):
        """
        Appelée par MainView après changement de sous-vue, pour
        mettre en évidence visuellement l'item actif dans le menu.
        """
        couleurs = theme.get_colors()
        for nom, bouton in self._boutons_menu.items():
            if nom == nom_vue:
                bouton.config(bg=couleurs["emeraude"], fg="#FFFFFF")
            else:
                bouton.config(bg=couleurs["fond"], fg=couleurs["texte"])

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def _basculer_theme(self):
        theme.toggle_theme()
        self.appliquer_theme()
        self.on_theme_change()

    def appliquer_theme(self):
        couleurs = theme.get_colors()

        self.config(bg=couleurs["fond_carte"])
        for zone in (self.zone_entete, self.zone_utilisateur, self.zone_menu, self.zone_basse):
            zone.config(bg=couleurs["fond_carte"])

        self.label_logo.config(
            bg=couleurs["fond_carte"], fg=couleurs["emeraude"],
            font=theme.get_font("titre_petit")
        )
        self.label_username.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            font=theme.get_font("texte")
        )

        for separateur in (self.separateur_haut, self.separateur_bas):
            separateur.config(bg=couleurs["bordure"])

        for bouton in self._boutons_menu.values():
            bouton.config(
                bg=couleurs["fond_carte"], fg=couleurs["texte"],
                activebackground=couleurs["emeraude"],
                font=theme.get_font("texte"), bd=0
            )

        # Réapplique la sélection active (si menu déjà utilisé)
        self.mettre_a_jour_selection(getattr(self, "_derniere_selection", "monitor"))

        self.bouton_theme.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            activebackground=couleurs["fond_carte"], font=theme.get_font("texte")
        )
        self.label_version.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte_secondaire"],
            font=theme.get_font("texte_petit")
        )

        icone_theme = "🌙  Mode sombre" if theme.get_current_mode() == "clair" else "☀️  Mode clair"
        self.bouton_theme.config(text=icone_theme)


if __name__ == "__main__":
    # Test manuel : python -m gui.sidebar
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