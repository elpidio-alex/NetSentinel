"""
Date : 11/07/2026
Auteur : Elpidio Alexis AMOUSSOU
Email : amoussouelpidioalexis@gmail.com

"""

-- =============================================================
-- netsentinel.sql — Schéma de base de données NetSentinel
-- Outil de surveillance réseau et défense automatisée
-- =============================================================

CREATE DATABASE IF NOT EXISTS netsentinel_db CHARACTER SET utf8mb4;
USE netsentinel_db;

-- ── Table des utilisateurs ─────────────────────────────────
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(63) UNIQUE NOT NULL,
    email VARCHAR(127) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Table des sessions de surveillance ─────────────────────
CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    mode ENUM('passif', 'actif') DEFAULT 'passif',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── Table des alertes IDS ───────────────────────────────────
CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    ip_source VARCHAR(63) NOT NULL,
    type_menace VARCHAR(127) NOT NULL,
    criticite ENUM('info', 'warning', 'critique') DEFAULT 'info',
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- ── Table des IP bloquées / blacklist ───────────────────────
CREATE TABLE blocked_ips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(63) UNIQUE NOT NULL,
    raison VARCHAR(255),
    mode ENUM('passif', 'actif') DEFAULT 'passif',
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    active BOOLEAN DEFAULT TRUE
);

-- ── Table des ports détectés ─────────────────────────────────
CREATE TABLE open_ports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    port INT NOT NULL,
    proto ENUM('tcp', 'udp') NOT NULL,
    processus VARCHAR(127),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- ── Table whitelist (IP jamais bloquées) ────────────────────
CREATE TABLE whitelist_ips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(63) UNIQUE NOT NULL,
    raison VARCHAR(255),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE history_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type ENUM('alerte', 'blocage', 'deblocage', 'connexion', 'inscription') NOT NULL,
    ip VARCHAR(63) NULL,
    description VARCHAR(255) NOT NULL,
    username VARCHAR(63) NULL,
    user_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE captured_packets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    horodatage DATETIME NOT NULL,
    ip_source VARCHAR(63),
    ip_destination VARCHAR(63),
    protocole VARCHAR(10),
    port_source INT,
    port_destination INT,
    taille INT,
    flags_tcp VARCHAR(20),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);