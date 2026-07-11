# =============================================================
# gui/blacklist_view.py — Gestion de la liste noire et whitelist
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Cette vue affiche les IP actuellement bloquées (table
# blocked_ips) avec possibilité de débloquer une IP ou tout
# débloquer, ainsi que la gestion de la whitelist (IP jamais
# bloquables) via defense.py.
# =============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from gui import theme
from db import recuperer_plusieurs
from defense import ModuleDefense


class BlacklistView(tk.Frame):
    """
    Vue de gestion des IP bloquées et de la whitelist.

    Utilisation typique (dans main_view.py) :
        blacklist_view = BlacklistView(parent, utilisateur=utilisateur)
        blacklist_view.pack(fill="both", expand=True)
    """

    def __init__(self, parent, utilisateur):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.defense = ModuleDefense()

        self._ips_bloquees = []

        self._construire_interface()
        self.appliquer_theme()

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── En-tête ───────────────────────────────────────────
        self.zone_entete = tk.Frame(self)
        self.zone_entete.pack(fill="x", padx=25, pady=(20, 10))

        self.label_titre = tk.Label(self.zone_entete, text="Liste noire")
        self.label_titre.pack(side="left")

        self.bouton_actualiser = tk.Button(
            self.zone_entete, text="⟳ Actualiser",
            command=self.rafraichir_donnees, relief="flat", cursor="hand2"
        )
        self.bouton_actualiser.pack(side="right")

        self.bouton_debloquer_tout = tk.Button(
            self.zone_entete, text="🔓 Débloquer tout",
            command=self._debloquer_tout, relief="flat", cursor="hand2"
        )
        self.bouton_debloquer_tout.pack(side="right", padx=(0, 8))

        # ── Tableau des IP bloquées ───────────────────────────
        self.zone_tableau = tk.Frame(self)
        self.zone_tableau.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        colonnes = ("ip", "raison", "mode", "bloquee_le", "expire_le")
        self.tableau_blocages = ttk.Treeview(
            self.zone_tableau, columns=colonnes, show="headings", height=12
        )
        entetes = {
            "ip": "IP", "raison": "Raison", "mode": "Mode",
            "bloquee_le": "Bloquée le", "expire_le": "Expire le"
        }
        largeurs = {
            "ip": 120, "raison": 260, "mode": 70,
            "bloquee_le": 130, "expire_le": 130
        }
        for col in colonnes:
            self.tableau_blocages.heading(col, text=entetes[col])
            self.tableau_blocages.column(col, width=largeurs[col], anchor="w")

        barre_defilement = ttk.Scrollbar(
            self.zone_tableau, orient="vertical", command=self.tableau_blocages.yview
        )
        self.tableau_blocages.configure(yscrollcommand=barre_defilement.set)
        self.tableau_blocages.pack(side="left", fill="both", expand=True)
        barre_defilement.pack(side="right", fill="y")

        self.tableau_blocages.bind("<<TreeviewSelect>>", self._sur_selection)

        # ── Panneau d'action (débloquer une IP) ──────────────
        self.zone_action = tk.Frame(self)
        self.zone_action.pack(fill="x", padx=25, pady=(0, 15))

        self.label_selection = tk.Label(self.zone_action, text="Sélectionnez une IP pour la débloquer.")
        self.label_selection.pack(side="left")

        self.bouton_debloquer = tk.Button(
            self.zone_action, text="🔓 Débloquer cette IP",
            command=self._debloquer_ip_selectionnee,
            relief="flat", cursor="hand2", state="disabled"
        )
        self.bouton_debloquer.pack(side="right")

        # ── Séparateur ────────────────────────────────────────
        self.separateur = tk.Frame(self, height=1)
        self.separateur.pack(fill="x", padx=25, pady=(5, 15))

        # ── Zone whitelist ────────────────────────────────────
        self.zone_whitelist = tk.Frame(self)
        self.zone_whitelist.pack(fill="x", padx=25, pady=(0, 20))

        self.label_titre_whitelist = tk.Label(self.zone_whitelist, text="Ajouter une IP à la whitelist")
        self.label_titre_whitelist.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.label_champ_ip = tk.Label(self.zone_whitelist, text="IP")
        self.label_champ_ip.grid(row=1, column=0, sticky="w")
        self.entree_ip_whitelist = tk.Entry(self.zone_whitelist, width=20)
        self.entree_ip_whitelist.grid(row=2, column=0, padx=(0, 10), sticky="w")

        self.label_champ_raison = tk.Label(self.zone_whitelist, text="Raison (optionnel)")
        self.label_champ_raison.grid(row=1, column=1, sticky="w")
        self.entree_raison_whitelist = tk.Entry(self.zone_whitelist, width=35)
        self.entree_raison_whitelist.grid(row=2, column=1, padx=(0, 10), sticky="w")

        self.bouton_ajouter_whitelist = tk.Button(
            self.zone_whitelist, text="➕ Ajouter",
            command=self._ajouter_a_whitelist, relief="flat", cursor="hand2"
        )
        self.bouton_ajouter_whitelist.grid(row=2, column=2, sticky="w")

        self.label_whitelist_actuelle = tk.Label(
            self.zone_whitelist,
            text="IP protégées : " + ", ".join(sorted(self.defense.whitelist))
        )
        self.label_whitelist_actuelle.grid(row=3, column=0, columnspan=3, sticky="w", pady=(10, 0))

    # ─────────────────────────────────────────────────────────
    # Chargement des données
    # ─────────────────────────────────────────────────────────
    def rafraichir_donnees(self):
        """Recharge la liste des IP bloquées depuis la BDD."""
        self._ips_bloquees = self.defense.lister_ip_bloquees()
        self._remplir_tableau()

    def _remplir_tableau(self):
        self.tableau_blocages.delete(*self.tableau_blocages.get_children())
        for blocage in self._ips_bloquees:
            expire_le = blocage.get("expires_at") or "Permanent"
            self.tableau_blocages.insert(
                "", "end", iid=str(blocage["id"]),
                values=(
                    blocage.get("ip", ""),
                    blocage.get("raison", ""),
                    blocage.get("mode", ""),
                    blocage.get("blocked_at", ""),
                    expire_le,
                )
            )
        self._reinitialiser_panneau_action()

    # ─────────────────────────────────────────────────────────
    # Sélection d'une IP bloquée
    # ─────────────────────────────────────────────────────────
    def _sur_selection(self, event=None):
        selection = self.tableau_blocages.selection()
        if not selection:
            self._reinitialiser_panneau_action()
            return

        id_blocage = int(selection[0])
        blocage = next((b for b in self._ips_bloquees if b["id"] == id_blocage), None)
        if not blocage:
            self._reinitialiser_panneau_action()
            return

        self._ip_selectionnee = blocage.get("ip")
        self.label_selection.config(text=f"IP sélectionnée : {self._ip_selectionnee}")
        self.bouton_debloquer.config(state="normal")

    def _reinitialiser_panneau_action(self):
        self._ip_selectionnee = None
        self.label_selection.config(text="Sélectionnez une IP pour la débloquer.")
        self.bouton_debloquer.config(state="disabled")

    # ─────────────────────────────────────────────────────────
    # Déblocage
    # ─────────────────────────────────────────────────────────
    def _debloquer_ip_selectionnee(self):
        ip = getattr(self, "_ip_selectionnee", None)
        if not ip:
            return

        resultat = self.defense.debloquer_ip(ip)
        messagebox.showinfo("Déblocage", resultat["message"])
        self.rafraichir_donnees()

    def _debloquer_tout(self):
        confirme = messagebox.askyesno(
            "Confirmer", "Débloquer toutes les IP actuellement bloquées ?"
        )
        if not confirme:
            return

        resultat = self.defense.debloquer_tout()
        messagebox.showinfo("Déblocage", resultat["message"])
        self.rafraichir_donnees()

    # ─────────────────────────────────────────────────────────
    # Whitelist
    # ─────────────────────────────────────────────────────────
    def _ajouter_a_whitelist(self):
        ip = self.entree_ip_whitelist.get().strip()
        raison = self.entree_raison_whitelist.get().strip()

        if not ip:
            messagebox.showwarning("Champ requis", "Veuillez saisir une adresse IP.")
            return

        resultat = self.defense.ajouter_a_whitelist(ip, raison)
        if resultat["succes"]:
            messagebox.showinfo("Whitelist", resultat["message"])
            self.entree_ip_whitelist.delete(0, tk.END)
            self.entree_raison_whitelist.delete(0, tk.END)
            self.label_whitelist_actuelle.config(
                text="IP protégées : " + ", ".join(sorted(self.defense.whitelist))
            )
        else:
            messagebox.showerror("Erreur", resultat["message"])

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def appliquer_theme(self):
        couleurs = theme.get_colors()

        self.config(bg=couleurs["fond"])
        for zone in (self.zone_entete, self.zone_tableau, self.zone_action, self.zone_whitelist):
            zone.config(bg=couleurs["fond"])

        self.label_titre.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("titre_petit"))

        for bouton in (self.bouton_actualiser, self.bouton_debloquer_tout):
            bouton.config(
                bg=couleurs["fond_carte"], fg=couleurs["texte"],
                activebackground=couleurs["fond_carte"], font=theme.get_font("texte_petit")
            )

        self.label_selection.config(bg=couleurs["fond"], fg=couleurs["texte_secondaire"], font=theme.get_font("texte_petit"))
        self.bouton_debloquer.config(
            bg=couleurs["emeraude"], fg="#FFFFFF",
            activebackground=couleurs["emeraude"], font=theme.get_font("bouton")
        )

        self.separateur.config(bg=couleurs["bordure"])

        self.label_titre_whitelist.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("texte"))
        for label in (self.label_champ_ip, self.label_champ_raison, self.label_whitelist_actuelle):
            label.config(bg=couleurs["fond"], fg=couleurs["texte_secondaire"], font=theme.get_font("texte_petit"))

        for entree in (self.entree_ip_whitelist, self.entree_raison_whitelist):
            entree.config(
                bg=couleurs["fond_carte"], fg=couleurs["texte"],
                insertbackground=couleurs["texte"], relief="flat",
                font=theme.get_font("texte"), highlightthickness=1,
                highlightbackground=couleurs["bordure"], highlightcolor=couleurs["emeraude"]
            )

        self.bouton_ajouter_whitelist.config(
            bg=couleurs["emeraude"], fg="#FFFFFF",
            activebackground=couleurs["emeraude"], font=theme.get_font("bouton")
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
    # Test manuel : python -m gui.blacklist_view
    root = tk.Tk()
    root.title("NetSentinel — Test BlacklistView")
    root.geometry("950x650")

    utilisateur_test = {"id": 1, "username": "test_admin"}
    vue = BlacklistView(root, utilisateur=utilisateur_test)
    vue.pack(fill="both", expand=True)

    root.mainloop()