#!/bin/bash

set -e

echo "=== УНИВЕРСАЛЬНАЯ УСТАНОВКА СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ ==="
echo "📦 Устанавливаю все компоненты системы..."

# Автоматическое определение путей
USER_HOME="$HOME"
APP_NAME="family_system"
APP_DIR="$USER_HOME/.local/share/$APP_NAME"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_APPS_DIR="$USER_HOME/.local/share/applications"

echo "📁 Создаю директорию приложения..."
mkdir -p "$APP_DIR"
mkdir -p "$DESKTOP_APPS_DIR"

# Копируем ВСЕ необходимые файлы
echo "📋 Копирую файлы системы..."
cp -f "$SCRIPT_DIR/json_family_creator.py" "$APP_DIR/" 2>/dev/null || true
cp -f "$SCRIPT_DIR/massform.py" "$APP_DIR/" 2>/dev/null || true
cp -f "$SCRIPT_DIR/database_client.sh" "$APP_DIR/" 2>/dev/null || true
cp -f "$SCRIPT_DIR/config.env" "$APP_DIR/" 2>/dev/null || true
cp -f "$SCRIPT_DIR/family_database_launcher.sh" "$APP_DIR/" 2>/dev/null || true

# Делаем скрипты исполняемыми
chmod +x "$APP_DIR/"*.sh 2>/dev/null || true

echo "✅ Основные файлы скопированы"

# Функция определения среды рабочего стола
detect_desktop_environment() {
    local de=""
    
    # Проверяем переменные среды
    if [ -n "$XDG_CURRENT_DESKTOP" ]; then
        de=$(echo "$XDG_CURRENT_DESKTOP" | tr '[:upper:]' '[:lower:]')
    elif [ -n "$DESKTOP_SESSION" ]; then
        de=$(echo "$DESKTOP_SESSION" | tr '[:upper:]' '[:lower:]')
    fi
    
    # Определяем конкретную среду
    case "$de" in
        *gnome*)
            echo "gnome"
            ;;
        *kde*|*plasma*)
            echo "kde"
            ;;
        *mate*)
            echo "mate"
            ;;
        *xfce*)
            echo "xfce"
            ;;
        *cinnamon*)
            echo "cinnamon"
            ;;
        *lxde*|*lxqt*)
            echo "lxde"
            ;;
        *redos*|*rosa*|*astra*|*alt*)
            echo "russian"
            ;;
        *)
            # Если не определили, пробуем определить по процессам
            if pgrep -l "gnome-session" >/dev/null; then
                echo "gnome"
            elif pgrep -l "plasmashell" >/dev/null; then
                echo "kde"
            elif pgrep -l "mate-session" >/dev/null; then
                echo "mate"
            elif pgrep -l "xfce4-session" >/dev/null; then
                echo "xfce"
            else
                echo "unknown"
            fi
            ;;
    esac
}

# Функция определения пути к рабочему столу
detect_desktop_path() {
    local desktop_path=""
    
    # Пробуем XDG стандарт
    if [ -n "$XDG_DESKTOP_DIR" ]; then
        desktop_path="$XDG_DESKTOP_DIR"
    elif command -v xdg-user-dir >/dev/null 2>&1; then
        desktop_path=$(xdg-user-dir DESKTOP 2>/dev/null)
    fi
    
    # Если XDG не сработал, пробуем стандартные пути
    if [ -z "$desktop_path" ] || [ ! -d "$desktop_path" ]; then
        local possible_paths=(
            "$USER_HOME/Desktop"
            "$USER_HOME/desktop"
            "$USER_HOME/Рабочий стол"
            "$USER_HOME/рабочий стол"
            "$USER_HOME/Стол"
            "$USER_HOME/стол"
        )
        
        for path in "${possible_paths[@]}"; do
            if [ -d "$path" ]; then
                desktop_path="$path"
                break
            fi
        done
    fi
    
    # Если всё ещё не нашли, создаем стандартный Desktop
    if [ -z "$desktop_path" ] || [ ! -d "$desktop_path" ]; then
        desktop_path="$USER_HOME/Desktop"
        mkdir -p "$desktop_path"
    fi
    
    echo "$desktop_path"
}

