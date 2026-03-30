#!/usr/bin/env bash
# backup_db.sh — copy the SQLite database to a backup location.
#
# Usage:
#   DB_PATH=/data/db.sqlite3 BACKUP_DIR=/backups ./scripts/backup_db.sh
#
# Designed to be run as a cron job. Backups are named by timestamp.
# Set BACKUP_DIR to a mounted volume or remote path (e.g. via rclone).

set -euo pipefail

DB_PATH="${DB_PATH:-/data/db.sqlite3}"
BACKUP_DIR="${BACKUP_DIR:-/data/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DEST="${BACKUP_DIR}/db_${TIMESTAMP}.sqlite3"

mkdir -p "$BACKUP_DIR"

# Use SQLite's backup API via the .backup command for a consistent snapshot
sqlite3 "$DB_PATH" ".backup '$DEST'"

echo "Backup written to $DEST"

# Optional: retain only the 10 most recent backups
ls -t "${BACKUP_DIR}"/db_*.sqlite3 | tail -n +11 | xargs -r rm --
