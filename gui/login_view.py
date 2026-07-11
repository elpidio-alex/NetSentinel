# =============================================================
# gui/login_view.py — Écran de connexion / inscription
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Cette vue gère la connexion et l'inscription des utilisateurs.
# Elle utilise auth.py pour la logique métier et theme.py pour
# le style (couleurs, police), sans jamais coder les couleurs
# en dur ici.
# =============================================================

import tkinter as tk
from tkinter import messagebox

from gui import theme
from auth import connecter_utilisateur, inscrire_utilisateur


class LoginView(tk.Frame):
    """
    Écran de connexion avec bascule vers un formulaire d'inscription.

    Utilisation typique (dans app.py) :
        login_view = LoginView(parent, on_connexion_reussie=self._afficher_main_view)
        login_view.pack(fill="both", expand=True)
    """

    def __init__(self, parent, on_connexion_reussie):
        """
        Paramètres :
            parent : conteneur Tkinter parent
            on_connexion_reussie (callable) : fonction appelée avec
                le dict utilisateur en paramètre après connexion réussie
        """
        super().__init__(parent)
        self.on_connexion_reussie = on_connexion_reussie
        self.mode_inscription = False

        self._construire_interface()
        self.appliquer_theme()

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        self.conteneur_central = tk.Frame(self)
        self.conteneur_central.place(relx=0.5, rely=0.5, anchor="center")

        # ── Titre / logo ─────────────────────────────────────
        self.label_titre = tk.Label(self.conteneur_central, text="NetSentinel")
        self.label_titre.pack(pady=(0, 5))

        self.label_sous_titre = tk.Label(
            self.conteneur_central,
            text="Surveillance réseau et défense automatisée"
        )
        self.label_sous_titre.pack(pady=(0, 25))

        # ── Champ username ───────────────────────────────────
        self.label_username = tk.Label(self.conteneur_central, text="Nom d'utilisateur")
        self.label_username.pack(anchor="w")
        self.entree_username = tk.Entry(self.conteneur_central, width=32)
        self.entree_username.pack(pady=(0, 12))

        # ── Champ email (visible uniquement en mode inscription) ──
        self.label_email = tk.Label(self.conteneur_central, text="Email")
        self.entree_email = tk.Entry(self.conteneur_central, width=32)

        # ── Champ mot de passe ───────────────────────────────
        self.label_mdp = tk.Label(self.conteneur_central, text="Mot de passe")
        self.label_mdp.pack(anchor="w")
        self.entree_mdp = tk.Entry(self.conteneur_central, width=32, show="•")
        self.entree_mdp.pack(pady=(0, 20))
        self.entree_mdp.bind("<Return>", lambda e: self._soumettre())

        # ── Bouton principal (Connexion / Créer un compte) ──
        self.bouton_principal = tk.Button(
            self.conteneur_central, text="Se connecter",
            command=self._soumettre, width=26, relief="flat", cursor="hand2"
        )
        self.bouton_principal.pack(pady=(0, 10))

        # ── Lien de bascule (vers inscription / connexion) ──
        self.lien_bascule = tk.Label(
            self.conteneur_central,
            text="Pas encore de compte ? Créer un compte",
            cursor="hand2"
        )
        self.lien_bascule.pack()
        self.lien_bascule.bind("<Button-1>", lambda e: self._basculer_mode())

        # ── Bouton bascule thème (haut à droite) ─────────────
        self.bouton_theme = tk.Button(
            self, text="🌙", command=self._basculer_theme,
            relief="flat", cursor="hand2", bd=0
        )
        self.bouton_theme.place(relx=1.0, rely=0.0, x=-15, y=15, anchor="ne")

    # ─────────────────────────────────────────────────────────
    # Bascule connexion / inscription
    # ─────────────────────────────────────────────────────────
    def _basculer_mode(self):
        self.mode_inscription = not self.mode_inscription

        if self.mode_inscription:
            self.label_email.pack(anchor="w", before=self.label_mdp)
            self.entree_email.pack(pady=(0, 12), before=self.label_mdp)
            self.bouton_principal.config(text="Créer un compte")
            self.lien_bascule.config(text="Déjà un compte ? Se connecter")
        else:
            self.label_email.pack_forget()
            self.entree_email.pack_forget()
            self.bouton_principal.config(text="Se connecter")
            self.lien_bascule.config(text="Pas encore de compte ? Créer un compte")

    # ─────────────────────────────────────────────────────────
    # Soumission du formulaire
    # ─────────────────────────────────────────────────────────
    def _soumettre(self):
        username = self.entree_username.get().strip()
        mot_de_passe = self.entree_mdp.get()

        if self.mode_inscription:
            email = self.entree_email.get().strip()
            resultat = inscrire_utilisateur(username, email, mot_de_passe)
            if resultat["succes"]:
                messagebox.showinfo("Compte créé", "Compte créé avec succès. Vous pouvez vous connecter.")
                self._basculer_mode()
                self.entree_mdp.delete(0, tk.END)
            else:
                messagebox.showerror("Erreur", resultat["message"])
        else:
            resultat = connecter_utilisateur(username, mot_de_passe)
            if resultat["succes"]:
                self.on_connexion_reussie(resultat["user"])
            else:
                messagebox.showerror("Erreur", resultat["message"])
                self.entree_mdp.delete(0, tk.END)

    # ─────────────────────────────────────────────────────────
    # Thème
    # ─────────────────────────────────────────────────────────
    def _basculer_theme(self):
        theme.toggle_theme()
        self.appliquer_theme()

    def appliquer_theme(self):
        """
        Applique les couleurs et polices actuelles à tous les
        widgets de cette vue. Appelée à la construction et à
        chaque bascule de thème.
        """
        couleurs = theme.get_colors()

        self.config(bg=couleurs["fond"])
        self.conteneur_central.config(bg=couleurs["fond"])

        self.label_titre.config(
            bg=couleurs["fond"], fg=couleurs["emeraude"],
            font=theme.get_font("titre")
        )
        self.label_sous_titre.config(
            bg=couleurs["fond"], fg=couleurs["texte_secondaire"],
            font=theme.get_font("texte_petit")
        )

        for label in (self.label_username, self.label_email, self.label_mdp):
            label.config(bg=couleurs["fond"], fg=couleurs["texte"], font=theme.get_font("texte"))

        for entree in (self.entree_username, self.entree_email, self.entree_mdp):
            entree.config(
                bg=couleurs["fond_carte"], fg=couleurs["texte"],
                insertbackground=couleurs["texte"], relief="flat",
                font=theme.get_font("texte"), highlightthickness=1,
                highlightbackground=couleurs["bordure"], highlightcolor=couleurs["emeraude"]
            )

        self.bouton_principal.config(
            bg=couleurs["emeraude"], fg="#FFFFFF",
            activebackground=couleurs["emeraude"], font=theme.get_font("bouton")
        )

        self.lien_bascule.config(
            bg=couleurs["fond"], fg=couleurs["emeraude"],
            font=theme.get_font("texte_petit")
        )

        self.bouton_theme.config(
            bg=couleurs["fond"], fg=couleurs["texte"],
            activebackground=couleurs["fond"], font=theme.get_font("texte")
        )

        icone_theme = "🌙" if theme.get_current_mode() == "clair" else "☀️"
        self.bouton_theme.config(text=icone_theme)


if __name__ == "__main__":
    # Test manuel : python -m gui.login_view
    def on_connexion(utilisateur):
        print("Connecté :", utilisateur)
        root.quit()

    root = tk.Tk()
    root.title("NetSentinel — Test LoginView")
    root.geometry("500x500")

    vue = LoginView(root, on_connexion_reussie=on_connexion)
    vue.pack(fill="both", expand=True)

    root.mainloop()