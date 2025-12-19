#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УНИВЕРСАЛЬНЫЙ УСТАНОВЩИК СИСТЕМЫ
Запустите этот файл для установки системы на любую ОС
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from datetime import datetime

def print_colored(text, color_code):
    """Печатает цветной текст (для терминала)"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    
    color = colors.get(color_code, colors['white'])
    print(f"{color}{text}{colors['reset']}")

def get_desktop_path():
    """Определяет путь к рабочему столу"""
    home_dir = os.path.expanduser("~")
    system = platform.system()
    
    if system == "Windows":
        return os.path.join(home_dir, "Desktop")
    
    # Для Linux/RedOS
    possible_paths = [
        os.path.join(home_dir, "Рабочий стол"),
        os.path.join(home_dir, "Desktop"),
        os.path.join(home_dir, "desktop"),
        os.path.join(home_dir, "Стол")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Если ничего не найдено, создаем Desktop
    desktop = os.path.join(home_dir, "Desktop")
    os.makedirs(desktop, exist_ok=True)
    return desktop

def check_dependencies():
    """Проверяет и устанавливает зависимости"""
    print_colored("\n🔍 Проверка зависимостей...", "cyan")
    
    system = platform.system()
    python_version = sys.version_info
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print_colored("❌ Требуется Python 3.7 или выше", "red")
        return False
    
    print_colored(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}", "green")
    
    # Проверяем необходимые библиотеки
    try:
        import customtkinter
        print_colored("✅ customtkinter установлена", "green")
    except ImportError:
        print_colored("❌ customtkinter не установлена", "red")
        print_colored("Установите: pip install customtkinter", "yellow")
        return False
    
    try:
        import tkinter
        print_colored("✅ tkinter установлена", "green")
    except ImportError:
        print_colored("❌ tkinter не установлена", "red")
        if system == "Linux" or system == "RedOS":
            print_colored("Установите: sudo dnf install python3-tkinter", "yellow")
        elif system == "Windows":
            print_colored("Переустановите Python с опцией 'tcl/tk and IDLE'", "yellow")
        return False
    
    try:
        import selenium
        print_colored("✅ selenium установлена", "green")
    except ImportError:
        print_colored("⚠️  selenium не установлена (требуется для массового обработчика)", "yellow")
    
    try:
        import pandas
        print_colored("✅ pandas установлена", "green")
    except ImportError:
        print_colored("⚠️  pandas не установлена (требуется для работы с Excel)", "yellow")
    
    return True

def install_system():
    """Устанавливает систему на рабочий стол"""
    print_colored("\n" + "="*60, "purple")
    print_colored("    УСТАНОВКА СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ", "purple")
    print_colored("="*60, "purple")
    
    # Определяем ОС
    system = platform.system()
    os_name = "RedOS/Linux" if system in ["Linux", "RedOS"] else system
    print_colored(f"📱 Операционная система: {os_name} ({platform.release()})", "cyan")
    
    # Проверяем зависимости
    if not check_dependencies():
        response = input("\n⚠️  Некоторые зависимости отсутствуют. Продолжить установку? (y/N): ")
        if response.lower() not in ['y', 'yes', 'д', 'да']:
            print_colored("❌ Установка отменена", "red")
            return
    
    # Определяем путь к рабочему столу
    desktop_path = get_desktop_path()
    system_dir = os.path.join(desktop_path, "FamilySystem")
    
    print_colored(f"📁 Путь установки: {system_dir}", "cyan")
    
    # Проверяем, существует ли уже система
    if os.path.exists(system_dir):
        print_colored("\n⚠️  Система уже установлена!", "yellow")
        response = input("Переустановить? (y/N): ")
        if response.lower() not in ['y', 'yes', 'д', 'да']:
            print_colored("❌ Установка отменена", "red")
            return
        
        # Создаем резервную копию конфига
        config_file = os.path.join(system_dir, "config.env")
        backup_file = os.path.join(system_dir, "config.env.backup")
        if os.path.exists(config_file):
            shutil.copy2(config_file, backup_file)
            print_colored("📋 Создана резервная копия конфигурации", "green")
    
    # Создаем папку системы
    os.makedirs(system_dir, exist_ok=True)
    print_colored(f"✅ Создана папка: {system_dir}", "green")
    
    # Определяем путь к файлам установщика
    installer_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Список файлов для копирования
    files_to_copy = [
        "json_family_creator.py",
        "massform.py", 
        "database_client.sh",
        "family_system_launcher.py",
        "install_system.py"  # Этот файл
    ]
    
    # Копируем файлы
    copied_files = 0
    print_colored("\n📦 Копирую файлы системы...", "cyan")
    
    for filename in files_to_copy:
        src_path = os.path.join(installer_dir, filename)
        dst_path = os.path.join(system_dir, filename)
        
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, dst_path)
                copied_files += 1
                print_colored(f"  📄 {filename}", "green")
            except Exception as e:
                print_colored(f"  ❌ {filename}: {e}", "red")
        else:
            print_colored(f"  ⚠️  {filename}: не найден", "yellow")
    
    # Создаем конфигурационный файл
    config_file = os.path.join(system_dir, "config.env")
    if not os.path.exists(config_file):
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("""# Конфигурация подключения к базе данных
# ЗАПОЛНИТЕ ЭТИ НАСТРОЙКИ ПЕРЕД ЗАПУСКОМ

