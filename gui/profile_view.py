# =============================================================
# gui/profile_view.py — Vue profil utilisateur
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Affiche les informations du compte connecté, permet de modifier
# le username/email et le mot de passe, et affiche l'historique
# des actions du compte (sessions de surveillance + alertes
# générées durant ces sessions).
# =============================================================

import tkinter as tk
from tkinter import messagebox

from gui import theme
from db import recuperer_un, recuperer_plusieurs
from auth import modifier_profil, modifier_mot_de_passe


class ProfileView(tk.Frame):
    """
    Vue affichant les informations du compte, un formulaire de
    modification de profil, un formulaire de changement de mot
    de passe, et l'historique des actions du compte.

    Utilisation typique (dans main_view.py) :
        profile_view = ProfileView(parent, utilisateur=utilisateur_connecte,
                                    on_deconnexion=self.on_deconnexion)
        profile_view.pack(fill="both", expand=True)
    """

    def __init__(self, parent, utilisateur, on_deconnexion):
        """
        Paramètres :
            parent : conteneur Tkinter parent
            utilisateur (dict) : {"id", "username", "email"} — retourné par auth.py
            on_deconnexion (callable) : appelé après confirmation de déconnexion
                (remonte jusqu'à app.py pour réafficher l'écran de login)
        """
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.on_deconnexion = on_deconnexion

        self._construire_interface()
        self.appliquer_theme()
        self.rafraichir_donnees()

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ── Conteneur scrollable (la vue peut être longue) ───
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.conteneur = tk.Frame(self.canvas)

        self.conteneur.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.conteneur, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._defiler_molette)

        # ── Titre ─────────────────────────────────────────────
        self.label_titre = tk.Label(self.conteneur, text="👤 Mon profil", anchor="w")
        self.label_titre.pack(fill="x", padx=30, pady=(30, 20))

        # ── Bloc 1 : informations + modification du profil ───
        self.carte_profil = tk.Frame(self.conteneur)
        self.carte_profil.pack(fill="x", padx=30, pady=(0, 20))

        self.label_section_profil = tk.Label(self.carte_profil, text="Informations du compte", anchor="w")
        self.label_section_profil.pack(fill="x", padx=20, pady=(20, 15))

        self.label_username_titre = tk.Label(self.carte_profil, text="Nom d'utilisateur", anchor="w")
        self.label_username_titre.pack(fill="x", padx=20)
        self.entree_username = tk.Entry(self.carte_profil, width=40)
        self.entree_username.pack(fill="x", padx=20, pady=(2, 12))

        self.label_email_titre = tk.Label(self.carte_profil, text="Email", anchor="w")
        self.label_email_titre.pack(fill="x", padx=20)
        self.entree_email = tk.Entry(self.carte_profil, width=40)
        self.entree_email.pack(fill="x", padx=20, pady=(2, 12))

        self.label_date_titre = tk.Label(self.carte_profil, text="Membre depuis", anchor="w")
        self.label_date_titre.pack(fill="x", padx=20)
        self.label_date_valeur = tk.Label(self.carte_profil, text="—", anchor="w")
        self.label_date_valeur.pack(fill="x", padx=20, pady=(2, 15))

        self.bouton_enregistrer_profil = tk.Button(
            self.carte_profil, text="Enregistrer les modifications",
            command=self._enregistrer_profil, relief="flat", cursor="hand2"
        )
        self.bouton_enregistrer_profil.pack(anchor="w", padx=20, pady=(0, 20))

        # ── Bloc 2 : changement de mot de passe ──────────────
        self.carte_mdp = tk.Frame(self.conteneur)
        self.carte_mdp.pack(fill="x", padx=30, pady=(0, 20))

        self.label_section_mdp = tk.Label(self.carte_mdp, text="Changer le mot de passe", anchor="w")
        self.label_section_mdp.pack(fill="x", padx=20, pady=(20, 15))

        self.label_ancien_mdp = tk.Label(self.carte_mdp, text="Mot de passe actuel", anchor="w")
        self.label_ancien_mdp.pack(fill="x", padx=20)
        self.entree_ancien_mdp = tk.Entry(self.carte_mdp, width=40, show="•")
        self.entree_ancien_mdp.pack(fill="x", padx=20, pady=(2, 12))

        self.label_nouveau_mdp = tk.Label(self.carte_mdp, text="Nouveau mot de passe", anchor="w")
        self.label_nouveau_mdp.pack(fill="x", padx=20)
        self.entree_nouveau_mdp = tk.Entry(self.carte_mdp, width=40, show="•")
        self.entree_nouveau_mdp.pack(fill="x", padx=20, pady=(2, 12))

        self.label_confirmation_mdp = tk.Label(self.carte_mdp, text="Confirmer le nouveau mot de passe", anchor="w")
        self.label_confirmation_mdp.pack(fill="x", padx=20)
        self.entree_confirmation_mdp = tk.Entry(self.carte_mdp, width=40, show="•")
        self.entree_confirmation_mdp.pack(fill="x", padx=20, pady=(2, 12))

        self.bouton_changer_mdp = tk.Button(
            self.carte_mdp, text="Changer le mot de passe",
            command=self._changer_mot_de_passe, relief="flat", cursor="hand2"
        )
        self.bouton_changer_mdp.pack(anchor="w", padx=20, pady=(0, 20))

        # ── Bloc 3 : historique du compte ────────────────────
        self.carte_historique = tk.Frame(self.conteneur)
        self.carte_historique.pack(fill="x", padx=30, pady=(0, 20))

        self.label_section_historique = tk.Label(self.carte_historique, text="Historique du compte", anchor="w")
        self.label_section_historique.pack(fill="x", padx=20, pady=(20, 15))

        self.zone_historique = tk.Frame(self.carte_historique)
        self.zone_historique.pack(fill="x", padx=20, pady=(0, 20))
        self._lignes_historique = []

        # ── Bouton déconnexion ───────────────────────────────
        self.bouton_deconnexion = tk.Button(
            self.conteneur, text="Se déconnecter",
            command=self._deconnexion, relief="flat", cursor="hand2"
        )
        self.bouton_deconnexion.pack(anchor="w", padx=30, pady=(0, 30))

    def _defiler_molette(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ─────────────────────────────────────────────────────────
    # Rafraîchissement des données
    # ─────────────────────────────────────────────────────────
    def rafraichir_donnees(self):
        """
        Recharge les informations du compte et l'historique depuis
        la base (appelée automatiquement par main_view.py à chaque
        affichage de cette vue).
        """
        self.entree_username.delete(0, tk.END)
        self.entree_username.insert(0, self.utilisateur.get("username", ""))

        self.entree_email.delete(0, tk.END)
        self.entree_email.insert(0, self.utilisateur.get("email", ""))

        ligne = recuperer_un(
            "SELECT created_at FROM users WHERE id = %s",
            (self.utilisateur.get("id"),)
        )
        if ligne and ligne.get("created_at"):
            self.label_date_valeur.config(text=ligne["created_at"].strftime("%d/%m/%Y"))
        else:
            self.label_date_valeur.config(text="—")

        self._charger_historique()

    def _charger_historique(self):
        """
        Charge les 20 dernières sessions de surveillance du compte,
        avec le nombre d'alertes générées durant chacune.
        """
        for widget in self._lignes_historique:
            widget.destroy()
        self._lignes_historique = []

        sessions = recuperer_plusieurs(
            """SELECT s.id, s.mode, s.started_at, s.ended_at,
                      COUNT(a.id) AS nb_alertes
               FROM sessions s
               LEFT JOIN alerts a ON a.session_id = s.id
               WHERE s.user_id = %s
               GROUP BY s.id
               ORDER BY s.started_at DESC
               LIMIT 20""",
            (self.utilisateur.get("id"),)
        )

        couleurs = theme.get_colors()

        if not sessions:
            label_vide = tk.Label(
                self.zone_historique, text="Aucune session enregistrée pour ce compte.",
                anchor="w", bg=couleurs["fond_carte"], fg=couleurs["texte_secondaire"],
                font=theme.get_font("texte_petit")
            )
            label_vide.pack(fill="x", pady=(0, 5))
            self._lignes_historique.append(label_vide)
            return

        for session in sessions:
            debut = session["started_at"].strftime("%d/%m/%Y %H:%M") if session["started_at"] else "—"
            fin = session["ended_at"].strftime("%d/%m/%Y %H:%M") if session["ended_at"] else "en cours"
            texte = (
                f"Session #{session['id']} — mode {session['mode']} — "
                f"{debut} → {fin} — {session['nb_alertes']} alerte(s)"
            )
            ligne = tk.Label(
                self.zone_historique, text=texte, anchor="w",
                bg=couleurs["fond_carte"], fg=couleurs["texte"],
                font=theme.get_font("texte_petit")
            )
            ligne.pack(fill="x", pady=3)
            self._lignes_historique.append(ligne)

    # ─────────────────────────────────────────────────────────
    # Modification du profil
    # ─────────────────────────────────────────────────────────
    def _enregistrer_profil(self):
        nouveau_username = self.entree_username.get().strip()
        nouvel_email = self.entree_email.get().strip()

        resultat = modifier_profil(self.utilisateur["id"], nouveau_username, nouvel_email)

        if resultat["succes"]:
            self.utilisateur["username"] = resultat["user"]["username"]
            self.utilisateur["email"] = resultat["user"]["email"]
            messagebox.showinfo("Profil mis à jour", resultat["message"])
        else:
            messagebox.showerror("Erreur", resultat["message"])

    # ─────────────────────────────────────────────────────────
    # Changement de mot de passe
    # ─────────────────────────────────────────────────────────
    def _changer_mot_de_passe(self):
        ancien = self.entree_ancien_mdp.get()
        nouveau = self.entree_nouveau_mdp.get()
        confirmation = self.entree_confirmation_mdp.get()

        if nouveau != confirmation:
            messagebox.showerror("Erreur", "Le nouveau mot de passe et sa confirmation ne correspondent pas.")
            return

        resultat = modifier_mot_de_passe(self.utilisateur["id"], ancien, nouveau)

        if resultat["succes"]:
            messagebox.showinfo("Mot de passe modifié", resultat["message"])
            self.entree_ancien_mdp.delete(0, tk.END)
            self.entree_nouveau_mdp.delete(0, tk.END)
            self.entree_confirmation_mdp.delete(0, tk.END)
        else:
            messagebox.showerror("Erreur", resultat["message"])

    # ─────────────────────────────────────────────────────────
    # Déconnexion
    # ─────────────────────────────────────────────────────────
    def _deconnexion(self):
        """
        Demande confirmation puis délègue la déconnexion à app.py
        via le callback on_deconnexion (retour à l'écran de login,
        sans fermer l'application).
        """
        if messagebox.askyesno("Déconnexion", "Voulez-vous vraiment vous déconnecter ?"):
            self.on_deconnexion()

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def appliquer_theme(self):
        couleurs = theme.get_colors()

        self.config(bg=couleurs["fond"])
        self.canvas.config(bg=couleurs["fond"])
        self.conteneur.config(bg=couleurs["fond"])

        self.label_titre.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("titre"))

        for carte in (self.carte_profil, self.carte_mdp, self.carte_historique):
            carte.config(bg=couleurs["fond_carte"], highlightbackground=couleurs["bordure"], highlightthickness=1)

        for label in (self.label_section_profil, self.label_section_mdp, self.label_section_historique):
            label.config(bg=couleurs["fond_carte"], fg=couleurs["texte"], font=theme.get_font("sous_titre"))

        for label in (self.label_username_titre, self.label_email_titre, self.label_date_titre,
                      self.label_ancien_mdp, self.label_nouveau_mdp, self.label_confirmation_mdp):
            label.config(bg=couleurs["fond_carte"], fg=couleurs["texte_secondaire"], font=theme.get_font("texte_petit"))

        self.label_date_valeur.config(bg=couleurs["fond_carte"], fg=couleurs["texte"], font=theme.get_font("texte"))

        for entree in (self.entree_username, self.entree_email, self.entree_ancien_mdp,
                       self.entree_nouveau_mdp, self.entree_confirmation_mdp):
            entree.config(
                bg=couleurs["fond"], fg=couleurs["texte"],
                insertbackground=couleurs["texte"], relief="flat",
                font=theme.get_font("texte"), highlightthickness=1,
                highlightbackground=couleurs["bordure"], highlightcolor=couleurs["emeraude"]
            )

        for bouton in (self.bouton_enregistrer_profil, self.bouton_changer_mdp):
            bouton.config(
                bg=couleurs["emeraude"], fg="#FFFFFF",
                activebackground=couleurs["emeraude"], font=theme.get_font("bouton")
            )

        self.zone_historique.config(bg=couleurs["fond_carte"])

        self.bouton_deconnexion.config(
            bg=couleurs["rouge"], fg="#FFFFFF",
            activebackground=couleurs["rouge"], font=theme.get_font("bouton")
        )

        # Réapplique les couleurs des lignes d'historique déjà affichées
        for ligne in self._lignes_historique:
            ligne.config(bg=couleurs["fond_carte"])


if __name__ == "__main__":
    # Test manuel : python -m gui.profile_view
    root = tk.Tk()
    root.title("NetSentinel — Test ProfileView")
    root.geometry("600x700")

    utilisateur_test = {"id": 1, "username": "test_admin", "email": "test@netsentinel.local"}
    vue = ProfileView(
        root, utilisateur=utilisateur_test,
        on_deconnexion=lambda: print("Déconnexion demandée")
    )
    vue.pack(fill="both", expand=True)

    root.mainloop()