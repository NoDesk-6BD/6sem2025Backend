#!/bin/bash
# =====================================
# Backup completo do PostgreSQL - Nodesk (LGPD + offsite)
# =====================================
set -o errexit
set -o pipefail
set -o nounset

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../.env"
[ -f "$ENV_FILE" ] && export $(grep -v '^#' "$ENV_FILE" | xargs)

BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/../../backups/full}"
LOG_DIR="${LOG_DIR:-$SCRIPT_DIR/../../backups/logs}"
AUDIT_LOG="$LOG_DIR/auditoria_backups.log"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
GPG_PASSPHRASE="${GPG_PASSPHRASE:-}"
RCLONE_REMOTE="${RCLONE_REMOTE:-gdrive:nodesk_backups}" # destino Google Drive

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

DATE=$(date +%F_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/backup_full_${DATE}.sql"
GPG_FILE="${BACKUP_FILE}.gpg"
LOG_FILE="$LOG_DIR/backup_full_${DATE}.log"

cleanup() {
    unset PGPASSWORD || true
    [ -f "${BACKUP_FILE}.tmp" ] && rm -f "${BACKUP_FILE}.tmp" || true
}
trap cleanup EXIT

export PGPASSWORD="${DB_PASS:-}" || true

{
    echo "====================================="
    echo "Iniciando backup completo do banco '${DB_NAME:-unknown}' em $DATE..."
    echo "Host: ${DB_HOST:-localhost}:${DB_PORT:-5432}"
    echo "Realizado por: $(whoami) on $(hostname)"
} | tee -a "$LOG_FILE"

# --- Dump SQL ---
if ! pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" "${DB_NAME:-postgres}" > "$BACKUP_FILE" 2>> "$LOG_FILE"; then
    echo "❌ Erro ao executar pg_dump" | tee -a "$LOG_FILE"
    exit 1
fi

# --- Verificação ---
if [ ! -s "$BACKUP_FILE" ]; then
    echo "⚠️ Arquivo de backup vazio" | tee -a "$LOG_FILE"
    exit 1
fi

CHECKSUM=$(sha256sum "$BACKUP_FILE" | awk '{print $1}')
echo "✔️ Dump criado: $BACKUP_FILE" | tee -a "$LOG_FILE"
echo "SHA256: $CHECKSUM" | tee -a "$LOG_FILE"

# --- Criptografia ---
if [ -n "$GPG_PASSPHRASE" ]; then
    echo "$GPG_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 --symmetric --cipher-algo AES256 -o "$GPG_FILE" "$BACKUP_FILE" 2>> "$LOG_FILE"
    shred -u "$BACKUP_FILE" 2>> "$LOG_FILE" || rm -f "$BACKUP_FILE"
    echo "✔️ Backup criptografado: $GPG_FILE" | tee -a "$LOG_FILE"
else
    echo "⚠️ GPG_PASSPHRASE não definida. Backup em texto plano." | tee -a "$LOG_FILE"
    GPG_FILE="$BACKUP_FILE"
fi

# --- Upload Google Drive via Rclone ---
if [ -n "$RCLONE_REMOTE" ]; then
    if command -v rclone >/dev/null 2>&1; then
        echo "📤 Upload para Drop box ($RCLONE_REMOTE)..." | tee -a "$LOG_FILE"
        if rclone copyto "$GPG_FILE" "$RCLONE_REMOTE/$(basename "$GPG_FILE")" --no-traverse 2>> "$LOG_FILE"; then
            echo "✔️ Upload concluído" | tee -a "$LOG_FILE"
        else
            echo "⚠️ Falha no upload" | tee -a "$LOG_FILE"
        fi
    else
        echo "⚠️ Rclone não encontrado. Instale rclone." | tee -a "$LOG_FILE"
    fi
fi

# --- Auditoria ---
echo "$(date +'%F %T') | user=$(whoami) | host=$(hostname) | file=$(basename "$GPG_FILE") | sha256=$CHECKSUM | size=$(stat -c%s "$GPG_FILE")" >> "$AUDIT_LOG"

# --- Retenção ---
find "$BACKUP_DIR" -type f -name "*.sql*" -mtime +$RETENTION_DAYS -print -delete 2>> "$LOG_FILE" || true
find "$LOG_DIR" -type f -name "*.log" -mtime +$RETENTION_DAYS -print -delete 2>> "$LOG_FILE" || true

echo "Backup finalizado em $(date)" | tee -a "$LOG_FILE"
echo "=====================================" | tee -a "$LOG_FILE"
