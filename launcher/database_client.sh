#!/bin/bash

# Универсальный клиент для всех сред
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.env"
LOG_FILE="$SCRIPT_DIR/connection.log"

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Автоматическое определение рабочей директории
cd "$SCRIPT_DIR"

# Проверка конфигурации
if [ ! -f "$CONFIG_FILE" ]; then
    log "❌ Файл конфигурации не найден: $CONFIG_FILE"
    echo "Создайте config.env со следующим содержимым:"
    cat << 'EOF'
SSH_HOST="192.168.10.59"
SSH_USER="sshuser"  
SSH_PASSWORD="orsd321"
LOCAL_PORT="8080"
REMOTE_HOST="172.30.1.18"
REMOTE_PORT="80"
WEB_PATH="/aspnetkp/common/FindInfo.aspx"
EOF
    exit 1
fi

source "$CONFIG_FILE"

# Проверка пароля
if [ -z "$SSH_PASSWORD" ] || [ "$SSH_PASSWORD" = "ваш_пароль" ]; then
    log "❌ Пароль не установлен в config.env"
    exit 1
fi

# Установка sshpass если нужно
if ! command -v sshpass >/dev/null 2>&1; then
    log "📦 Устанавливаю sshpass..."
    sudo dnf install -y sshpass || {
        log "❌ Не удалось установить sshpass"
        exit 1
    }
fi

# Остановка старых туннелей
pkill -f "ssh.*${LOCAL_PORT}:.*${REMOTE_HOST}:${REMOTE_PORT}" 2>/dev/null && sleep 2

log "🚀 Запускаю подключение к базе данных..."
sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 \
    -N -L "${LOCAL_PORT}:${REMOTE_HOST}:${REMOTE_PORT}" "${SSH_USER}@${SSH_HOST}" &
TUNNEL_PID=$!

sleep 5

if ! kill -0 $TUNNEL_PID 2>/dev/null; then
    log "❌ Не удалось запустить туннель"
    exit 1
fi

log "✅ Туннель запущен (PID: $TUNNEL_PID)"

# Универсальное открытие браузера
log "🌐 Открываю браузер..."
for browser in xdg-open firefox chromium google-chrome; do
    if command -v "$browser" >/dev/null 2>&1; then
        $browser "http://localhost:${LOCAL_PORT}${WEB_PATH}" 2>/dev/null &
        break
    fi
done

echo ""
echo "=== КЛИЕНТ БАЗЫ ДАННЫХ ЗАПУЩЕН ==="
echo "🌐 Адрес: http://localhost:${LOCAL_PORT}${WEB_PATH}"
echo "📡 PID: $TUNNEL_PID"
echo "📋 Лог: $LOG_FILE"
echo ""
echo "Нажмите Enter для остановки..."
read

kill $TUNNEL_PID 2>/dev/null
log "🛑 Туннель остановлен"