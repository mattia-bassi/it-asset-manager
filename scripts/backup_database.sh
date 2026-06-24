#!/bin/bash
#
# Script Backup Automatico Database - IT Asset Management
# Esegue backup giornaliero e mantiene ultimi 5 backup
#

# Configurazione
BACKUP_DIR="/share/ZFS18_DATA/Container/AssetManagment/backup/database"
LOG_DIR="/share/ZFS18_DATA/Container/AssetManagment/backup/logs"
CONTAINER_NAME="asset-mariadb"
DB_USER="root"
DB_PASSWORD="root_password_2025"
DB_NAME="assetdb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/auto_backup_$TIMESTAMP.sql.gz"
KEEP_BACKUPS=5

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Inizio backup
log "Inizio backup automatico database..."

# Verifica container attivo
if ! /share/ZFS530_DATA/.qpkg/container-station/bin/docker ps | grep -q $CONTAINER_NAME; then
    log "ERRORE: Container $CONTAINER_NAME non in esecuzione!"
    exit 1
fi

# Crea directory backup se non esiste
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Esegui backup
log "Creazione backup in: $BACKUP_FILE"
/share/ZFS530_DATA/.qpkg/container-station/bin/docker exec $CONTAINER_NAME mysqldump \
    -u$DB_USER \
    -p$DB_PASSWORD \
    --single-transaction \
    --routines \
    --triggers \
    --quick \
    --lock-tables=false \
    $DB_NAME | gzip > "$BACKUP_FILE"

# Verifica successo
if [ $? -eq 0 ] && [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    log "✅ Backup completato con successo! Dimensione: $BACKUP_SIZE"
else
    log "❌ ERRORE: Backup fallito!"
    exit 1
fi

# Pulizia backup vecchi (mantieni solo ultimi 5)
log "Pulizia backup vecchi (mantengo ultimi $KEEP_BACKUPS)..."
cd "$BACKUP_DIR"
ls -t auto_backup_*.sql.gz 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -f

REMAINING=$(ls -1 auto_backup_*.sql.gz 2>/dev/null | wc -l)
log "Backup rimanenti: $REMAINING"

# Lista backup attuali
log "Backup disponibili:"
ls -lh auto_backup_*.sql.gz 2>/dev/null | tail -$KEEP_BACKUPS

log "Backup automatico completato!"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup completato: $BACKUP_FILE ($(ls -lh "$BACKUP_FILE" | awk '{print $5}'))" >> "$LOG_DIR/backup.log"
exit 0
