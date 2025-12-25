#!/bin/bash

# ============================================
# ЕДИНЫЙ ЗАПУСКАЮЩИЙ СКРИПТ ДЛЯ СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ
# ============================================

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Лог файл
LOG_FILE="$(dirname "$0")/system_launch.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Запуск системы" > "$LOG_FILE"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║          СИСТЕМА РАБОТЫ С СЕМЬЯМИ - ВСЕ В ОДНОМ         ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_menu() {
    echo -e "${CYAN}"
    echo "Выберите действие:"
    echo -e "${GREEN}1)${NC} 📝 Создатель JSON (редактирование семей)"
    echo -e "${GREEN}2)${NC} ⚙️  Массовый обработчик (заполнение базы)"
    echo -e "${GREEN}3)${NC} 🗄️  База данных (подключение)"
    echo -e "${GREEN}4)${NC} 🚀 Запустить ВСЁ (полный цикл)"
    echo -e "${GREEN}5)${NC} 🛑 Остановить все процессы"
    echo -e "${GREEN}6)${NC} 📊 Показать статус процессов"
    echo -e "${GREEN}7)${NC} 🔧 Настройки и управление"
    echo -e "${GREEN}8)${NC} 📦 УСТАНОВИТЬ/ОБНОВИТЬ систему"
    echo -e "${GREEN}9)${NC} ❌ Выход"
    echo -e "${CYAN}"
    echo -n "Ваш выбор [1-9]: "
    echo -e "${NC}"
}

# Функция меню управления
print_management_menu() {
    echo -e "${CYAN}"
    echo "Управление системой:"
    echo -e "${GREEN}1)${NC} 📋 Проверить зависимости"
    echo -e "${GREEN}2)${NC} ⚙️  Открыть конфигурацию"
    echo -e "${GREEN}3)${NC} 🔄 Обновить систему"
    echo -e "${GREEN}4)${NC} 🗑️  Удалить систему"
    echo -e "${GREEN}5)${NC} 📁 Открыть папку приложения"
    echo -e "${GREEN}6)${NC} ↩️  Назад в главное меню"
    echo -e "${CYAN}"
    echo -n "Ваш выбор [1-6]: "
    echo -e "${NC}"
}

# Функция установки системы
install_system() {
    echo -e "${BLUE}📦 Запуск установки системы...${NC}"
    
    local script_dir=$(get_script_dir)
    local install_script="$script_dir/install_family_system.sh"
    
    if [ -f "$install_script" ]; then
        echo -e "${GREEN}✅ Найден скрипт установки${NC}"
        chmod +x "$install_script"
        echo -e "${YELLOW}⚠️  Для установки требуются права администратора${NC}"
        echo -e "${CYAN}Продолжить установку? (y/N): ${NC}"
        read confirm
        
        if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
            bash "$install_script"
        else
            echo -e "${YELLOW}❌ Установка отменена${NC}"
        fi
    else
        echo -e "${RED}❌ Скрипт установки не найден${NC}"
        echo "Создайте файл install_family_system.sh или скачайте полную версию системы"
    fi
}

# Функция проверки установки
check_installation() {
    local app_dir="$HOME/.local/share/family_system"
    
    if [ ! -d "$app_dir" ]; then
        echo -e "${YELLOW}⚠️  Система не установлена!${NC}"
        echo -e "${CYAN}Хотите установить систему сейчас? (y/N): ${NC}"
        read confirm
        
        if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
            install_system
            return 1
        else
            echo -e "${YELLOW}⚠️  Работа без установки - некоторые функции могут быть недоступны${NC}"
            return 0
        fi
    fi
    
    return 0
}

# Остальные функции остаются такими же, как в предыдущей версии
# [get_script_dir, check_process, start_json_creator, start_mass_processor, 
# start_database, stop_all_processes, show_status, check_dependencies, 
# open_configuration, update_system, uninstall_system, open_app_folder]

get_script_dir() {
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
}

# ... остальные функции без изменений ...

check_dependencies() {
    echo -e "${CYAN}📋 Проверка зависимостей:${NC}"
    echo ""
    
    # Проверяем Python
    if command -v python3 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Python3: установлен"
    else
        echo -e "  ${RED}✗${NC} Python3: не установлен"
    fi
    
    # Проверяем pip
    if command -v pip3 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} pip3: установлен"
    else
        echo -e "  ${RED}✗${NC} pip3: не установлен"
    fi
    
    # Проверяем sshpass
    if command -v sshpass >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} sshpass: установлен"
    else
        echo -e "  ${RED}✗${NC} sshpass: не установлен"
    fi
    
    # Проверяем curl
    if command -v curl >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} curl: установлен"
    else
        echo -e "  ${RED}✗${NC} curl: не установлен"
    fi
    
    echo ""
    echo -e "${CYAN}📚 Проверка Python библиотек:${NC}"
    
    local libs=("customtkinter" "selenium" "webdriver_manager" "pandas" "openpyxl" "dateutil")
    for lib in "${libs[@]}"; do
        if python3 -c "import $lib" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} $lib: установлена"
        else
            echo -e "  ${RED}✗${NC} $lib: не установлена"
        fi
    done
}