# Функция определения терминала
detect_terminal() {
    local terminals=(
        "gnome-terminal" "konsole" "mate-terminal" "xfce4-terminal"
        "lxterminal" "terminator" "xterm" "uxterm" "st" "alacritty"
        "kitty" "tilix" "qterminal" "sakura" "roxterm"
    )
    
    for term in "${terminals[@]}"; do
        if command -v "$term" >/dev/null 2>&1; then
            echo "$term"
            return 0
        fi
    done
    
    echo "xterm" # запасной вариант
}

# Функция создания десктоп-файла в ~/.local/share/applications
create_desktop_entry() {
    local desktop_env="$1"
    local terminal="$2"
    
    local desktop_file="$DESKTOP_APPS_DIR/family_system.desktop"
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Система работы с семьями
GenericName=Комплексная система обработки семей
Comment=Запуск всех компонентов системы работы с базами данных семей
Exec=$APP_DIR/family_database_launcher.sh
Icon=system-run
Categories=Utility;Office;Database;
Terminal=true
StartupNotify=true
EOF
    
    # Специфичные настройки для разных сред
    case "$desktop_env" in
        "kde")
            echo "StartupWMClass=family_system" >> "$desktop_file"
            ;;
        "gnome")
            echo "DBusActivatable=true" >> "$desktop_file"
            ;;
    esac
    
    chmod +x "$desktop_file"
    echo "$desktop_file"
}

# Функция создания ярлыка на рабочем столе
create_desktop_shortcut() {
    local desktop_path="$1"
    local desktop_env="$2"
    
    local desktop_file="$desktop_path/Система_работы_с_семьями.desktop"
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Система работы с семьями
Comment=Запуск всех компонентов системы обработки семей
Exec=$APP_DIR/family_database_launcher.sh
Icon=system-run
Terminal=true
Categories=Utility;
EOF
    
    chmod +x "$desktop_file"
    echo "$desktop_file"
}

# Функция создания отдельного ярлыка для JSON создателя
create_json_creator_shortcut() {
    local desktop_path="$1"
    
    local desktop_file="$desktop_path/Создатель_JSON_семей.desktop"
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Создатель JSON (семьи)
Comment=Создание и редактирование JSON файлов с данными семей
Exec=python3 $APP_DIR/json_family_creator.py
Icon=text-x-generic
Terminal=false
Categories=Office;Utility;
EOF
    
    chmod +x "$desktop_file"
    echo "$desktop_file"
}

# Функция создания отдельного ярлыка для массового обработчика
create_mass_processor_shortcut() {
    local desktop_path="$1"
    
    local desktop_file="$desktop_path/Массовый_обработчик_семей.desktop"
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Массовый обработчик семей
Comment=Автоматическое заполнение базы данных семьями
Exec=python3 $APP_DIR/massform.py
Icon=system-run
Terminal=false
Categories=Office;Utility;
EOF
    
    chmod +x "$desktop_file"
    echo "$desktop_file"
}

# Функция создания отдельного ярлыка для базы данных
create_database_shortcut() {
    local desktop_path="$1"
    
    local desktop_file="$desktop_path/База_данных_семей.desktop"
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=База данных семей
Comment=Подключение к корпоративной базе данных семей
Exec=$APP_DIR/database_client.sh
Icon=network-wired
Terminal=true
Categories=Network;Utility;
EOF
    
    chmod +x "$desktop_file"
    echo "$desktop_file"
}

