# =============================================================
# auth.py — Authentification et gestion des utilisateurs
# NetSentinel — Surveillance réseau et défense automatisée
# =============================================================
# Ce module gère l'inscription, la connexion, le hachage des
# mots de passe (bcrypt) et la modification du profil. Toute
# vérification d'identité passe par les fonctions de ce fichier
# — jamais de comparaison de mot de passe en clair ailleurs dans
# l'application. Les connexions et inscriptions réussies sont
# journalisées dans history_log.
# =============================================================

import bcrypt
from db import executer_requete, recuperer_un
from history_log import logger_connexion, logger_inscription


def hacher_mot_de_passe(mot_de_passe):
    """
    Hache un mot de passe en clair avec bcrypt (sel généré
    automatiquement, intégré au hash retourné).

    Paramètres :
        mot_de_passe (str) : mot de passe en clair

    Retourne :
        str : hash bcrypt (à stocker tel quel en base)
    """
    sel = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(mot_de_passe.encode("utf-8"), sel)
    return hash_bytes.decode("utf-8")


def verifier_mot_de_passe(mot_de_passe, hash_stocke):
    """
    Compare un mot de passe en clair à un hash bcrypt stocké.

    Paramètres :
        mot_de_passe (str) : mot de passe saisi par l'utilisateur
        hash_stocke (str)  : hash bcrypt récupéré depuis la base

    Retourne :
        bool : True si le mot de passe correspond
    """
    try:
        return bcrypt.checkpw(
            mot_de_passe.encode("utf-8"),
            hash_stocke.encode("utf-8")
        )
    except (ValueError, AttributeError):
        # Hash corrompu ou mal formé
        return False


def utilisateur_existe(username=None, email=None, exclure_id=None):
    """
    Vérifie si un username ou un email est déjà utilisé.

    Paramètres :
        username (str|None)
        email (str|None)
        exclure_id (int|None) : si fourni, ignore l'utilisateur ayant
            cet id (utile pour vérifier l'unicité lors d'une modification
            de profil, sans se bloquer soi-même)

    Retourne :
        bool : True si un utilisateur correspondant existe déjà
    """
    if username:
        if exclure_id:
            resultat = recuperer_un(
                "SELECT id FROM users WHERE username = %s AND id != %s",
                (username, exclure_id)
            )
        else:
            resultat = recuperer_un(
                "SELECT id FROM users WHERE username = %s", (username,)
            )
        if resultat:
            return True
    if email:
        if exclure_id:
            resultat = recuperer_un(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                (email, exclure_id)
            )
        else:
            resultat = recuperer_un(
                "SELECT id FROM users WHERE email = %s", (email,)
            )
        if resultat:
            return True
    return False


def inscrire_utilisateur(username, email, mot_de_passe):
    """
    Crée un nouvel utilisateur en base après vérification des
    doublons et hachage du mot de passe.

    Paramètres :
        username (str)
        email (str)
        mot_de_passe (str) : mot de passe en clair

    Retourne :
        dict : {"succes": bool, "message": str, "user_id": int|None}
    """
    if not username or not email or not mot_de_passe:
        return {"succes": False, "message": "Tous les champs sont requis.", "user_id": None}

    if len(mot_de_passe) < 8:
        return {"succes": False, "message": "Le mot de passe doit contenir au moins 8 caractères.", "user_id": None}

    if utilisateur_existe(username=username):
        return {"succes": False, "message": "Ce nom d'utilisateur est déjà pris.", "user_id": None}

    if utilisateur_existe(email=email):
        return {"succes": False, "message": "Cet email est déjà utilisé.", "user_id": None}

    hash_mdp = hacher_mot_de_passe(mot_de_passe)

    nouvel_id = executer_requete(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        (username, email, hash_mdp),
        commit=True,
        retour_id=True
    )

    if nouvel_id:
        logger_inscription(username, nouvel_id)
        return {"succes": True, "message": "Compte créé avec succès.", "user_id": nouvel_id}
    return {"succes": False, "message": "Erreur lors de la création du compte.", "user_id": None}