open_configuration() {
    local app_dir="$HOME/.local/share/family_system"
    local config_file="$app_dir/config.env"
    
    if [ -f "$config_file" ]; then
        echo -e "${CYAN}⚙️  Открываю конфигурационный файл...${NC}"
        
        # Пробуем разные редакторы
        if command -v nano >/dev/null 2>&1; then
            nano "$config_file"
        elif command -v vim >/dev/null 2>&1; then
            vim "$config_file"
        elif command -v vi >/dev/null 2>&1; then
            vi "$config_file"
        else
            echo -e "${YELLOW}⚠️  Текстовый редактор не найден${NC}"
            echo "Содержимое config.env:"
            cat "$config_file"
        fi
    else
        echo -e "${RED}❌ Конфигурационный файл не найден${NC}"
        echo "Создайте его вручную или запустите установку системы"
    fi
}

update_system() {
    local app_dir="$HOME/.local/share/family_system"
    local update_script="$app_dir/update_system.sh"
    
    if [ -f "$update_script" ]; then
        echo -e "${BLUE}🔄 Запуск обновления системы...${NC}"
        bash "$update_script"
    else
        echo -e "${RED}❌ Скрипт обновления не найден${NC}"
        echo "Попробуйте переустановить систему"
    fi
}

uninstall_system() {
    local app_dir="$HOME/.local/share/family_system"
    local uninstall_script="$app_dir/uninstall.sh"
    
    if [ -f "$uninstall_script" ]; then
        echo -e "${RED}🗑️  Запуск удаления системы...${NC}"
        bash "$uninstall_script"
    else
        echo -e "${YELLOW}⚠️  Скрипт удаления не найден${NC}"
        echo "Удалите вручную папку: $app_dir"
    fi
}

open_app_folder() {
    local app_dir="$HOME/.local/share/family_system"
    
    if [ -d "$app_dir" ]; then
        echo -e "${CYAN}📁 Открываю папку приложения...${NC}"
        
        # Пробуем разные файловые менеджеры
        if command -v nautilus >/dev/null 2>&1; then
            nautilus "$app_dir" &
        elif command -v dolphin >/dev/null 2>&1; then
            dolphin "$app_dir" &
        elif command -v thunar >/dev/null 2>&1; then
            thunar "$app_dir" &
        elif command -v pcmanfm >/dev/null 2>&1; then
            pcmanfm "$app_dir" &
        else
            echo -e "${YELLOW}⚠️  Файловый менеджер не найден${NC}"
            echo "Папка приложения: $app_dir"
        fi
    else
        echo -e "${RED}❌ Папка приложения не найдена${NC}"
        echo "Сначала установите систему"
    fi
}

# Основной цикл с обновленным меню
main() {
    # Проверяем установку
    check_installation
    
    while true; do
        clear
        print_header
        print_menu
        
        read choice
        
        case $choice in
            1)
                start_json_creator
                read -p "Нажмите Enter для продолжения..."
                ;;
            2)
                start_mass_processor
                read -p "Нажмите Enter для продолжения..."
                ;;
            3)
                start_database
                read -p "Нажмите Enter для продолжения..."
                ;;
            4)
                echo -e "${PURPLE}🚀 Запускаю ВСЕ компоненты системы...${NC}"
                start_database
                sleep 3
                start_json_creator
                sleep 2
                start_mass_processor
                echo -e "${GREEN}✨ Все компоненты запущены!${NC}"
                read -p "Нажмите Enter для продолжения..."
                ;;
            5)
                stop_all_processes
                read -p "Нажмите Enter для продолжения..."
                ;;
            6)
                show_status
                read -p "Нажмите Enter для продолжения..."
                ;;
            7)
                # Меню управления
                while true; do
                    clear
                    echo -e "${PURPLE}"
                    echo "╔══════════════════════════════════════╗"
                    echo "║         УПРАВЛЕНИЕ СИСТЕМОЙ         ║"
                    echo "╚══════════════════════════════════════╝"
                    echo -e "${NC}"
                    print_management_menu
                    
                    read mgmt_choice
                    
                    case $mgmt_choice in
                        1)
                            check_dependencies
                            read -p "Нажмите Enter для продолжения..."
                            ;;
                        2)
                            open_configuration
                            ;;
                        3)
                            update_system
                            read -p "Нажмите Enter для продолжения..."
                            ;;
                        4)
                            uninstall_system
                            read -p "Нажмите Enter для продолжения..."
                            break
                            ;;
                        5)
                            open_app_folder
                            read -p "Нажмите Enter для продолжения..."
                            ;;
                        6)
                            break
                            ;;
                        *)
                            echo -e "${RED}❌ Неверный выбор${NC}"
                            sleep 1
                            ;;
                    esac
                done
                ;;
            8)
                install_system
                read -p "Нажмите Enter для продолжения..."
                ;;
            9)
                echo -e "${YELLOW}👋 Выход из программы${NC}"
                log "Завершение работы системы"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Неверный выбор. Попробуйте снова.${NC}"
                sleep 1
                ;;
        esac
    done
}

# Проверяем, что мы в bash
if [ -n "$BASH_VERSION" ]; then
    # Запускаем главную функцию
    main
else
    echo -e "${RED}❌ Этот скрипт должен запускаться в bash${NC}"
    echo "Запустите: bash $0"
    exit 1
fi