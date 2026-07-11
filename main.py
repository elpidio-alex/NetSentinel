"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

# =============================================================
# main.py — Point d'entrée de NetSentinel
# Outil de surveillance réseau et défense automatisée
# =============================================================
# Lance l'application graphique. Certaines fonctionnalités
# (capture réseau via sniffer.py, blocage pare-feu via
# defense.py) nécessitent les droits administrateur.
#
# Utilisation :
#     python main.py
# =============================================================

from gui.app import App


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()