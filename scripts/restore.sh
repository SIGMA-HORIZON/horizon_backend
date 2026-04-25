#!/usr/bin/env bash
# =============================================================================
# Horizon - Script de restauration PostgreSQL
# Usage   : ./restore.sh --file /path/to/horizon_backup_YYYYMMDD_HHMMSS.sql[.gz]
# ATTENTION: Supprime et recrée la base cible. Utiliser avec précaution.
# =============================================================================

set -euo pipefail

DB_NAME="${HORIZON_DB_NAME:-horizon_db}"
DB_USER="${HORIZON_DB_USER:-horizon_user}"
DB_HOST="${HORIZON_DB_HOST:-localhost}"
DB_PORT="${HORIZON_DB_PORT:-5433}"
DB_ADMIN_USER="${HORIZON_DB_ADMIN_USER:-postgres}"
BACKUP_FILE=""
SKIP_CONFIRM=false
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="./restore_${TIMESTAMP}.log"

# ------------------------------------------------------------------ ARGS
while [[ $# -gt 0 ]]; do
    case "$1" in
        --file)          BACKUP_FILE="$2"; shift ;;
        --yes)           SKIP_CONFIRM=true ;;
        *) echo "Option inconnue : $1"; exit 1 ;;
    esac
    shift
done

# ------------------------------------------------------------------ VALIDATE
if [ -z "${BACKUP_FILE}" ]; then
    echo "[ERROR] --file requis. Usage : ./restore.sh --file backup.sql[.gz]"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[ERROR] Fichier non trouvé : ${BACKUP_FILE}"
    exit 1
fi

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=============================================="
echo " Horizon DB - Restauration ${TIMESTAMP}"
echo " Source : ${BACKUP_FILE}"
echo " Cible  : ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "=============================================="
echo ""
echo "[ATTENTION] Cette opération va SUPPRIMER et RECRÉER la base ${DB_NAME}."

# ------------------------------------------------------------------ CHECKSUM
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
    echo "[$(date '+%H:%M:%S')] Vérification du checksum SHA256..."
    sha256sum --check "${CHECKSUM_FILE}" || { echo "[ERROR] Checksum invalide - fichier corrompu."; exit 1; }
    echo "[$(date '+%H:%M:%S')] Checksum OK."
else
    echo "[WARN] Fichier .sha256 absent - vérification du checksum ignorée."
fi

# ------------------------------------------------------------------ CONFIRMATION
if [ "${SKIP_CONFIRM}" = false ]; then
    read -rp "Confirmer la restauration ? [oui/NON] : " CONFIRM
    if [ "${CONFIRM}" != "oui" ]; then
        echo "Restauration annulée."
        exit 0
    fi
fi

# ------------------------------------------------------------------ DÉCOMPRESSION (si .gz)
RESTORE_FILE="${BACKUP_FILE}"
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    echo "[$(date '+%H:%M:%S')] Décompression du fichier..."
    RESTORE_FILE="${BACKUP_FILE%.gz}"
    gunzip -kf "${BACKUP_FILE}"
    echo "[$(date '+%H:%M:%S')] Fichier décompressé : ${RESTORE_FILE}"
fi

# ------------------------------------------------------------------ DROP & RECREATE
echo "[$(date '+%H:%M:%S')] Suppression de la base existante..."
PGPASSWORD="${HORIZON_DB_ADMIN_PASSWORD:-postgres}" psql \
    --host="${DB_HOST}" --port="${DB_PORT}" \
    --username="${DB_ADMIN_USER}" \
    --dbname="postgres" \
    --command="DROP DATABASE IF EXISTS ${DB_NAME};"

echo "[$(date '+%H:%M:%S')] Création d'une nouvelle base vide..."
PGPASSWORD="${HORIZON_DB_ADMIN_PASSWORD:-postgres}" psql \
    --host="${DB_HOST}" --port="${DB_PORT}" \
    --username="${DB_ADMIN_USER}" \
    --dbname="postgres" \
    --command="CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} ENCODING 'UTF8';"

# ------------------------------------------------------------------ RESTORE
echo "[$(date '+%H:%M:%S')] Restauration en cours..."
PGPASSWORD="${HORIZON_DB_PASSWORD:-horizon_pass}" psql \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --file="${RESTORE_FILE}"

echo "[$(date '+%H:%M:%S')] Restauration terminée."

# ------------------------------------------------------------------ NETTOYAGE fichier décompressé temporaire
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    rm -f "${RESTORE_FILE}"
    echo "[$(date '+%H:%M:%S')] Fichier temporaire supprimé."
fi

echo ""
echo "=============================================="
echo " Restauration réussie"
echo " Base    : ${DB_NAME}"
echo " Log     : ${LOG_FILE}"
echo "=============================================="
