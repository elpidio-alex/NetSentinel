"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# theme.py — Gestion centralisée des thèmes (clair / sombre)
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Ce module centralise toutes les couleurs et la police utilisées
# dans l'application. Chaque vue importe ce module et appelle
# theme.get_colors() pour récupérer la palette active, au lieu
# de coder les couleurs en dur.
#
# Bascule : theme.toggle_theme() change le thème actif et
# retourne le nouveau mode ("clair" ou "sombre").
# =============================================================

# ── État global du thème actif ──────────────────────────────
# "clair" ou "sombre" — modifié par toggle_theme()
_current_mode = "clair"

# ── Police unique de l'application ──────────────────────────
FONT_FAMILY = "Times New Roman"

FONTS = {
    "titre":       (FONT_FAMILY, 20, "bold"),
    "titre_petit": (FONT_FAMILY, 15, "bold"),
    "sous_titre":  (FONT_FAMILY, 14, "bold"),
    "texte":       (FONT_FAMILY, 11, "normal"),
    "texte_petit": (FONT_FAMILY, 9,  "normal"),
    "bouton":      (FONT_FAMILY, 11, "bold"),
}

# ── Palette Mode Clair (jour) ───────────────────────────────
LIGHT_THEME = {
    "fond":            "#F7F5F0",  # Fond principal (ivoire doux)
    "fond_carte":       "#FFFFFF",  # Panneaux / cartes
    "texte":            "#1A1A1A",  # Texte principal
    "texte_secondaire": "#5A5A5A",  # Texte atténué (sous-titres, dates)
    "bordure":          "#D8D5CE",  # Séparateurs, contours
    "sidebar":          "#EDEAE2",  # Fond du menu latéral
    "emeraude":         "#2E8B6F",  # Statut OK / bouton principal
    "ambre":            "#B8890C",  # Alerte moyenne (foncé pour lisibilité sur fond clair)
    "rouge":            "#C0392B",  # Alerte critique
}

# ── Palette Mode Sombre (nuit) ───────────────────────────────
DARK_THEME = {
    "fond":            "#0D1321",  # Fond principal (marine profond)
    "fond_carte":       "#161D2E",  # Panneaux / cartes
    "texte":            "#EDEDE8",  # Texte principal
    "texte_secondaire": "#9CA3AF",  # Texte atténué
    "bordure":          "#2A3345",  # Séparateurs, contours
    "sidebar":          "#111827",  # Fond du menu latéral
    "emeraude":         "#2E8B6F",  # Statut OK / bouton principal
    "ambre":            "#F2C744",  # Alerte moyenne (clair pour lisibilité sur fond sombre)
    "rouge":            "#D9463C",  # Alerte critique
}


def get_colors():
    """
    Retourne le dictionnaire de couleurs du thème actuellement actif.

    Retourne :
        dict : palette de couleurs (clés identiques dans les deux thèmes,
               donc aucune vue n'a besoin de savoir quel thème est actif)
    """
    return LIGHT_THEME if _current_mode == "clair" else DARK_THEME


def get_font(style="texte"):
    """
    Retourne un tuple de police prêt à l'emploi pour Tkinter.

    Paramètres :
        style (str) : clé dans FONTS ("titre", "sous_titre", "texte", ...)

    Retourne :
        tuple : (famille, taille, style) — ex: ("Times New Roman", 11, "normal")
    """
    return FONTS.get(style, FONTS["texte"])


def get_current_mode():
    """Retourne le mode actif : "clair" ou "sombre"."""
    return _current_mode


def toggle_theme():
    """
    Bascule entre mode clair et mode sombre.

    Retourne :
        str : le nouveau mode actif ("clair" ou "sombre")

    Utilisation typique (dans sidebar.py) :
        nouveau_mode = theme.toggle_theme()
        app.refresh_all_views()   # méthode à définir dans app.py
    """
    global _current_mode
    _current_mode = "sombre" if _current_mode == "clair" else "clair"
    return _current_mode


def set_theme(mode):
    """
    Force un thème spécifique (utile au démarrage si on veut
    mémoriser le dernier choix de l'utilisateur).

    Paramètres :
        mode (str) : "clair" ou "sombre"
    """
    global _current_mode
    if mode in ("clair", "sombre"):
        _current_mode = mode