SSH_HOST="192.168.10.59"
SSH_USER="sshuser"
SSH_PASSWORD="orsd321"
LOCAL_PORT="8080"
REMOTE_HOST="172.30.1.18"
REMOTE_PORT="80"
WEB_PATH="/aspnetkp/common/FindInfo.aspx"
""")
        print_colored("⚙️  Создан конфигурационный файл config.env", "green")
    
    # Делаем скрипты исполняемыми (для Linux/RedOS)
    if system in ["Linux", "RedOS"]:
        for script in ["database_client.sh"]:
            script_path = os.path.join(system_dir, script)
            if os.path.exists(script_path):
                os.chmod(script_path, 0o755)
                print_colored(f"🔧 Исполняемый: {script}", "green")
    
    # Создаем ярлыки
    print_colored("\n🖱️ Создаю ярлыки...", "cyan")
    
    if system == "Windows":
        create_windows_shortcut(system_dir)
    elif system in ["Linux", "RedOS"]:
        create_linux_desktop_file(system_dir, desktop_path)
    
    # Создаем файл информации
    info_file = os.path.join(system_dir, "README.txt")
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"""СИСТЕМА РАБОТЫ С СЕМЬЯМИ
Установлена: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
Путь: {system_dir}
ОС: {platform.system()} {platform.release()}

ДЛЯ ЗАПУСКА:
1. Запустите файл "family_system_launcher.py"
2. Или используйте ярлык на рабочем столе

КОМПОНЕНТЫ СИСТЕМЫ:
1. 📝 Создатель JSON - редактирование данных семей
2. ⚙️ Массовый обработчик - автоматическое заполнение базы
3. 🗄️ База данных - подключение к корпоративной БД

НАСТРОЙКА:
Отредактируйте файл config.env для подключения к базе данных
""")
    
    print_colored(f"\n✅ Установка завершена!", "green")
    print_colored(f"📁 Папка системы: {system_dir}", "cyan")
    print_colored(f"📋 Скопировано файлов: {copied_files}", "cyan")
    
    # Запускаем лаунчер
    print_colored("\n🚀 Запускаю лаунчер системы...", "cyan")
    launcher_path = os.path.join(system_dir, "family_system_launcher.py")
    
    try:
        if system == "Windows":
            subprocess.Popen([sys.executable, launcher_path])
        else:
            subprocess.Popen(["python3", launcher_path])
        print_colored("✅ Лаунчер запущен!", "green")
    except Exception as e:
        print_colored(f"⚠️  Не удалось запустить лаунчер: {e}", "yellow")
        print_colored(f"Запустите вручную: python3 {launcher_path}", "cyan")
    
    input("\nНажмите Enter для завершения...")

def create_windows_shortcut(system_dir):
    """Создает ярлык на рабочем столе Windows"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "Система работы с семьями.lnk")
        
        target = sys.executable
        arguments = os.path.join(system_dir, "family_system_launcher.py")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.Arguments = f'"{arguments}"'
        shortcut.WorkingDirectory = system_dir
        shortcut.IconLocation = target
        shortcut.save()
        
        print_colored("✅ Создан ярлык на рабочем столе Windows", "green")
        return True
        
    except Exception as e:
        print_colored(f"⚠️  Не удалось создать ярлык Windows: {e}", "yellow")
        return False

