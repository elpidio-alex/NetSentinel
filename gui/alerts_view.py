"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# gui/alerts_view.py — Alertes de sécurité détectées
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Cette vue affiche les alertes générées par ids_engine.py (scan de
# ports, brute-force, exfiltration), stockées dans la table
# `alerts`. Permet d'agir directement sur une alerte : bloquer
# l'IP source (passif ou actif, avec confirmation) via defense.py.
# =============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from gui import theme
from db import recuperer_plusieurs
from defense import ModuleDefense


class AlertsView(tk.Frame):
    """
    Vue d'affichage et de traitement des alertes de sécurité.

    Utilisation typique (dans main_view.py) :
        alerts_view = AlertsView(parent, utilisateur=utilisateur)
        alerts_view.pack(fill="both", expand=True)
    """

    def __init__(self, parent, utilisateur):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.defense = ModuleDefense()

        self._alertes_courantes = []
        self._ip_selectionnee = None

        self._construire_interface()
        self.appliquer_theme()

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── En-tête ───────────────────────────────────────────
        self.zone_entete = tk.Frame(self)
        self.zone_entete.pack(fill="x", padx=25, pady=(20, 10))

        self.label_titre = tk.Label(self.zone_entete, text="Alertes de sécurité")
        self.label_titre.pack(side="left")

        self.bouton_actualiser = tk.Button(
            self.zone_entete, text="⟳ Actualiser",
            command=self.rafraichir_donnees, relief="flat", cursor="hand2"
        )
        self.bouton_actualiser.pack(side="right")

        # ── Filtre par criticité ───────────────────────────────
        self.zone_filtre = tk.Frame(self)
        self.zone_filtre.pack(fill="x", padx=25, pady=(0, 10))

        self.label_filtre = tk.Label(self.zone_filtre, text="Filtrer :")
        self.label_filtre.pack(side="left", padx=(0, 8))

        # Valeurs alignées sur l'ENUM criticite de la table alerts
        self.variable_filtre = tk.StringVar(value="toutes")
        self.menu_filtre = tk.OptionMenu(
            self.zone_filtre, self.variable_filtre,
            "toutes", "critique", "warning", "info",
            command=lambda _: self.rafraichir_donnees()
        )
        self.menu_filtre.pack(side="left")

        # ── Tableau des alertes ───────────────────────────────
        self.zone_tableau = tk.Frame(self)
        self.zone_tableau.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        colonnes = ("heure", "criticite", "type_menace", "ip_source", "details")
        self.tableau_alertes = ttk.Treeview(
            self.zone_tableau, columns=colonnes, show="headings", height=14
        )
        entetes = {
            "heure": "Heure", "criticite": "Criticité", "type_menace": "Type",
            "ip_source": "IP source", "details": "Détails"
        }
        largeurs = {
            "heure": 130, "criticite": 90, "type_menace": 160,
            "ip_source": 120, "details": 320
        }
        for col in colonnes:
            self.tableau_alertes.heading(col, text=entetes[col])
            self.tableau_alertes.column(col, width=largeurs[col], anchor="w")

        barre_defilement = ttk.Scrollbar(
            self.zone_tableau, orient="vertical", command=self.tableau_alertes.yview
        )
        self.tableau_alertes.configure(yscrollcommand=barre_defilement.set)
        self.tableau_alertes.pack(side="left", fill="both", expand=True)
        barre_defilement.pack(side="right", fill="y")

        self.tableau_alertes.bind("<<TreeviewSelect>>", self._sur_selection)

        # ── Panneau d'action sur l'alerte sélectionnée ───────
        self.zone_action = tk.Frame(self)
        self.zone_action.pack(fill="x", padx=25, pady=(0, 20))

        self.label_selection = tk.Label(self.zone_action, text="Sélectionnez une alerte pour agir.")
        self.label_selection.pack(side="left")

        self.bouton_bloquer_passif = tk.Button(
            self.zone_action, text="🔒 Bloquer (passif)",
            command=lambda: self._bloquer_ip_selectionnee(mode="passif"),
            relief="flat", cursor="hand2", state="disabled"
        )
        self.bouton_bloquer_passif.pack(side="right", padx=(8, 0))

        self.bouton_bloquer_actif = tk.Button(
            self.zone_action, text="⛔ Bloquer (actif)",
            command=lambda: self._bloquer_ip_selectionnee(mode="actif"),
            relief="flat", cursor="hand2", state="disabled"
        )
        self.bouton_bloquer_actif.pack(side="right", padx=(8, 0))

    # ─────────────────────────────────────────────────────────
    # Chargement des données
    # ─────────────────────────────────────────────────────────
    def rafraichir_donnees(self):
        """Recharge les alertes depuis la BDD, avec filtre optionnel par criticité."""
        criticite = self.variable_filtre.get()

        if criticite == "toutes":
            self._alertes_courantes = recuperer_plusieurs(
                "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 200"
            )
        else:
            self._alertes_courantes = recuperer_plusieurs(
                "SELECT * FROM alerts WHERE criticite = %s ORDER BY created_at DESC LIMIT 200",
                (criticite,)
            )

        self._remplir_tableau()

    def _remplir_tableau(self):
        self.tableau_alertes.delete(*self.tableau_alertes.get_children())
        for alerte in self._alertes_courantes:
            horodatage = alerte.get("created_at", "")
            heure_affichee = horodatage.strftime("%d/%m/%Y %H:%M:%S") if horodatage else ""

            self.tableau_alertes.insert(
                "", "end", iid=str(alerte["id"]),
                values=(
                    heure_affichee,
                    alerte.get("criticite", ""),
                    alerte.get("type_menace", ""),
                    alerte.get("ip_source", ""),
                    alerte.get("details", ""),
                )
            )
        self._reinitialiser_panneau_action()

    # ─────────────────────────────────────────────────────────
    # Sélection d'une alerte
    # ─────────────────────────────────────────────────────────
    def _sur_selection(self, event=None):
        selection = self.tableau_alertes.selection()
        if not selection:
            self._reinitialiser_panneau_action()
            return

        id_alerte = int(selection[0])
        alerte = next((a for a in self._alertes_courantes if a["id"] == id_alerte), None)
        if not alerte:
            self._reinitialiser_panneau_action()
            return

        ip = alerte.get("ip_source", "")
        self._ip_selectionnee = ip

        if self.defense.est_dans_whitelist(ip):
            self.label_selection.config(text=f"IP {ip} — protégée par la whitelist, blocage impossible.")
            self.bouton_bloquer_passif.config(state="disabled")
            self.bouton_bloquer_actif.config(state="disabled")
        else:
            self.label_selection.config(text=f"IP sélectionnée : {ip}")
            self.bouton_bloquer_passif.config(state="normal")
            self.bouton_bloquer_actif.config(state="normal")

    def _reinitialiser_panneau_action(self):
        self._ip_selectionnee = None
        self.label_selection.config(text="Sélectionnez une alerte pour agir.")
        self.bouton_bloquer_passif.config(state="disabled")
        self.bouton_bloquer_actif.config(state="disabled")

    # ─────────────────────────────────────────────────────────
    # Blocage depuis une alerte
    # ─────────────────────────────────────────────────────────
    def _bloquer_ip_selectionnee(self, mode):
        ip = self._ip_selectionnee
        if not ip:
            return

        confirme = False
        if mode == "actif":
            confirme = messagebox.askyesno(
                "Confirmer le blocage actif",
                f"Bloquer réellement {ip} via le pare-feu Windows ?\n\n"
                "Cette action nécessite les droits administrateur et "
                "ajoute une vraie règle de blocage."
            )
            if not confirme:
                return

        resultat = self.defense.bloquer_ip(
            ip, raison="Blocage manuel depuis une alerte",
            mode=mode, confirme_par_utilisateur=confirme
        )

        if resultat["succes"]:
            messagebox.showinfo("Blocage", resultat["message"])
        else:
            messagebox.showerror("Échec du blocage", resultat["message"])

        self._reinitialiser_panneau_action()

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def appliquer_theme(self):
        couleurs = theme.get_colors()

        self.config(bg=couleurs["fond"])
        for zone in (self.zone_entete, self.zone_filtre, self.zone_tableau, self.zone_action):
            zone.config(bg=couleurs["fond"])

        self.label_titre.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("titre_petit"))
        self.bouton_actualiser.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            activebackground=couleurs["fond_carte"], font=theme.get_font("texte_petit")
        )

        self.label_filtre.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("texte"))
        self.menu_filtre.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            activebackground=couleurs["fond_carte"], font=theme.get_font("texte")
        )

        self.label_selection.config(bg=couleurs["fond"], fg=couleurs["texte_secondaire"], font=theme.get_font("texte_petit"))

        self.bouton_bloquer_passif.config(
            bg=couleurs["ambre"], fg="#FFFFFF",
            activebackground=couleurs["ambre"], font=theme.get_font("bouton")
        )
        self.bouton_bloquer_actif.config(
            bg=couleurs["rouge"], fg="#FFFFFF",
            activebackground=couleurs["rouge"], font=theme.get_font("bouton")
        )

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", background=couleurs["fond_carte"], foreground=couleurs["texte"],
            fieldbackground=couleurs["fond_carte"], rowheight=26, font=theme.get_font("texte_petit")
        )
        style.configure(
            "Treeview.Heading", background=couleurs["fond"], foreground=couleurs["texte"],
            font=theme.get_font("texte")
        )
        style.map("Treeview", background=[("selected", couleurs["emeraude"])])


if __name__ == "__main__":
    # Test manuel : python -m gui.alerts_view
    root = tk.Tk()
    root.title("NetSentinel — Test AlertsView")
    root.geometry("950x600")

    utilisateur_test = {"id": 1, "username": "test_admin"}
    vue = AlertsView(root, utilisateur=utilisateur_test)
    vue.pack(fill="both", expand=True)

    root.mainloop()