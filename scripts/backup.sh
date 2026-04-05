#!/usr/bin/env bash
# =============================================================================
# Horizon — Script de sauvegarde PostgreSQL
# Usage   : ./backup.sh [--compress] [--output-dir /path/to/backups]
# Prérequis: pg_dump, gzip (optionnel), variables d'env ou .env
# =============================================================================

set -euo pipefail

# ------------------------------------------------------------------ CONFIG
DB_NAME="${HORIZON_DB_NAME:-horizon_db}"
DB_USER="${HORIZON_DB_USER:-horizon_user}"
DB_HOST="${HORIZON_DB_HOST:-localhost}"
DB_PORT="${HORIZON_DB_PORT:-5433}"
BACKUP_DIR="${HORIZON_BACKUP_DIR:-./backups}"
RETENTION_DAYS="${HORIZON_BACKUP_RETENTION:-30}"    # Jours de rétention
COMPRESS=false
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# ------------------------------------------------------------------ ARGS
while [[ $# -gt 0 ]]; do
    case "$1" in
        --compress)       COMPRESS=true ;;
        --output-dir)     BACKUP_DIR="$2"; shift ;;
        *) echo "Option inconnue : $1"; exit 1 ;;
    esac
    shift
done

# ------------------------------------------------------------------ INIT
mkdir -p "${BACKUP_DIR}"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "=============================================="
echo " Horizon DB — Backup ${TIMESTAMP}"
echo " DB     : ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo " Dest   : ${BACKUP_DIR}"
echo " Compress: ${COMPRESS}"
echo "=============================================="

# ------------------------------------------------------------------ CHECK
command -v pg_dump >/dev/null 2>&1 || { echo "[ERROR] pg_dump non trouvé. Installez postgresql-client."; exit 1; }

# ------------------------------------------------------------------ DUMP
DUMP_FILE="${BACKUP_DIR}/horizon_backup_${TIMESTAMP}.sql"

echo "[$(date '+%H:%M:%S')] Lancement du dump..."

PGPASSWORD="${HORIZON_DB_PASSWORD:-horizon_pass}" pg_dump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-privileges \
    --verbose \
    --file="${DUMP_FILE}"

echo "[$(date '+%H:%M:%S')] Dump terminé : ${DUMP_FILE}"
echo "[$(date '+%H:%M:%S')] Taille brute  : $(du -sh "${DUMP_FILE}" | cut -f1)"

# ------------------------------------------------------------------ COMPRESS
if [ "${COMPRESS}" = true ]; then
    echo "[$(date '+%H:%M:%S')] Compression gzip..."
    gzip -f "${DUMP_FILE}"
    DUMP_FILE="${DUMP_FILE}.gz"
    echo "[$(date '+%H:%M:%S')] Fichier compressé : ${DUMP_FILE}"
    echo "[$(date '+%H:%M:%S')] Taille compressée : $(du -sh "${DUMP_FILE}" | cut -f1)"
fi

# ------------------------------------------------------------------ CHECKSUM
echo "[$(date '+%H:%M:%S')] Calcul du checksum SHA256..."
sha256sum "${DUMP_FILE}" > "${DUMP_FILE}.sha256"
echo "[$(date '+%H:%M:%S')] Checksum : $(cat "${DUMP_FILE}.sha256")"

# ------------------------------------------------------------------ PURGE anciens backups
echo "[$(date '+%H:%M:%S')] Purge des sauvegardes de plus de ${RETENTION_DAYS} jours..."
find "${BACKUP_DIR}" -name "horizon_backup_*.sql*" -mtime "+${RETENTION_DAYS}" -delete
echo "[$(date '+%H:%M:%S')] Purge terminée."

# ------------------------------------------------------------------ RÉSUMÉ
echo ""
echo "=============================================="
echo " Backup réussi"
echo " Fichier   : $(basename "${DUMP_FILE}")"
echo " Rétention : ${RETENTION_DAYS} jours"
echo " Log       : ${LOG_FILE}"
echo "=============================================="
