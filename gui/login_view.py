"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# gui/login_view.py — Écran de connexion / inscription
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================

import tkinter as tk
from tkinter import messagebox

from gui import theme
from auth import connecter_utilisateur, inscrire_utilisateur

try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False


class LoginView(tk.Frame):

    def __init__(self, parent, on_connexion_reussie):
        super().__init__(parent)
        self.on_connexion_reussie = on_connexion_reussie
        self.mode_inscription = False
        self._photo_logo = None

        self._construire_interface()
        self.appliquer_theme()

    # ─────────────────────────────────────────────────────────
    # Construction de l'interface
    # ─────────────────────────────────────────────────────────
    def _construire_interface(self):
        # ══ Panneau gauche (sombre, logo + nom) ══════════════
        self.panneau_gauche = tk.Frame(self, width=380)
        self.panneau_gauche.pack(side="left", fill="y")
        self.panneau_gauche.pack_propagate(False)

        # Centrage vertical dans le panneau gauche
        self.zone_logo_centrale = tk.Frame(self.panneau_gauche)
        self.zone_logo_centrale.place(relx=0.5, rely=0.5, anchor="center")

        # Logo
        if PIL_DISPONIBLE:
            try:
                img = Image.open("assets/logo.png").convert("RGBA")
                img = img.resize((250, 320), Image.LANCZOS)
                self._photo_logo = ImageTk.PhotoImage(img)
                self.label_logo_img = tk.Label(
                    self.zone_logo_centrale, image=self._photo_logo
                )
            except Exception:
                self.label_logo_img = tk.Label(
                    self.zone_logo_centrale, text="🛡️",
                    font=("Times New Roman", 80)
                )
        else:
            self.label_logo_img = tk.Label(
                self.zone_logo_centrale, text="🛡️",
                font=("Times New Roman", 80)
            )
        self.label_logo_img.pack(pady=(0, 25))

        # Nom de l'application
        self.label_app_nom = tk.Label(
            self.zone_logo_centrale, text="NetSentinel"
        )
        self.label_app_nom.pack()

        # Tagline
        self.label_tagline = tk.Label(
            self.zone_logo_centrale,
            text="Surveillance réseau et défense automatisée"
        )
        self.label_tagline.pack(pady=(6, 0))

        # ══ Panneau droit (clair, formulaire) ════════════════
        self.panneau_droit = tk.Frame(self)
        self.panneau_droit.pack(side="right", fill="both", expand=True)

        # Bouton thème en haut à droite
        self.bouton_theme = tk.Button(
            self.panneau_droit, text="🌙",
            command=self._basculer_theme,
            relief="flat", cursor="hand2", bd=0
        )
        self.bouton_theme.place(relx=1.0, rely=0.0, x=-15, y=15, anchor="ne")

        # Carte formulaire centrée dans le panneau droit
        self.carte_formulaire = tk.Frame(self.panneau_droit)
        self.carte_formulaire.place(relx=0.5, rely=0.5, anchor="center")

        # Titre du formulaire
        self.label_titre_form = tk.Label(
            self.carte_formulaire, text="Connexion"
        )
        self.label_titre_form.pack(anchor="w", pady=(0, 20))

        # ── Champ username ────────────────────────────────────
        self.label_username = tk.Label(
            self.carte_formulaire, text="Nom d'utilisateur"
        )
        self.label_username.pack(anchor="w")
        self.entree_username = tk.Entry(self.carte_formulaire, width=36)
        self.entree_username.pack(pady=(4, 14), ipady=6)

        # ── Champ email (inscription uniquement) ──────────────
        self.label_email = tk.Label(self.carte_formulaire, text="Email")
        self.entree_email = tk.Entry(self.carte_formulaire, width=36)

        # ── Champ mot de passe ────────────────────────────────
        self.label_mdp = tk.Label(
            self.carte_formulaire, text="Mot de passe"
        )
        self.label_mdp.pack(anchor="w")
        self.entree_mdp = tk.Entry(
            self.carte_formulaire, width=36, show="•"
        )
        self.entree_mdp.pack(pady=(4, 24), ipady=6)
        self.entree_mdp.bind("<Return>", lambda e: self._soumettre())

        # ── Bouton principal ──────────────────────────────────
        self.bouton_principal = tk.Button(
            self.carte_formulaire, text="Se connecter",
            command=self._soumettre,
            width=34, relief="flat", cursor="hand2"
        )
        self.bouton_principal.pack(pady=(0, 12), ipady=8)

        # ── Lien bascule mode ─────────────────────────────────
        self.lien_bascule = tk.Label(
            self.carte_formulaire,
            text="Pas encore de compte ?  Créer un compte",
            cursor="hand2"
        )
        self.lien_bascule.pack()
        self.lien_bascule.bind("<Button-1>", lambda e: self._basculer_mode())

    # ─────────────────────────────────────────────────────────
    # Bascule connexion / inscription
    # ─────────────────────────────────────────────────────────
    def _basculer_mode(self):
        self.mode_inscription = not self.mode_inscription

        if self.mode_inscription:
            self.label_titre_form.config(text="Créer un compte")
            self.label_email.pack(anchor="w", before=self.label_mdp)
            self.entree_email.pack(pady=(4, 14), ipady=6, before=self.label_mdp)
            self.bouton_principal.config(text="Créer un compte")
            self.lien_bascule.config(text="Déjà un compte ?  Se connecter")
        else:
            self.label_titre_form.config(text="Connexion")
            self.label_email.pack_forget()
            self.entree_email.pack_forget()
            self.bouton_principal.config(text="Se connecter")
            self.lien_bascule.config(
                text="Pas encore de compte ?  Créer un compte"
            )

    # ─────────────────────────────────────────────────────────
    # Soumission
    # ─────────────────────────────────────────────────────────
    def _soumettre(self):
        username = self.entree_username.get().strip()
        mot_de_passe = self.entree_mdp.get()

        if self.mode_inscription:
            email = self.entree_email.get().strip()
            resultat = inscrire_utilisateur(username, email, mot_de_passe)
            if resultat["succes"]:
                messagebox.showinfo(
                    "Compte créé",
                    "Compte créé avec succès. Vous pouvez vous connecter."
                )
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
        couleurs = theme.get_colors()

        # ── Panneau gauche (toujours sombre, indépendant du thème) ──
        FOND_GAUCHE  = "#0f1b2d"
        TEXTE_GAUCHE = "#FFFFFF"

        self.config(bg=couleurs["fond"])
        self.panneau_gauche.config(bg=FOND_GAUCHE)
        self.zone_logo_centrale.config(bg=FOND_GAUCHE)
        self.label_logo_img.config(bg=FOND_GAUCHE)

        self.label_app_nom.config(
            bg=FOND_GAUCHE, fg=TEXTE_GAUCHE,
            font=theme.get_font("titre")
        )
        self.label_tagline.config(
            bg=FOND_GAUCHE, fg="#8899aa",
            font=theme.get_font("texte_petit")
        )

        # ── Panneau droit ─────────────────────────────────────
        self.panneau_droit.config(bg=couleurs["fond"])
        self.carte_formulaire.config(bg=couleurs["fond"])

        self.label_titre_form.config(
            bg=couleurs["fond"], fg=couleurs["texte"],
            font=theme.get_font("titre")
        )

        for label in (self.label_username, self.label_email, self.label_mdp):
            label.config(
                bg=couleurs["fond"], fg=couleurs["texte"],
                font=theme.get_font("texte")
            )

        for entree in (self.entree_username, self.entree_email, self.entree_mdp):
            entree.config(
                bg=couleurs["fond_carte"], fg=couleurs["texte"],
                insertbackground=couleurs["texte"], relief="flat",
                font=theme.get_font("texte"), highlightthickness=1,
                highlightbackground=couleurs["bordure"],
                highlightcolor=couleurs["emeraude"]
            )

        self.bouton_principal.config(
            bg=couleurs["emeraude"], fg="#FFFFFF",
            activebackground=couleurs["emeraude"],
            font=theme.get_font("bouton")
        )

        self.lien_bascule.config(
            bg=couleurs["fond"], fg=couleurs["emeraude"],
            font=theme.get_font("texte_petit")
        )

        self.bouton_theme.config(
            bg=couleurs["fond"], fg=couleurs["texte"],
            activebackground=couleurs["fond"],
            font=theme.get_font("texte")
        )
        icone_theme = "🌙" if theme.get_current_mode() == "clair" else "☀️"
        self.bouton_theme.config(text=icone_theme)


if __name__ == "__main__":
    def on_connexion(utilisateur):
        print("Connecté :", utilisateur)
        root.quit()

    root = tk.Tk()
    root.title("NetSentinel — Test LoginView")
    root.geometry("900x600")

    vue = LoginView(root, on_connexion_reussie=on_connexion)
    vue.pack(fill="both", expand=True)

    root.mainloop()