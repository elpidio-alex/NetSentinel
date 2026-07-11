"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# gui/history_view.py — Historique des événements
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Cette vue affiche un historique consultable et filtrable de
# tous les événements journalisés dans la table history_log
# (alertes, blocages, déblocages, connexions, inscriptions).
# Depuis une ligne de type "connexion", l'utilisateur peut
# consulter les paquets capturés durant la session associée.
# =============================================================

import tkinter as tk
from tkinter import ttk, messagebox

from gui import theme
from db import recuperer_plusieurs


class HistoryView(tk.Frame):
    """
    Vue d'historique consultable des événements journalisés.

    Utilisation typique (dans main_view.py) :
        history_view = HistoryView(parent, utilisateur=utilisateur)
        history_view.pack(fill="both", expand=True)
    """

    TYPES_EVENEMENT = ("tous", "alerte", "blocage", "deblocage", "connexion", "inscription")

    def __init__(self, parent, utilisateur):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self._evenements_courants = []

        self._construire_interface()
        self.appliquer_theme()

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── En-tête ───────────────────────────────────────────
        self.zone_entete = tk.Frame(self)
        self.zone_entete.pack(fill="x", padx=25, pady=(20, 10))

        self.label_titre = tk.Label(self.zone_entete, text="Historique")
        self.label_titre.pack(side="left")

        self.bouton_actualiser = tk.Button(
            self.zone_entete, text="⟳ Actualiser",
            command=self.rafraichir_donnees, relief="flat", cursor="hand2"
        )
        self.bouton_actualiser.pack(side="right")

        # ── Filtres ───────────────────────────────────────────
        self.zone_filtres = tk.Frame(self)
        self.zone_filtres.pack(fill="x", padx=25, pady=(0, 10))

        self.label_type = tk.Label(self.zone_filtres, text="Type :")
        self.label_type.pack(side="left", padx=(0, 8))

        self.variable_type = tk.StringVar(value="tous")
        self.menu_type = tk.OptionMenu(
            self.zone_filtres, self.variable_type, *self.TYPES_EVENEMENT,
            command=lambda _: self.rafraichir_donnees()
        )
        self.menu_type.pack(side="left", padx=(0, 20))

        self.label_recherche = tk.Label(self.zone_filtres, text="Rechercher (IP) :")
        self.label_recherche.pack(side="left", padx=(0, 8))

        self.entree_recherche = tk.Entry(self.zone_filtres, width=20)
        self.entree_recherche.pack(side="left")
        self.entree_recherche.bind("<Return>", lambda e: self.rafraichir_donnees())

        self.bouton_rechercher = tk.Button(
            self.zone_filtres, text="🔍", command=self.rafraichir_donnees,
            relief="flat", cursor="hand2"
        )
        self.bouton_rechercher.pack(side="left", padx=(6, 0))

        # ── Tableau de l'historique ───────────────────────────
        self.zone_tableau = tk.Frame(self)
        self.zone_tableau.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        colonnes = ("date", "type", "ip", "description", "utilisateur")
        self.tableau_historique = ttk.Treeview(
            self.zone_tableau, columns=colonnes, show="headings", height=16
        )
        entetes = {
            "date": "Date", "type": "Type", "ip": "IP",
            "description": "Description", "utilisateur": "Utilisateur"
        }
        largeurs = {
            "date": 140, "type": 100, "ip": 120,
            "description": 320, "utilisateur": 110
        }
        for col in colonnes:
            self.tableau_historique.heading(col, text=entetes[col])
            self.tableau_historique.column(col, width=largeurs[col], anchor="w")

        barre_defilement = ttk.Scrollbar(
            self.zone_tableau, orient="vertical", command=self.tableau_historique.yview
        )
        self.tableau_historique.configure(yscrollcommand=barre_defilement.set)
        self.tableau_historique.pack(side="left", fill="both", expand=True)
        barre_defilement.pack(side="right", fill="y")

        self.tableau_historique.bind("<<TreeviewSelect>>", self._sur_selection)

        # ── Panneau d'action ──────────────────────────────────
        self.zone_action = tk.Frame(self)
        self.zone_action.pack(fill="x", padx=25, pady=(0, 20))

        self.label_action = tk.Label(self.zone_action, text="")
        self.label_action.pack(side="left")

        self.bouton_voir_paquets = tk.Button(
            self.zone_action, text="📦 Voir les paquets capturés",
            command=self._ouvrir_fenetre_paquets,
            relief="flat", cursor="hand2", state="disabled"
        )
        self.bouton_voir_paquets.pack(side="right")

    # ─────────────────────────────────────────────────────────
    # Chargement des données
    # ─────────────────────────────────────────────────────────
    def rafraichir_donnees(self):
        type_filtre = self.variable_type.get()
        ip_recherchee = self.entree_recherche.get().strip()

        conditions = []
        parametres = []

        if type_filtre != "tous":
            conditions.append("type = %s")
            parametres.append(type_filtre)

        if ip_recherchee:
            conditions.append("ip LIKE %s")
            parametres.append(f"%{ip_recherchee}%")

        clause_where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        requete = f"""
            SELECT * FROM history_log
            {clause_where}
            ORDER BY created_at DESC
            LIMIT 300
        """
        self._evenements_courants = recuperer_plusieurs(requete, tuple(parametres))
        self._remplir_tableau()
        self._reinitialiser_action()

    def _remplir_tableau(self):
        self.tableau_historique.delete(*self.tableau_historique.get_children())
        for evenement in self._evenements_courants:
            horodatage = evenement.get("created_at", "")
            date_affichee = horodatage.strftime("%d/%m/%Y %H:%M:%S") if horodatage else ""

            self.tableau_historique.insert(
                "", "end", iid=str(evenement["id"]),
                values=(
                    date_affichee,
                    evenement.get("type", ""),
                    evenement.get("ip", "") or "",
                    evenement.get("description", ""),
                    evenement.get("username", "") or "",
                )
            )

    # ─────────────────────────────────────────────────────────
    # Sélection d'une ligne
    # ─────────────────────────────────────────────────────────
    def _sur_selection(self, event=None):
        selection = self.tableau_historique.selection()
        if not selection:
            self._reinitialiser_action()
            return

        id_evenement = int(selection[0])
        evenement = next((e for e in self._evenements_courants if e["id"] == id_evenement), None)
        if not evenement:
            self._reinitialiser_action()
            return

        # Le bouton "Voir les paquets" n'est pertinent que pour les
        # événements de type "connexion" (qui correspondent à une session
        # de capture). Pour les autres types, on le désactive.
        if evenement.get("type") == "connexion":
            self.label_action.config(text=f"Connexion du {evenement.get('created_at', '').strftime('%d/%m/%Y %H:%M') if evenement.get('created_at') else ''}")
            self.bouton_voir_paquets.config(state="normal")
            self._evenement_selectionne = evenement
        else:
            self.label_action.config(text="Sélectionnez une ligne de type 'connexion' pour voir les paquets.")
            self.bouton_voir_paquets.config(state="disabled")
            self._evenement_selectionne = None

    def _reinitialiser_action(self):
        self._evenement_selectionne = None
        self.label_action.config(text="")
        self.bouton_voir_paquets.config(state="disabled")

    # ─────────────────────────────────────────────────────────
    # Fenêtre détail des paquets capturés
    # ─────────────────────────────────────────────────────────
    def _ouvrir_fenetre_paquets(self):
        """
        Ouvre une fenêtre Toplevel affichant tous les paquets
        capturés durant la session associée à la connexion sélectionnée.
        La session est retrouvée via user_id + created_at (la connexion
        précède la session de quelques secondes au plus).
        """
        evenement = getattr(self, "_evenement_selectionne", None)
        if not evenement:
            return

        # Retrouver la session la plus proche de cet événement de connexion
        # pour le même utilisateur (démarrée juste après la connexion)
        sessions = recuperer_plusieurs(
            """SELECT id, started_at, ended_at
               FROM sessions
               WHERE user_id = %s AND started_at >= %s
               ORDER BY started_at ASC
               LIMIT 1""",
            (evenement.get("user_id"), evenement.get("created_at"))
        )

        if not sessions:
            messagebox.showinfo(
                "Aucune capture",
                "Aucune session de capture trouvée pour cette connexion.\n"
                "La capture n'a peut-être pas été démarrée lors de cette session."
            )
            return

        session = sessions[0]
        session_id = session["id"]

        paquets = recuperer_plusieurs(
            """SELECT horodatage, ip_source, ip_destination,
                      protocole, port_source, port_destination, taille, flags_tcp
               FROM captured_packets
               WHERE session_id = %s
               ORDER BY horodatage ASC""",
            (session_id,)
        )

        if not paquets:
            messagebox.showinfo(
                "Aucun paquet",
                f"La session #{session_id} n'a aucun paquet enregistré."
            )
            return

        self._afficher_fenetre_paquets(session, paquets)

    def _afficher_fenetre_paquets(self, session, paquets):
        """Construit et affiche la fenêtre Toplevel avec le tableau de paquets."""
        couleurs = theme.get_colors()

        fenetre = tk.Toplevel(self)
        fenetre.title(f"Paquets — Session #{session['id']}")
        fenetre.geometry("1000x550")
        fenetre.configure(bg=couleurs["fond"])

        # ── En-tête ───────────────────────────────────────────
        debut = session["started_at"].strftime("%d/%m/%Y %H:%M:%S") if session["started_at"] else "—"
        fin = session["ended_at"].strftime("%d/%m/%Y %H:%M:%S") if session["ended_at"] else "en cours"

        label_info = tk.Label(
            fenetre,
            text=f"Session #{session['id']}   |   Début : {debut}   |   Fin : {fin}   |   {len(paquets)} paquet(s)",
            bg=couleurs["fond"], fg=couleurs["texte"],
            font=theme.get_font("texte"), anchor="w"
        )
        label_info.pack(fill="x", padx=20, pady=(15, 10))

        # ── Tableau ───────────────────────────────────────────
        zone = tk.Frame(fenetre, bg=couleurs["fond"])
        zone.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        colonnes = ("heure", "source", "destination", "protocole", "port_src", "port_dst", "taille", "flags")
        tableau = ttk.Treeview(zone, columns=colonnes, show="headings", height=20)

        entetes = {
            "heure": "Heure", "source": "Source", "destination": "Destination",
            "protocole": "Protocole", "port_src": "Port src", "port_dst": "Port dst",
            "taille": "Taille", "flags": "Flags TCP"
        }
        largeurs = {
            "heure": 90, "source": 130, "destination": 130,
            "protocole": 80, "port_src": 70, "port_dst": 70,
            "taille": 70, "flags": 80
        }
        for col in colonnes:
            tableau.heading(col, text=entetes[col])
            tableau.column(col, width=largeurs[col], anchor="w")

        barre = ttk.Scrollbar(zone, orient="vertical", command=tableau.yview)
        tableau.configure(yscrollcommand=barre.set)
        tableau.pack(side="left", fill="both", expand=True)
        barre.pack(side="right", fill="y")

        for paquet in paquets:
            h = paquet["horodatage"].strftime("%H:%M:%S") if paquet.get("horodatage") else ""
            tableau.insert("", "end", values=(
                h,
                paquet.get("ip_source", "") or "",
                paquet.get("ip_destination", "") or "",
                (paquet.get("protocole", "") or "").upper(),
                paquet.get("port_source", "") or "",
                paquet.get("port_destination", "") or "",
                paquet.get("taille", "") or "",
                paquet.get("flags_tcp", "") or "",
            ))

        # Style ttk
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

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def appliquer_theme(self):
        couleurs = theme.get_colors()

        self.config(bg=couleurs["fond"])
        for zone in (self.zone_entete, self.zone_filtres, self.zone_tableau, self.zone_action):
            zone.config(bg=couleurs["fond"])

        self.label_titre.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("titre_petit"))
        self.bouton_actualiser.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            activebackground=couleurs["fond_carte"], font=theme.get_font("texte_petit")
        )

        for label in (self.label_type, self.label_recherche):
            label.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("texte"))

        self.menu_type.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            activebackground=couleurs["fond_carte"], font=theme.get_font("texte")
        )

        self.entree_recherche.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            insertbackground=couleurs["texte"], relief="flat",
            font=theme.get_font("texte"), highlightthickness=1,
            highlightbackground=couleurs["bordure"], highlightcolor=couleurs["emeraude"]
        )

        self.bouton_rechercher.config(
            bg=couleurs["fond_carte"], fg=couleurs["texte"],
            activebackground=couleurs["fond_carte"], font=theme.get_font("texte")
        )

        self.label_action.config(bg=couleurs["fond"], fg=couleurs["texte_secondaire"], font=theme.get_font("texte_petit"))
        self.bouton_voir_paquets.config(
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
    root = tk.Tk()
    root.title("NetSentinel — Test HistoryView")
    root.geometry("950x650")

    utilisateur_test = {"id": 1, "username": "test_admin"}
    vue = HistoryView(root, utilisateur=utilisateur_test)
    vue.pack(fill="both", expand=True)

    root.mainloop()