def connecter_utilisateur(username, mot_de_passe):
    """
    Vérifie les identifiants d'un utilisateur pour la connexion.

    Paramètres :
        username (str)
        mot_de_passe (str) : mot de passe en clair saisi

    Retourne :
        dict : {"succes": bool, "message": str, "user": dict|None}
    """
    utilisateur = recuperer_un(
        "SELECT id, username, email, password_hash FROM users WHERE username = %s",
        (username,)
    )

    if not utilisateur:
        return {"succes": False, "message": "Nom d'utilisateur ou mot de passe incorrect.", "user": None}

    if not verifier_mot_de_passe(mot_de_passe, utilisateur["password_hash"]):
        return {"succes": False, "message": "Nom d'utilisateur ou mot de passe incorrect.", "user": None}

    # On ne renvoie jamais le hash au reste de l'application
    utilisateur_public = {
        "id": utilisateur["id"],
        "username": utilisateur["username"],
        "email": utilisateur["email"]
    }

    logger_connexion(utilisateur_public["username"], utilisateur_public["id"])

    return {"succes": True, "message": "Connexion réussie.", "user": utilisateur_public}


def modifier_profil(user_id, nouveau_username, nouvel_email):
    """
    Modifie le username et/ou l'email d'un utilisateur existant.

    Paramètres :
        user_id (int)
        nouveau_username (str)
        nouvel_email (str)

    Retourne :
        dict : {"succes": bool, "message": str, "user": dict|None}
    """
    if not nouveau_username or not nouvel_email:
        return {"succes": False, "message": "Tous les champs sont requis.", "user": None}

    if utilisateur_existe(username=nouveau_username, exclure_id=user_id):
        return {"succes": False, "message": "Ce nom d'utilisateur est déjà pris.", "user": None}

    if utilisateur_existe(email=nouvel_email, exclure_id=user_id):
        return {"succes": False, "message": "Cet email est déjà utilisé.", "user": None}

    succes = executer_requete(
        "UPDATE users SET username = %s, email = %s WHERE id = %s",
        (nouveau_username, nouvel_email, user_id),
        commit=True
    )

    if succes:
        utilisateur_public = {"id": user_id, "username": nouveau_username, "email": nouvel_email}
        return {"succes": True, "message": "Profil mis à jour avec succès.", "user": utilisateur_public}
    return {"succes": False, "message": "Erreur lors de la mise à jour du profil.", "user": None}


def modifier_mot_de_passe(user_id, ancien_mot_de_passe, nouveau_mot_de_passe):
    """
    Change le mot de passe d'un utilisateur après vérification
    de l'ancien mot de passe.

    Paramètres :
        user_id (int)
        ancien_mot_de_passe (str) : mot de passe actuel en clair
        nouveau_mot_de_passe (str) : nouveau mot de passe en clair

    Retourne :
        dict : {"succes": bool, "message": str}
    """
    if not ancien_mot_de_passe or not nouveau_mot_de_passe:
        return {"succes": False, "message": "Tous les champs sont requis."}

    if len(nouveau_mot_de_passe) < 8:
        return {"succes": False, "message": "Le nouveau mot de passe doit contenir au moins 8 caractères."}

    utilisateur = recuperer_un(
        "SELECT password_hash FROM users WHERE id = %s", (user_id,)
    )
    if not utilisateur:
        return {"succes": False, "message": "Utilisateur introuvable."}

    if not verifier_mot_de_passe(ancien_mot_de_passe, utilisateur["password_hash"]):
        return {"succes": False, "message": "Mot de passe actuel incorrect."}

    nouveau_hash = hacher_mot_de_passe(nouveau_mot_de_passe)
    succes = executer_requete(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (nouveau_hash, user_id),
        commit=True
    )

    if succes:
        return {"succes": True, "message": "Mot de passe modifié avec succès."}
    return {"succes": False, "message": "Erreur lors du changement de mot de passe."}


if __name__ == "__main__":
    # Test manuel : python auth.py
    resultat = inscrire_utilisateur("test_admin", "test@netsentinel.local", "motdepasse123")
    print(resultat)

    connexion = connecter_utilisateur("test_admin", "motdepasse123")
    print(connexion)