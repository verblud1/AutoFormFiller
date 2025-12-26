#!/bin/bash

# Универсальный установщик для Linux/RedOS
# Поддерживает Red OS и другие Linux-дистрибутивы

set -e  # Прерывать выполнение при ошибках

# Функция логирования
log() {
    echo "[$(date '+%H:%M:%S')] [INFO] $1"
}

log_error() {
    echo "[$(date '+%H:%M:%S')] [ERROR] $1" >&2
}

log_success() {
    echo "[$(date '+%H:%M:%S')] [SUCCESS] $1"
}

# Определение директории скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER_DIR="$(dirname "$SCRIPT_DIR")/Installer"

# Проверка Python
check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python3 не найден"
        exit 1
    fi
    
    # Проверка версии Python
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    if [ $? -ne 0 ]; then
        log_error "Ошибка проверки версии Python"
        exit 1
    fi
    
    # Проверка, что версия >= 3.6
    if [ "$(printf '%s\n' "3.6" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.6" ]; then
        log_error "Требуется Python 3.6+, у вас $PYTHON_VERSION"
        exit 1
    fi
    
    log "Python $PYTHON_VERSION найден"
}

# Установка зависимостей
install_dependencies() {
    log "Установка зависимостей..."
    
    # Определение дистрибутива
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$NAME
    else
        DISTRO="Unknown"
    fi
    
    log "Дистрибутив: $DISTRO"
    
    # Установка пакетов в зависимости от дистрибутива
    if [[ "$DISTRO" == *"RedOS"* ]] || [[ "$DISTRO" == *"Astra"* ]] || [[ "$DISTRO" == *"Alt"* ]]; then
        # Для RedOS и подобных
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update
            sudo apt-get install -y python3-pip python3-tk
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y python3-pip python3-tkinter
        elif command -v yum >/dev/null 2>&1; then
            sudo yum install -y python3-pip python3-tkinter
        fi
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y python3-pip python3-tk
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3-pip python3-tkinter
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3-pip python3-tkinter
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y python3-pip python3-tk
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm python-pip tk
    fi
    
    # Установка Python-пакетов
    python3 -m pip install --user selenium==3.141.0 webdriver-manager==3.8.0
    log_success "Зависимости установлены"
}

# Создание структуры папок и копирование файлов
install_system() {
    log "Начало установки системы..."
    
    # Определение пути установки
    DESKTOP_DIR="$HOME/Рабочий стол"
    if [ ! -d "$DESKTOP_DIR" ]; then
        DESKTOP_DIR="$HOME/Desktop"
        if [ ! -d "$DESKTOP_DIR" ]; then
            DESKTOP_DIR="$HOME"
        fi
    fi
    
    INSTALL_DIR="$DESKTOP_DIR/FamilySystem"
    log "Установка в: $INSTALL_DIR"
    
    # Создание папки установки
    mkdir -p "$INSTALL_DIR"
    
    # Создание подпапок
    mkdir -p "$INSTALL_DIR/config"
    mkdir -p "$INSTALL_DIR/config/logs"
    mkdir -p "$INSTALL_DIR/config/screenshots"
    
    # Копирование файлов из установщика
    cp -f "$INSTALLER_DIR/json_family_creator.py" "$INSTALL_DIR/" 2>/dev/null || log_error "Не удалось скопировать json_family_creator.py"
    cp -f "$INSTALLER_DIR/massform.py" "$INSTALL_DIR/" 2>/dev/null || log_error "Не удалось скопировать massform.py"
    cp -f "$INSTALLER_DIR/family_system_launcher.py" "$INSTALL_DIR/" 2>/dev/null || log_error "Не удалось скопировать family_system_launcher.py"
    cp -f "$INSTALLER_DIR/chrome_driver_helper.py" "$INSTALL_DIR/" 2>/dev/null || log_error "Не удалось скопировать chrome_driver_helper.py"
    cp -f "$INSTALLER_DIR/database_client.sh" "$INSTALL_DIR/" 2>/dev/null || log_error "Не удалось скопировать database_client.sh"
    cp -f "$INSTALLER_DIR/autosave_families.json" "$INSTALL_DIR/" 2>/dev/null || log "Файл автосохранения не найден - пропущен"
    
    # Копирование папки registry если она существует
    if [ -d "$INSTALLER_DIR/registry" ]; then
        cp -r "$INSTALLER_DIR/registry" "$INSTALL_DIR/" 2>/dev/null
        if [ $? -eq 0 ]; then
            log_success "Скопирована папка registry"
        else
            log_error "Ошибка копирования папки registry"
        fi
    else
        log "Папка registry не найдена - пропущена"
    fi
    
    # Создание конфигурационного файла
    if [ ! -f "$INSTALL_DIR/config.env" ]; then
        cat > "$INSTALL_DIR/config.env" << 'EOF'
# Конфигурация подключения к базе данных
SSH_HOST="192.168.10.59"
SSH_USER="sshuser"
SSH_PASSWORD="orsd321"
LOCAL_PORT="8080"
REMOTE_HOST="172.30.1.18"
REMOTE_PORT="80"
WEB_PATH="/aspnetkp/common/FindInfo.aspx"
EOF
        log_success "Создан конфигурационный файл"
    fi
    
    # Делаем скрипт исполняемым
    chmod +x "$INSTALL_DIR/database_client.sh"
    
    # Создание .desktop файла
    DESKTOP_FILE="$DESKTOP_DIR/family_system.desktop"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Система работы с семьями
Comment=Запуск всех компонентов системы обработки семей
Exec=python3 $INSTALL_DIR/family_system_launcher.py
Path=$INSTALL_DIR
Icon=system-run
Terminal=false
Categories=Utility;Office;
StartupNotify=true
EOF
    
    chmod +x "$DESKTOP_FILE"
    
    log_success "Система установлена в $INSTALL_DIR"
    log_success "Ярлык создан на рабочем столе"
}

# Основная функция
main() {
    log "=== УСТАНОВКА СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ ==="
    log "Для Red OS и Linux-дистрибутивов"
    
    check_python
    install_dependencies
    install_system
    
    log_success "=== УСТАНОВКА ЗАВЕРШЕНА ==="
    log "Система установлена. Запустите через ярлык на рабочем столе."
}

# Запуск основной функции
main "$@"