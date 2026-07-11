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
    LARGEUR_REPLIEE = 56

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

        self._charger_logo()
        self._construire_interface()
        self.appliquer_theme()

    # ─────────────────────────────────────────────────────────
    # Chargement du logo
    # ─────────────────────────────────────────────────────────
    def _charger_logo(self):
        self._photo_logo_grand = None
        self._photo_logo_petit = None

        if not PIL_DISPONIBLE:
            return
        try:
            img = Image.open("assets/logo.png").convert("RGBA")
            grand = img.resize((36, 36), Image.LANCZOS)
            petit = img.resize((28, 28), Image.LANCZOS)
            self._photo_logo_grand = ImageTk.PhotoImage(grand)
            self._photo_logo_petit = ImageTk.PhotoImage(petit)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── En-tête : logo + nom + bouton repli ──────────────
        self.zone_entete = tk.Frame(self)
        self.zone_entete.pack(fill="x", pady=(15, 5), padx=10)

        # Logo image ou emoji
        if self._photo_logo_grand:
            self.label_logo_img = tk.Label(self.zone_entete, image=self._photo_logo_grand)
        else:
            self.label_logo_img = tk.Label(self.zone_entete, text="🛡️")
        self.label_logo_img.pack(side="left")

        self.label_app_nom = tk.Label(self.zone_entete, text="NetSentinel")
        self.label_app_nom.pack(side="left", padx=(8, 0))

        # Bouton repli (flèche ←) à l'extrême droite de l'en-tête
        self.bouton_repli = tk.Button(
            self.zone_entete, text="◀",
            command=self._basculer_repli,
            relief="flat", cursor="hand2", bd=0
        )
        self.bouton_repli.pack(side="right")

        # ── Bloc utilisateur ──────────────────────────────────
        self.zone_utilisateur = tk.Frame(self)
        self.zone_utilisateur.pack(fill="x", pady=(0, 15), padx=12)

        self.label_username = tk.Label(
            self.zone_utilisateur,
            text=f"👋 {self.utilisateur.get('username', '')}"
        )
        self.label_username.pack(anchor="w")

        # ── Séparateur ────────────────────────────────────────
        self.separateur_haut = tk.Frame(self, height=1)
        self.separateur_haut.pack(fill="x", padx=12, pady=(0, 8))

        # ── Boutons de navigation ─────────────────────────────
        self.zone_menu = tk.Frame(self)
        self.zone_menu.pack(fill="x", padx=6)

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
        self.zone_basse.pack(side="bottom", fill="x", padx=12, pady=12)

        self.separateur_bas = tk.Frame(self.zone_basse, height=1)
        self.separateur_bas.pack(fill="x", pady=(0, 8))

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
    # Repliage / dépliage
    # ─────────────────────────────────────────────────────────
    def _basculer_repli(self):
        self._replie = not self._replie

        if self._replie:
            # ── Mode replié : icônes uniquement ──────────────
            self.config(width=self.LARGEUR_REPLIEE)
            self.label_app_nom.pack_forget()
            self.zone_utilisateur.pack_forget()
            self.label_version.pack_forget()
            self.bouton_theme.config(text="🌙")

            for nom_vue, icone, _ in self.ITEMS_MENU:
                self._boutons_menu[nom_vue].config(text=f" {icone}", anchor="center")

            self.bouton_repli.config(text="▶")

            # Logo petit
            if self._photo_logo_petit:
                self.label_logo_img.config(image=self._photo_logo_petit)

        else:
            # ── Mode déplié : icônes + libellés ──────────────
            self.config(width=self.LARGEUR_DEPLIEE)
            self.label_app_nom.pack(side="left", padx=(8, 0))
            self.zone_utilisateur.pack(fill="x", pady=(0, 15), padx=12,
                                       before=self.separateur_haut)
            self.label_version.pack(anchor="w", pady=(8, 0))

            couleurs = theme.get_colors()
            icone_theme = "🌙  Mode sombre" if theme.get_current_mode() == "clair" else "☀️  Mode clair"
            self.bouton_theme.config(text=icone_theme)

            for nom_vue, icone, libelle in self.ITEMS_MENU:
                self._boutons_menu[nom_vue].config(
                    text=f"  {icone}   {libelle}", anchor="w"
                )

            self.bouton_repli.config(text="◀")

            if self._photo_logo_grand:
                self.label_logo_img.config(image=self._photo_logo_grand)

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
                bouton.config(bg=couleurs["emeraude"], fg="#FFFFFF")
            else:
                bouton.config(bg=couleurs["fond_carte"], fg=couleurs["texte"])

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
        for zone in (self.zone_entete, self.zone_utilisateur,
                     self.zone_menu, self.zone_basse):
            zone.config(bg=couleurs["fond_carte"])

        self.label_logo_img.config(bg=couleurs["fond_carte"])
        self.label_app_nom.config(
            bg=couleurs["fond_carte"], fg=couleurs["emeraude"],
            font=theme.get_font("titre_petit")
        )
        self.bouton_repli.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte_secondaire"],
            activebackground=couleurs["fond_carte"],
            font=theme.get_font("texte")
        )
        self.label_username.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            font=theme.get_font("texte")
        )
        for sep in (self.separateur_haut, self.separateur_bas):
            sep.config(bg=couleurs["bordure"])

        for bouton in self._boutons_menu.values():
            bouton.config(
                bg=couleurs["fond_carte"], fg=couleurs["texte"],
                activebackground=couleurs["emeraude"],
                font=theme.get_font("texte"), bd=0
            )

        self.mettre_a_jour_selection(self._derniere_selection)

        icone_theme = "🌙  Mode sombre" if theme.get_current_mode() == "clair" else "☀️  Mode clair"
        if self._replie:
            icone_theme = "🌙" if theme.get_current_mode() == "clair" else "☀️"

        self.bouton_theme.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            activebackground=couleurs["fond_carte"],
            font=theme.get_font("texte"), text=icone_theme
        )
        self.label_version.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte_secondaire"],
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