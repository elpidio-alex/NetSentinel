# 🛡️ NetSentinel

**Outil de surveillance réseau et de défense automatisée pour PME africaines sans SOC.**

Développé dans le cadre du cursus *Licence Professionnelle Cybersécurité* à l'iPNet Institute of Technology (Lomé, Togo) — Sprint J4–J6, supervisé par M. SHABAN et M. AHOUNDA.

---

## 📋 Présentation

NetSentinel est une application desktop Windows qui permet à une PME de :

- **Capturer** le trafic réseau en temps réel (mode passif ou actif)
- **Détecter** automatiquement les menaces : scan de ports, brute-force, exfiltration de données
- **Bloquer** les IP suspectes via le pare-feu Windows (netsh) avec confirmation
- **Consulter** l'historique complet des événements et des captures passées
- **Gérer** une whitelist d'IP jamais bloquées (protection anti-auto-blocage)

---

## 🖥️ Prérequis

| Composant | Version minimale |
|---|---|
| Windows | 10 / 11 |
| Python | 3.10+ |
| MySQL Server | 8.0+ |
| Droits | Administrateur (capture réseau + pare-feu) |

---

## ⚙️ Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/elpidio-alex/netsentinel.git
cd netsentinel
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

```bash
copy .env.example .env
```

Éditez `.env` avec vos identifiants MySQL et vos seuils de détection.

### 4. Initialiser la base de données

Lancez MySQL et exécutez le schéma :

```bash
mysql -u root -p < netsentinel.sql
```

### 5. Lancer l'application

**Obligatoirement en tant qu'administrateur** (capture réseau + blocage pare-feu) :

```bash
python main.py
```

---

## 🗂️ Structure du projet

```
netsentinel/
├── main.py                  # Point d'entrée
├── config.py                # Chargement de la configuration (.env)
├── db.py                    # Couche d'accès base de données
├── auth.py                  # Authentification et gestion des comptes
├── sniffer.py               # Capture réseau (Scapy)
├── ids_engine.py            # Moteur de détection d'intrusion
├── defense.py               # Blocage IP et gestion whitelist
├── history_log.py           # Journalisation centralisée
│
├── gui/
│   ├── app.py               # Fenêtre racine et navigation
│   ├── theme.py             # Palette de couleurs et polices
│   ├── sidebar.py           # Menu latéral
│   ├── login_view.py        # Écran de connexion / inscription
│   ├── main_view.py         # Conteneur principal post-connexion
│   ├── monitor_view.py      # Surveillance réseau en temps réel
│   ├── alerts_view.py       # Alertes de sécurité
│   ├── blacklist_view.py    # Gestion des IP bloquées
│   ├── history_view.py      # Historique des événements
│   └── profile_view.py      # Profil utilisateur
│
├── netsentinel.sql          # Schéma de base de données
├── requirements.txt         # Dépendances Python
├── .env.example             # Template de configuration
├── .env                     # ⚠️ Non versionné (données sensibles)
└── README.md
```

---

## 🔍 Fonctionnalités de détection

| Menace | Mécanisme | Criticité |
|---|---|---|
| Scan de ports | ≥ N ports distincts depuis une même IP sur une fenêtre de temps | `warning` |
| Brute-force | ≥ N tentatives SYN vers un port sensible (SSH, RDP, FTP…) | `critique` |
| Exfiltration | Volume de données sortantes anormal vers une IP destination | `critique` |

Les seuils sont configurables dans `.env`.

---

## 🛡️ Architecture de défense
Paquet réseau
│
▼
Sniffer (Scapy)
│
▼
MoteurIDS ──── Alerte ──── DB (alerts) ──── AlertsView
│
▼
ModuleDefense
├── Mode passif : log uniquement
└── Mode actif  : règle netsh advfirewall (droits admin requis)

La **whitelist** est vérifiée en priorité absolue — aucune IP whitelistée ne peut être bloquée, même en mode actif.

---

## 🗄️ Base de données

| Table | Rôle |
|---|---|
| `users` | Comptes utilisateurs |
| `sessions` | Sessions de surveillance |
| `alerts` | Alertes générées par l'IDS |
| `blocked_ips` | IP bloquées (actives ou expirées) |
| `whitelist_ips` | IP protégées (jamais bloquables) |
| `open_ports` | Ports détectés durant les sessions |
| `captured_packets` | Paquets capturés (consultables depuis l'historique) |
| `history_log` | Journal d'audit unifié |

---

## 📦 Dépendances principales
scapy
mysql-connector-python
bcrypt
python-dotenv

---

## ⚠️ Avertissement légal

NetSentinel est conçu pour surveiller **uniquement les réseaux dont vous êtes administrateur ou pour lesquels vous avez une autorisation explicite**. Toute utilisation sur un réseau tiers sans autorisation est illégale.

---

## 👨‍💻 Auteur

**Elpidio Alexis AMOUSSOU**  
Étudiant en Première année de  Licence Professionnelle Cybersécurité — iPNet Institute of Technology, Lomé, Togo  
Superviseurs : M. SHABAN 

[![GitHub](https://img.shields.io/badge/GitHub-elpidio--alex-181717?logo=github)](https://github.com/elpidio-alex)

---

## 📄 Licence

Projet académique — tous droits réservés © 2026 Elpidio Alexis AMOUSSOU.