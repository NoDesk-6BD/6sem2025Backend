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

BASE_BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/../../backups}"
BACKUP_DIR="$BASE_BACKUP_DIR/backups"
LOG_DIR="$BASE_BACKUP_DIR/auditoria"
AUDIT_LOG="$LOG_DIR/auditoria_backups.log"

RETENTION_DAYS="${RETENTION_DAYS:-30}"
GPG_PASSPHRASE="${GPG_PASSPHRASE:-}"
RCLONE_REMOTE="${RCLONE_REMOTE:-dropbox:nodesk_backups}"
DB_CONTAINER_NAME="${DB_CONTAINER_NAME:-nodesk-db}"

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

DATE=$(date +%F_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/backup_full_${DATE}.sql"
GPG_FILE="${BACKUP_FILE}.gpg"
LOG_FILE="$LOG_DIR/backup_full_${DATE}.log"

cleanup() {
    [ -f "${BACKUP_FILE}.tmp" ] && rm -f "${BACKUP_FILE}.tmp" || true
}
trap cleanup EXIT

log_delete() {
    local filepath="$1"
    echo "$(date +'%F %T') | EXCLUSÃO | user=$(whoami) | host=$(hostname) | file=$(basename "$filepath")" | tee -a "$AUDIT_LOG"
}

{
    echo "====================================="
    echo "Iniciando backup completo do banco '${DB_NAME:-unknown}' em $DATE..."
    echo "Container: ${DB_CONTAINER_NAME}"
    echo "Banco: ${DB_NAME:-postgres}"
    echo "Usuário: ${DB_USER:-postgres}"
    echo "Realizado por: $(whoami) on $(hostname)"
} | tee -a "$LOG_FILE"

# --- Verifica se o container está rodando ---
if ! docker ps --format '{{.Names}}' | grep -q "$DB_CONTAINER_NAME"; then
    echo "❌ Container '$DB_CONTAINER_NAME' não está rodando." | tee -a "$LOG_FILE"
    exit 1
fi

# --- Execução do pg_dump dentro do container ---
if ! docker exec -t "$DB_CONTAINER_NAME" pg_dump -U "${DB_USER:-postgres}" "${DB_NAME:-postgres}" > "$BACKUP_FILE" 2>> "$LOG_FILE"; then
    echo "❌ Erro ao executar pg_dump dentro do container '$DB_CONTAINER_NAME'" | tee -a "$LOG_FILE"
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

# --- Upload do backup ---
if [ -n "$RCLONE_REMOTE" ]; then
    if command -v rclone >/dev/null 2>&1; then
        REMOTE_BACKUP_DIR="${RCLONE_REMOTE}/backups"
        echo "📤 Upload de backup para ($REMOTE_BACKUP_DIR)..." | tee -a "$LOG_FILE"
        if rclone mkdir "$REMOTE_BACKUP_DIR" && rclone copyto "$GPG_FILE" "$REMOTE_BACKUP_DIR/$(basename "$GPG_FILE")" --no-traverse 2>> "$LOG_FILE"; then
            echo "✔️ Upload concluído" | tee -a "$LOG_FILE"
        else
            echo "⚠️ Falha no upload do backup" | tee -a "$LOG_FILE"
        fi
    else
        echo "⚠️ Rclone não encontrado. Instale rclone." | tee -a "$LOG_FILE"
    fi
fi

# --- Auditoria local ---
AUDIT_ENTRY="$(date +'%F %T') | user=$(whoami) | host=$(hostname) | file=$(basename "$GPG_FILE") | sha256=$CHECKSUM | size=$(stat -c%s "$GPG_FILE")"
echo "$AUDIT_ENTRY" >> "$AUDIT_LOG"

# --- Upload da auditoria ---
if [ -n "$RCLONE_REMOTE" ] && command -v rclone >/dev/null 2>&1; then
    AUDIT_REMOTE_DIR="${RCLONE_REMOTE}/auditoria"
    AUDIT_REMOTE_FILE="auditoria_$(date +%F).log"
    echo "📤 Enviando auditoria para $AUDIT_REMOTE_DIR/$AUDIT_REMOTE_FILE" | tee -a "$LOG_FILE"
    if rclone mkdir "$AUDIT_REMOTE_DIR" && rclone copyto "$AUDIT_LOG" "$AUDIT_REMOTE_DIR/$AUDIT_REMOTE_FILE" --no-traverse 2>> "$LOG_FILE"; then
        echo "✔️ Auditoria enviada com sucesso" | tee -a "$LOG_FILE"
    else
        echo "⚠️ Falha ao enviar auditoria" | tee -a "$LOG_FILE"
    fi
fi

# --- Retenção local ---
echo "🧹 Iniciando limpeza de backups e logs antigos (>${RETENTION_DAYS} dias)..." | tee -a "$LOG_FILE"

find "$BACKUP_DIR" -type f -name "*.sql*" -mtime +$RETENTION_DAYS | while read -r old_file; do
    log_delete "$old_file"
    rm -f "$old_file"
done

find "$LOG_DIR" -type f -name "*.log" -mtime +$RETENTION_DAYS | while read -r old_log; do
    log_delete "$old_log"
    rm -f "$old_log"
done

# --- Retenção remota (offsite) ---
if [ -n "$RCLONE_REMOTE" ] && command -v rclone >/dev/null 2>&1; then
    echo "🧹 Iniciando limpeza de backups antigos no offsite ($RCLONE_REMOTE)..." | tee -a "$LOG_FILE"

    REMOTE_BACKUP_DIR="${RCLONE_REMOTE}/backups"
    rclone lsf "$REMOTE_BACKUP_DIR" --files-only --format "pt" | while read -r entry; do
        file_date=$(echo "$entry" | awk '{print $1}' | cut -d'T' -f1)
        filename=$(echo "$entry" | awk '{print $3}')
        if [[ $(date -d "$file_date" +%s) -lt $(date -d "-$RETENTION_DAYS days" +%s) ]]; then
            echo "🗑️  Excluindo remoto: $filename (data: $file_date)" | tee -a "$LOG_FILE"
            log_delete "$REMOTE_BACKUP_DIR/$filename"
            rclone deletefile "$REMOTE_BACKUP_DIR/$filename" 2>> "$LOG_FILE" || true
        fi
    done

    REMOTE_AUDIT_DIR="${RCLONE_REMOTE}/auditoria"
    rclone lsf "$REMOTE_AUDIT_DIR" --files-only --format "pt" | while read -r entry; do
        file_date=$(echo "$entry" | awk '{print $1}' | cut -d'T' -f1)
        filename=$(echo "$entry" | awk '{print $3}')
        if [[ $(date -d "$file_date" +%s) -lt $(date -d "-$RETENTION_DAYS days" +%s) ]]; then
            echo "🗑️  Excluindo auditoria remota: $filename (data: $file_date)" | tee -a "$LOG_FILE"
            log_delete "$REMOTE_AUDIT_DIR/$filename"
            rclone deletefile "$REMOTE_AUDIT_DIR/$filename" 2>> "$LOG_FILE" || true
        fi
    done
fi

echo "Backup finalizado em $(date)" | tee -a "$LOG_FILE"
echo "=====================================" | tee -a "$LOG_FILE"