def create_linux_desktop_file(system_dir, desktop_path):
    """Создает .desktop файл для Linux/RedOS"""
    try:
        desktop_file = os.path.join(desktop_path, "family_system.desktop")
        
        with open(desktop_file, 'w', encoding='utf-8') as f:
            f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Система работы с семьями
Comment=Запуск всех компонентов системы обработки семей
Exec=python3 {os.path.join(system_dir, 'family_system_launcher.py')}
Path={system_dir}
Icon=system-run
Terminal=false
Categories=Utility;Office;
StartupNotify=true
""")
        
        os.chmod(desktop_file, 0o755)
        print_colored("✅ Создан .desktop файл на рабочем столе", "green")
        return True
        
    except Exception as e:
        print_colored(f"⚠️  Не удалось создать .desktop файл: {e}", "yellow")
        return False

def uninstall_system():
    """Удаляет систему"""
    print_colored("\n" + "="*60, "red")
    print_colored("    УДАЛЕНИЕ СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ", "red")
    print_colored("="*60, "red")
    
    desktop_path = get_desktop_path()
    system_dir = os.path.join(desktop_path, "FamilySystem")
    
    if not os.path.exists(system_dir):
        print_colored("❌ Система не установлена!", "red")
        return
    
    print_colored(f"📁 Папка для удаления: {system_dir}", "cyan")
    
    response = input("\n❌ Вы уверены, что хотите удалить систему? (y/N): ")
    if response.lower() not in ['y', 'yes', 'д', 'да']:
        print_colored("❌ Удаление отменено", "yellow")
        return
    
    try:
        # Удаляем папку системы
        shutil.rmtree(system_dir)
        print_colored("✅ Папка системы удалена", "green")
        
        # Удаляем ярлыки
        if platform.system() == "Windows":
            try:
                import winshell
                desktop = winshell.desktop()
                shortcut = os.path.join(desktop, "Система работы с семьями.lnk")
                if os.path.exists(shortcut):
                    os.remove(shortcut)
                    print_colored("✅ Ярлык Windows удален", "green")
            except:
                pass
        elif platform.system() in ["Linux", "RedOS"]:
            desktop_file = os.path.join(desktop_path, "family_system.desktop")
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                print_colored("✅ .desktop файл удален", "green")
        
        print_colored("\n✅ Система полностью удалена!", "green")
        
    except Exception as e:
        print_colored(f"❌ Ошибка удаления: {e}", "red")
    
    input("\nНажмите Enter для завершения...")

def show_menu():
    """Показывает меню установщика"""
    while True:
        print_colored("\n" + "="*60, "purple")
        print_colored("    СИСТЕМА РАБОТЫ С СЕМЬЯМИ - УСТАНОВЩИК", "purple")
        print_colored("="*60, "purple")
        
        print_colored("\n1. 📦 Установить систему", "cyan")
        print_colored("2. 🗑️  Удалить систему", "cyan")
        print_colored("3. 🔍 Проверить зависимости", "cyan")
        print_colored("4. 🚪 Выход", "cyan")
        
        choice = input("\nВыберите действие [1-4]: ").strip()
        
        if choice == "1":
            install_system()
            break
        elif choice == "2":
            uninstall_system()
            break
        elif choice == "3":
            check_dependencies()
            input("\nНажмите Enter для продолжения...")
        elif choice == "4":
            print_colored("\n👋 До свидания!", "green")
            break
        else:
            print_colored("❌ Неверный выбор!", "red")

if __name__ == "__main__":
    show_menu()