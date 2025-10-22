#!/bin/bash
# =====================================
# Restauração de Backup Interativa - Nodesk (Produção)
# =====================================

# --- Caminho absoluto do script ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Carrega variáveis do .env ---
ENV_FILE="$SCRIPT_DIR/../../.env"
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# --- Diretórios e logs ---
BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/backups/full}"
LOG_DIR="${LOG_DIR:-$SCRIPT_DIR/logs}"
mkdir -p "$BACKUP_DIR" "$LOG_DIR"
TIMESTAMP=$(date +%F_%H-%M-%S)
LOG_FILE="$LOG_DIR/restore_final_$TIMESTAMP.log"

# --- Lista backups disponíveis ---
echo "📂 Backups disponíveis em: $BACKUP_DIR"
mapfile -t BACKUPS < <(ls -1 "$BACKUP_DIR"/*.gpg 2>/dev/null)
if [ ${#BACKUPS[@]} -eq 0 ]; then
    echo "❌ Nenhum backup encontrado em $BACKUP_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

for i in "${!BACKUPS[@]}"; do
    echo "[$i] ${BACKUPS[$i]}"
done

# --- Escolha do backup ---
read -p "Escolha o backup a restaurar (digite o número): " IDX
if ! [[ "$IDX" =~ ^[0-9]+$ ]] || [ "$IDX" -ge "${#BACKUPS[@]}" ]; then
    echo "❌ Opção inválida" | tee -a "$LOG_FILE"
    exit 1
fi
BACKUP_FILE="${BACKUPS[$IDX]}"

# --- Usuário PostgreSQL ---
read -p "Digite o usuário PostgreSQL que fará a restauração: " DB_USER

# --- Senha GPG ---
read -s -p "Digite a senha de descriptografia GPG: " GPG_PASSPHRASE
echo

# --- Senha PostgreSQL ---
read -s -p "Digite a senha do usuário PostgreSQL '$DB_USER': " PGPASSWORD
export PGPASSWORD
echo

# --- Log inicial ---
echo "=====================================" | tee -a "$LOG_FILE"
echo "Início da restauração: $(date)" | tee -a "$LOG_FILE"
echo "Usuário PostgreSQL: $DB_USER" | tee -a "$LOG_FILE"
echo "Usuário SO: $(whoami)" | tee -a "$LOG_FILE"
echo "Backup selecionado: $BACKUP_FILE" | tee -a "$LOG_FILE"
echo "=====================================" | tee -a "$LOG_FILE"

# --- Restaurando diretamente da memória ---
DB_HOST="127.0.0.1"
DB_PORT="${DB_PORT:-5432}"

echo "🔐 Descriptografando e restaurando o backup..." | tee -a "$LOG_FILE"
set +e
gpg --batch --yes --passphrase "$GPG_PASSPHRASE" -d "$BACKUP_FILE" | \
psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -p "$DB_PORT" &>> "$LOG_FILE"
EXIT_CODE=$?
set -e

# --- Limpeza de variáveis sensíveis ---
unset PGPASSWORD
unset GPG_PASSPHRASE

# --- Resultado ---
echo "=====================================" | tee -a "$LOG_FILE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Restauração concluída com sucesso!" | tee -a "$LOG_FILE"
else
    echo "❌ Falha na restauração do banco!" | tee -a "$LOG_FILE"
    echo "Veja detalhes no log acima." | tee -a "$LOG_FILE"
fi
echo "Fim da operação: $(date)" | tee -a "$LOG_FILE"
echo "📜 Log salvo em: $LOG_FILE"
echo "====================================="