# Функция установки зависимостей
install_dependencies() {
    echo "📦 Проверяю и устанавливаю зависимости..."
    
    # Проверяем Python
    if ! command -v python3 >/dev/null 2>&1; then
        echo "🐍 Устанавливаю Python3..."
        sudo dnf install -y python3 python3-pip || sudo apt install -y python3 python3-pip || {
            echo "❌ Не удалось установить Python3"
            return 1
        }
    fi
    
    # Проверяем pip
    if ! command -v pip3 >/dev/null 2>&1; then
        echo "📦 Устанавливаю pip..."
        sudo dnf install -y python3-pip || sudo apt install -y python3-pip || {
            echo "⚠️ Не удалось установить pip, продолжаю без него"
        }
    fi
    
    # Устанавливаем Python зависимости если есть pip
    if command -v pip3 >/dev/null 2>&1; then
        echo "📚 Устанавливаю Python библиотеки..."
        
        # Создаем временный файл с зависимостями
        cat > /tmp/requirements.txt << 'EOF'
customtkinter>=5.2.0
selenium>=4.15.0
webdriver-manager>=4.0.1
pandas>=2.1.0
openpyxl>=3.1.0
python-dateutil>=2.8.2
EOF
        
        pip3 install --user -r /tmp/requirements.txt || {
            echo "⚠️ Не удалось установить все зависимости через pip"
            echo "Попробуйте установить вручную:"
            echo "  pip3 install customtkinter selenium webdriver-manager pandas openpyxl python-dateutil"
        }
    else
        echo "ℹ️ pip не найден, установите зависимости вручную:"
        echo "  pip3 install customtkinter selenium webdriver-manager pandas openpyxl python-dateutil"
    fi
    
    # Проверяем sshpass
    if ! command -v sshpass >/dev/null 2>&1; then
        echo "🔑 Устанавливаю sshpass..."
        sudo dnf install -y sshpass || sudo apt install -y sshpass || {
            echo "⚠️ Не удалось установить sshpass"
            echo "Для подключения к базе данных потребуется sshpass"
        }
    fi
    
    # Проверяем curl
    if ! command -v curl >/dev/null 2>&1; then
        echo "🌐 Устанавливаю curl..."
        sudo dnf install -y curl || sudo apt install -y curl || {
            echo "⚠️ Не удалось установить curl"
        }
    fi
    
    echo "✅ Зависимости проверены"
}

# Основной процесс установки
echo "🔍 Определяю среду рабочего стола..."
DESKTOP_ENV=$(detect_desktop_environment)
echo "   Среда рабочего стола: $DESKTOP_ENV"

echo "📁 Определяю путь к рабочему столу..."
DESKTOP_PATH=$(detect_desktop_path)
echo "   Путь к рабочему столу: $DESKTOP_PATH"

echo "💻 Определяю терминал..."
TERMINAL=$(detect_terminal)
echo "   Терминал: $TERMINAL"

# Устанавливаем зависимости
install_dependencies

echo "🖱️ Создаю ярлыки..."

# Создаем главный десктоп-файл
MAIN_DESKTOP=$(create_desktop_entry "$DESKTOP_ENV" "$TERMINAL")
echo "   📄 Главный ярлык: $MAIN_DESKTOP"

# Создаем ярлыки на рабочем столе
SHORTCUT_DESKTOP=$(create_desktop_shortcut "$DESKTOP_PATH" "$DESKTOP_ENV")
echo "   🖥️  Ярлык на рабочем столе: $SHORTCUT_DESKTOP"

# Создаем отдельные ярлыки для каждого компонента
JSON_SHORTCUT=$(create_json_creator_shortcut "$DESKTOP_PATH")
echo "   📝 Ярлык Создателя JSON: $JSON_SHORTCUT"

MASS_SHORTCUT=$(create_mass_processor_shortcut "$DESKTOP_PATH")
echo "   ⚙️  Ярлык Массового обработчика: $MASS_SHORTCUT"

DB_SHORTCUT=$(create_database_shortcut "$DESKTOP_PATH")
echo "   🗄️  Ярлык Базы данных: $DB_SHORTCUT"

