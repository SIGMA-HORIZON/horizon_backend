# Horizon — API SIGMA / ENSPY

Monorepo unique : package Python **`horizon/`** à la racine du dépôt, architecture par fonctionnalités (`features/`), couches `shared/` et `infrastructure/`.

## Prérequis

- Python 3.11+ (recommandé ; les tests ont été validés avec 3.12 en local)
- Docker et Docker Compose (pour l’exécution compose et pour **pytest** + Testcontainers)

## Configuration

Copier `.env.example` vers `.env` à la racine et ajuster les secrets (`JWT_SECRET_KEY`, `APP_SECRET_KEY`, etc.). Pour Compose, les variables critiques peuvent aussi être surchargées dans `docker-compose.yml`.

## Démarrage avec Docker

À la racine du dépôt :

```bash
docker compose up --build -d
```

L’API est exposée sur **<http://localhost:8000>** (`/docs`, `/health`). Les migrations Alembic s’exécutent via le service `migrations` avant le démarrage de `api`.

Seed optionnel (profil Compose) :

```bash
docker compose --profile seed run --rm seed
```

## Migrations (local)

Avec Postgres accessible et `DATABASE_URL` défini, depuis la racine du dépôt :

```bash
export PYTHONPATH=.
alembic upgrade head
```

## Seed (local)

```bash
export PYTHONPATH=.
python scripts/seed.py
```

(`PYTHONPATH=.` place la racine du dépôt sur le chemin d’import pour le package `horizon`.)

## Proxmox (optionnel)

L’intégration **proxmoxer** est **désactivée par défaut** (`PROXMOX_ENABLED=false`) : création / arrêt / suppression de VM ne font **aucun appel** au cluster et le comportement reste celui d’Horizon sans Proxmox.

Pour l’activer :

1. Appliquer les migrations (`alembic upgrade head`) — la révision `0002` crée les tables `iso_proxmox_templates` et `proxmox_node_mappings` (lignes d’exemple pour REM / RAM / EMILIA).
2. Renseigner dans `.env` : `PROXMOX_ENABLED=true`, `PROXMOX_HOST`, `PROXMOX_USER`, `PROXMOX_TOKEN_ID`, `PROXMOX_TOKEN_SECRET`, `PROXMOX_VERIFY_SSL` (souvent `false` en labo).
3. Ajuster les **mappings** nœud métier → nom de nœud Proxmox (API admin ou table `proxmox_node_mappings`) et une ligne **par ISO** dans `iso_proxmox_templates` (VMID du template à cloner).
4. Optionnel : `PROXMOX_DEFAULT_NODE` si un nœud métier n’a pas encore de ligne de mapping ; `PROXMOX_NET0_TEMPLATE` pour le modèle `net0` (ex. `virtio,bridge=vmbr0`), complété par `,tag={vlan_id}` si la VM a un VLAN.

Après un **seed** local, des correspondances ISO → template **fictives** (VMID `9000+`) sont insérées : à remplacer en production par les vrais ID de templates Proxmox.

Endpoints d’exploration / pause : préfixe admin existant, sous-chemins `.../proxmox/...` (voir OpenAPI `/docs`).

## Tests

Créer un environnement virtuel, installer les dépendances, lancer la suite (Docker requis pour Postgres Testcontainers). `pytest.ini` définit déjà `pythonpath = .` :

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/pytest tests/ -v
```
