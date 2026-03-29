# 🚀 Horizon Backend - Cloud Management API

Bienvenue sur le backend de **Horizon**, une API de gestion de machines virtuelles (VM) performante, sécurisée et scalable, construite avec **FastAPI** et **SQLAlchemy 2.0**.

---

## 🛠 Stack Technique

- **Framework :** [FastAPI](https://fastapi.tiangolo.com/) (Asynchrone)
- **Base de données :** PostgreSQL avec [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Mode Async via `asyncpg`)
- **Validation :** [Pydantic v2](https://docs.pydantic.dev/latest/)
- **Migrations :** Alembic
- **Emails :** FastAPI-Mail (SMTP Asynchrone)
- **Sécurité :** Bcrypt (Passlib) & JWT (Python-jose)
- **Configuration :** Pydantic-Settings (Gestion via `.env`)

---

## 🏗 Architecture du Projet

Le projet suit une architecture propre (Clean Architecture) basée sur les patterns **Repository** et **Service** pour garantir une séparation stricte des responsabilités.

```text
app/
├── api/
│   └── v1/
│       ├── api.py             # Router principal
│       └── endpoints/         # Routes HTTP (Logique de transport)
├── core/
│   └── config.py              # Configuration & Variables d'env
├── db/
│   └── base.py                # Session SQLAlchemy & Engine Async
├── models/
│   ├── base_models.py         # Modèles SQLAlchemy (Reflet du SQL)
│   └── enums.py               # Énumérations PostgreSQL
├── repositories/              # Couche d'accès aux données (SQL pur)
├── schemas/                   # Schémas Pydantic (Validation & Sérialisation)
├── services/                  # Logique Métier (Emails, Orchestration)
├── main.py                    # Point d'entrée de l'application
├── init_db.py                 # Script de création des tables
└── seed_admin.py              # Script d'injection d'un administrateur
```

---

## ✨ Fonctionnalités Implémentées

### 1. Demande de création de compte (`POST /auth/register-request`)
- **Validation stricte :** Utilisation de Pydantic v2 pour valider les entrées (longueur, format email).
- **Gestion des conflits :** Retourne une erreur `409 Conflict` si l'email existe déjà dans la table `users`.
- **Logs d'audit :** Chaque tentative est enregistrée dans la table `audit_logs` (avec IP du client, type d'action et succès/échec).
- **Notifications :** Envoi automatique d'un email HTML professionnel à tous les administrateurs actifs (`role_type = 'admin'`) pour approbation.
- **Asynchronisme :** Tout le processus (DB et Email) est non-bloquant pour des performances optimales.

### 2. Gestion de la Base de Données
- Mapping complet du schéma PostgreSQL (Users, Roles, VMs, Policies, Quotas, Nodes, ISOs, etc.).
- Utilisation des types `ENUM` natifs de PostgreSQL pour la sécurité des données.
- Contraintes d'intégrité (Check constraints, Foreign Keys avec `ON DELETE CASCADE`).

---

## 🚀 Installation et Démarrage

### 1. Cloner et préparer l'environnement
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration du fichier `.env`
Copiez le fichier d'exemple :
```bash
cp .env.example .env
```

> ⚠️ **CRITIQUE : CONFIGURATION DE LA BASE DE DONNÉES**
> 
> Ouvrez votre fichier `.env` et assurez-vous que les variables suivantes correspondent à votre instance PostgreSQL locale :
> - **POSTGRES_USER** : Votre utilisateur (ex: `postgres`)
> - **POSTGRES_PASSWORD** : Votre mot de passe
> - **POSTGRES_SERVER** : `localhost` ou l'IP du serveur de base de données
> - **POSTGRES_DB** : Le nom de la base de données (elle doit être **déjà créée** dans Postgres)

---

## 📧 Configuration du SMTP (Gmail)

Pour envoyer des emails de notification, vous devez utiliser un **Mot de passe d'application** Google.

### Comment générer un mot de passe d'application Google :
1. Connectez-vous à votre [Compte Google](https://myaccount.google.com/).
2. Allez dans la section **Sécurité**.
3. Activez la **Validation en deux étapes** (si ce n'est pas déjà fait).
4. Recherchez "Mots de passe d'application" dans la barre de recherche en haut.
5. Donnez un nom à l'application (ex: `Horizon API`) et cliquez sur **Créer**.
6. Copiez le code de **16 caractères** affiché dans le cadre jaune.
7. Collez ce code dans votre fichier `.env` à la ligne `SMTP_PASSWORD`.

**Exemple de configuration SMTP dans `.env` :**
```env
SMTP_USER="votre.email@gmail.com"
SMTP_PASSWORD="abcd efgh ijkl mnop"  # Code de 16 caractères de Google
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_TLS=True
EMAILS_FROM_EMAIL="votre.email@gmail.com"
```

---

## 🏗 Initialisation et Lancement

1. **Créer les tables et les types ENUM :**
   ```bash
   python3 app/init_db.py
   ```

2. **Créer l'administrateur par défaut :**
   *Indispensable pour recevoir les mails de notification.*
   *Modifiez l'email dans `app/seed_admin.py` avant de lancer :*
   ```bash
   python3 app/seed_admin.py
   ```

3. **Lancer le serveur :**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 🧪 Documentation OpenAPI
Accédez aux interfaces interactives une fois le serveur lancé :
- **Swagger UI (Docs) :** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc :** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---
*Fichier README généré pour le projet Horizon Backend.*