# Создаем конфигурационный файл если его нет
if [ ! -f "$APP_DIR/config.env" ]; then
    echo "⚙️ Создаю файл конфигурации..."
    cat > "$APP_DIR/config.env" << 'EOF'
# Конфигурация подключения к базе данных
# ЗАПОЛНИТЕ ЭТИ НАСТРОЙКИ ПЕРЕД ЗАПУСКОМ

SSH_HOST="192.168.10.59"
SSH_USER="sshuser"
SSH_PASSWORD="orsd321"
LOCAL_PORT="8080"
REMOTE_HOST="172.30.1.18"
REMOTE_PORT="80"
WEB_PATH="/aspnetkp/common/FindInfo.aspx"
EOF
    echo "   📄 Конфигурационный файл создан: $APP_DIR/config.env"
fi

# Создаем скрипт обновления
cat > "$APP_DIR/update_system.sh" << 'EOF'
#!/bin/bash
echo "🔄 Обновление системы работы с семьями..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SCRIPT="$(dirname "$SCRIPT_DIR")/install_family_system.sh"
if [ -f "$INSTALL_SCRIPT" ]; then
    bash "$INSTALL_SCRIPT"
else
    echo "❌ Скрипт установки не найден"
fi
EOF
chmod +x "$APP_DIR/update_system.sh"

# Создаем скрипт удаления
cat > "$APP_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
echo "🗑️ Удаление системы работы с семьями..."
read -p "Вы уверены, что хотите удалить систему? (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    rm -rf ~/.local/share/family_system
    rm -f ~/.local/share/applications/family_system.desktop
    rm -f ~/Desktop/Система_работы_с_семьями.desktop 2>/dev/null
    rm -f ~/Рабочий\ стол/Система_работы_с_семьями.desktop 2>/dev/null
    rm -f ~/Desktop/Создатель_JSON_семей.desktop 2>/dev/null
    rm -f ~/Рабочий\ стол/Создатель_JSON_семей.desktop 2>/dev/null
    rm -f ~/Desktop/Массовый_обработчик_семей.desktop 2>/dev/null
    rm -f ~/Рабочий\ стол/Массовый_обработчик_семей.desktop 2>/dev/null
    rm -f ~/Desktop/База_данных_семей.desktop 2>/dev/null
    rm -f ~/Рабочий\ стол/База_данных_семей.desktop 2>/dev/null
    echo "✅ Система удалена"
else
    echo "❌ Удаление отменено"
fi
EOF
chmod +x "$APP_DIR/uninstall.sh"

echo "✅ Установка завершена!"
echo ""
echo "========================================="
echo "         СИСТЕМА УСПЕШНО УСТАНОВЛЕНА"
echo "========================================="
echo ""
echo "📊 ОТЧЕТ ОБ УСТАНОВКЕ:"
echo "   📁 Приложение: $APP_DIR"
echo "   🖥️  Среда: $DESKTOP_ENV"
echo "   📂 Рабочий стол: $DESKTOP_PATH"
echo ""
echo "🖱️ СОЗДАННЫЕ ЯРЛЫКИ:"
echo "   1. Система работы с семьями (лаунчер)"
echo "   2. Создатель JSON семей"
echo "   3. Массовый обработчик семей"
echo "   4. База данных семей"
echo ""
echo "🚀 ИСПОЛЬЗОВАНИЕ:"
echo "   • Дважды щелкните любой ярлык на рабочем столе"
echo "   • Или запустите: $APP_DIR/family_database_launcher.sh"
echo ""
echo "🔧 УПРАВЛЕНИЕ:"
echo "   • Обновить систему: $APP_DIR/update_system.sh"
echo "   • Удалить систему: $APP_DIR/uninstall.sh"
echo ""
echo "⚠️  ВНИМАНИЕ:"
echo "   1. Отредактируйте config.env: nano $APP_DIR/config.env"
echo "   2. Заполните настройки подключения к базе данных"
echo ""
echo "Нажмите Enter для завершения..."
read