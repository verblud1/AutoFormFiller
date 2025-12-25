#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УНИВЕРСАЛЬНЫЙ УСТАНОВЩИК СИСТЕМЫ
С ВЫБОРОМ МЕСТА УСТАНОВКИ
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

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

def select_install_directory(default_path=None):
    """Позволяет пользователю выбрать папку для установки"""
    try:
        # Создаем скрытое окно tkinter для диалога
        root = tk.Tk()
        root.withdraw()  # Скрываем основное окно
        
        if default_path and os.path.exists(default_path):
            initial_dir = default_path
        else:
            initial_dir = os.path.expanduser("~")
        
        print_colored(f"\n📁 Текущий путь по умолчанию: {initial_dir}", "cyan")
        
        # Показываем диалог выбора папки
        install_dir = filedialog.askdirectory(
            title="Выберите папку для установки системы",
            initialdir=initial_dir
        )
        
        root.destroy()
        
        if not install_dir:  # Пользователь нажал "Отмена"
            print_colored("❌ Установка отменена пользователем", "red")
            return None
        
        return install_dir
        
    except Exception as e:
        print_colored(f"⚠️  Ошибка выбора папки: {e}", "yellow")
        
        # Используем путь по умолчанию при ошибке
        if default_path:
            return default_path
        else:
            return os.path.join(os.path.expanduser("~"), "Desktop", "FamilySystem")

def get_default_install_path():
    """Определяет путь по умолчанию для установки"""
    system = platform.system()
    home_dir = os.path.expanduser("~")
    
    if system == "Windows":
        desktop = os.path.join(home_dir, "Desktop")
    else:  # Linux/RedOS
        # Пробуем найти рабочий стол
        possible_paths = [
            os.path.join(home_dir, "Рабочий стол"),
            os.path.join(home_dir, "Desktop"),
            os.path.join(home_dir, "desktop"),
            os.path.join(home_dir, "Стол")
        ]
        
        desktop = home_dir  # По умолчанию домашняя папка
        for path in possible_paths:
            if os.path.exists(path):
                desktop = path
                break
    
    return os.path.join(desktop, "FamilySystem")

def check_dependencies():
    """Проверяет и устанавливает зависимости"""
    print_colored("\n🔍 Проверка зависимостей...", "cyan")
    
    system = platform.system()
    python_version = sys.version_info
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print_colored("❌ Требуется Python 3.7 или выше", "red")
        print_colored(f"У вас установлен: Python {python_version.major}.{python_version.minor}", "yellow")
        return False
    
    print_colored(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}", "green")
    
    # Проверяем необходимые библиотеки
    missing_deps = []
    
    try:
        import customtkinter
        print_colored("✅ customtkinter установлена", "green")
    except ImportError:
        missing_deps.append("customtkinter")
        print_colored("❌ customtkinter не установлена", "red")
    
    try:
        import tkinter
        print_colored("✅ tkinter установлена", "green")
    except ImportError:
        if system == "Linux" or system == "RedOS":
            print_colored("❌ tkinter не установлена", "red")
            print_colored("Установите: sudo dnf install python3-tkinter", "yellow")
        elif system == "Windows":
            print_colored("❌ tkinter не установлена", "red")
            print_colored("Переустановите Python с опцией 'tcl/tk and IDLE'", "yellow")
        return False
    
    # Предлагаем установить недостающие зависимости
    if missing_deps:
        print_colored(f"\n⚠️  Отсутствуют библиотеки: {', '.join(missing_deps)}", "yellow")
        response = input("Установить автоматически? (y/N): ")
        
        if response.lower() in ['y', 'yes', 'д', 'да']:
            try:
                import subprocess
                for dep in missing_deps:
                    print_colored(f"📦 Устанавливаю {dep}...", "cyan")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                    print_colored(f"✅ {dep} установлена", "green")
            except Exception as e:
                print_colored(f"❌ Ошибка установки: {e}", "red")
                print_colored("Установите вручную: pip install customtkinter", "yellow")
                return False
    
    return True

def install_system():
    """Устанавливает систему в выбранную папку"""
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
    
    # Получаем путь по умолчанию
    default_path = get_default_install_path()
    
    # Предлагаем выбрать папку
    print_colored(f"\n📁 Путь по умолчанию: {default_path}", "cyan")
    response = input("Использовать путь по умолчанию? (Y/n): ").strip().lower()
    
    if response in ['', 'y', 'yes', 'д', 'да']:
        system_dir = default_path
    else:
        # Открываем диалог выбора папки
        system_dir = select_install_directory(default_path)
        if not system_dir:
            return
    
    # Запрашиваем подтверждение
    print_colored(f"\n📁 Будет установлено в: {system_dir}", "cyan")
    
    response = input("Продолжить установку? (Y/n): ").strip().lower()
    if response not in ['', 'y', 'yes', 'д', 'да']:
        print_colored("❌ Установка отменена пользователем", "red")
        return
    
    # Проверяем, существует ли уже система
    if os.path.exists(system_dir):
        print_colored("\n⚠️  Папка уже существует!", "yellow")
        response = input("Переустановить? (y/N): ")
        if response.lower() not in ['y', 'yes', 'д', 'да']:
            print_colored("❌ Установка отменена", "red")
            return
        
        # Создаем резервную копию конфига
        config_file = os.path.join(system_dir, "config.env")
        backup_file = os.path.join(system_dir, "config.env.backup")
        if os.path.exists(config_file):
            try:
                shutil.copy2(config_file, backup_file)
                print_colored("📋 Создана резервная копия конфигурации", "green")
            except:
                pass
    
    # Создаем папку системы
    os.makedirs(system_dir, exist_ok=True)
    print_colored(f"✅ Создана папка: {system_dir}", "green")
    
    # Определяем путь к файлам установщика
    installer_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Список файлов для копирования
    files_to_copy = [
        ("json_family_creator.py", True),
        ("massform.py", True),
        ("database_client.sh", True),
        ("database_client.bat", True),
        ("family_system_launcher.py", True),
        ("config.env", False),  # Не перезаписывать если есть
        ("family_creator_config.json", False),  # Конфигурация для json_family_creator
        ("mass_processor_config.json", False),  # Конфигурация для massform
        ("launcher_config.json", False),  # Конфигурация для лаунчера
        ("README.txt", True),
        ("install_system.py", True),  # Этот файл
    ]
    
    # Копируем файлы
    copied_files = 0
    print_colored("\n📦 Копирую файлы системы...", "cyan")
    
    for filename, overwrite in files_to_copy:
        src_path = os.path.join(installer_dir, filename)
        dst_path = os.path.join(system_dir, filename)
        
        # Проверяем, нужно ли копировать
        if not overwrite and os.path.exists(dst_path):
            print_colored(f"  ⚠️  {filename}: сохранен существующий", "yellow")
            continue
            
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, dst_path)
                copied_files += 1
                print_colored(f"  📄 {filename}", "green")
            except Exception as e:
                print_colored(f"  ❌ {filename}: {e}", "red")
        else:
            print_colored(f"  ⚠️  {filename}: не найден в установщике", "yellow")
    
    # Создаем структуру подпапок для конфигурации, логов и скриншотов
    config_dir = os.path.join(system_dir, "config")
    logs_dir = os.path.join(config_dir, "logs")
    screenshots_dir = os.path.join(config_dir, "screenshots")
    adpi_dir = os.path.join(config_dir, "adpi")
    register_dir = os.path.join(config_dir, "register")
    
    for dir_path in [config_dir, logs_dir, screenshots_dir, adpi_dir, register_dir]:
        os.makedirs(dir_path, exist_ok=True)
        print_colored(f"📁 Создана папка: {dir_path}", "green")
    
    # Создаем конфигурационный файл если его нет
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

# Дополнительные настройки
# AUTO_UPDATE=true
# CHECK_FOR_UPDATES=true
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
        create_linux_desktop_file(system_dir)
    
    # Создаем файл информации об установке
    info_file = os.path.join(system_dir, "INSTALL_INFO.txt")
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"""ИНФОРМАЦИЯ ОБ УСТАНОВКЕ
=================================
СИСТЕМА РАБОТЫ С СЕМЬЯМИ
=================================

Дата установки: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
Путь установки: {system_dir}
Операционная система: {platform.system()} {platform.release()}
Версия Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}

=================================
КАК ЗАПУСТИТЬ СИСТЕМУ:
=================================

1. НАСТОЯТЕЛЬНО РЕКОМЕНДУЕТСЯ:
- Найдите на рабочем столе ярлык "Система работы с семьями"
- Запустите его двойным щелчком
- Используйте лаунчер для запуска всех компонентов системы

2. АЛЬТЕРНАТИВНЫЙ СПОСОБ:
- Откройте папку: {system_dir}
- Запустите файл: family_system_launcher.py

=================================
КОМПОНЕНТЫ СИСТЕМЫ:
=================================

1. 📝 Создатель JSON (json_family_creator.py)
   - Редактирование данных о семьях
   - Создание JSON файлов
   - Автоопределение семей из реестра
   - Загрузка данных АДПИ из Excel/ODS файлов
   - Автоподсчет пособий и доходов
   - Автосохранение и загрузка данных

2. ⚙️ Массовый обработчик (massform.py)
   - Автоматическое заполнение базы данных
   - Обработка нескольких семей подряд
   - Поддержка ручного вмешательства
   - Сохранение скриншотов
   - Повторная обработка ошибок

3. 🗄️ Клиент базы данных (database_client.sh/bat)
   - Подключение к корпоративной базе данных
   - SSH туннель для доступа
   - Автоматическое открытие браузера

4. 🚀 Лаунчер системы (family_system_launcher.py)
   - Единая точка входа для всех компонентов
   - Обновление через GitHub
   - Статистика обработки семей
   - Управление системой (установка/удаление/обновление)

=================================
НАСТРОЙКА:
=================================

1. Откройте файл: {system_dir}/config.env
2. Заполните настройки подключения к базе данных:
   - SSH_HOST - адрес сервера
   - SSH_USER - имя пользователя
   - SSH_PASSWORD - пароль
   - и другие параметры
3. Дополнительные конфигурационные файлы находятся в папке config/

=================================
ОБНОВЛЕНИЕ СИСТЕМЫ:
=================================

1. Запустите систему через лаунчер
2. Нажмите кнопку "🔄 ОБНОВИТЬ ЧЕРЕЗ GITHUB"
3. Следуйте инструкциям на экране

Или запустите установщик заново для переустановки.

=================================
ПОДДЕРЖКА:
=================================

При возникновении проблем:
1. Проверьте наличие Python 3.7+
2. Установите зависимости: pip install customtkinter
3. Проверьте настройки в config.env
4. Убедитесь, что есть доступ к серверу базы данных
5. Файлы конфигурации, логи и скриншоты находятся в папке config/
6. Для обновления системы используйте кнопку "🔄 ОБНОВИТЬ ЧЕРЕЗ GITHUB" в лаунчере
7. При ошибках обращайтесь к файлам логов в папке config/logs/
""")
    
    # Сохраняем путь установки для обновлений
    install_info = {
        "install_path": system_dir,
        "install_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "os": platform.system(),
        "version": "1.0"
    }
    
    # Обновляем версию в информации об установке
    install_info = {
        "install_path": system_dir,
        "install_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "os": platform.system(),
        "version": "2.0",  # Обновленная версия с поддержкой новых функций
        "components": {
            "json_family_creator": "v1.0",
            "massform": "v1.0",
            "family_system_launcher": "v1.0",
            "database_client": "v1.0"
        }
    }
    
    info_json = os.path.join(system_dir, "install_info.json")
    with open(info_json, 'w', encoding='utf-8') as f:
        json.dump(install_info, f, indent=2, ensure_ascii=False)
    
    print_colored(f"\n✅ Установка завершена!", "green")
    print_colored(f"📁 Папка системы: {system_dir}", "cyan")
    print_colored(f"📋 Скопировано файлов: {copied_files}", "cyan")
    
    # Запускаем лаунчер
    response = input("\n🚀 Запустить систему сейчас? (Y/n): ").strip().lower()
    if response in ['', 'y', 'yes', 'д', 'да']:
        print_colored("Запускаю лаунчер системы...", "cyan")
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
    
    print_colored("\n🎉 Установка успешно завершена!", "green")
    print_colored("==========================================", "cyan")
    print_colored("Следующие шаги:", "cyan")
    print_colored("1. Настройте файл config.env", "cyan")
    print_colored("2. Запустите ярлык на рабочем столе", "cyan")
    print_colored("3. Начните работать с системой!", "cyan")
    print_colored("==========================================", "cyan")
    
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
        
        # Альтернатива: создаем .bat файл
        bat_path = os.path.join(os.path.expanduser("~"), "Desktop", "Запуск_системы.bat")
        try:
            with open(bat_path, 'w', encoding='cp1251') as f:
                f.write(f"""@echo off
chcp 65001 >nul
echo Запуск системы работы с семьями...
cd /D "{system_dir}"
"{sys.executable}" "family_system_launcher.py"
pause
""")
            print_colored("✅ Создан BAT файл на рабочем столе", "green")
            return True
        except:
            return False

def create_linux_desktop_file(system_dir):
    """Создает .desktop файл для Linux/RedOS"""
    try:
        # Определяем путь к рабочему столу
        home_dir = os.path.expanduser("~")
        possible_desktops = [
            os.path.join(home_dir, "Рабочий стол"),
            os.path.join(home_dir, "Desktop"),
            os.path.join(home_dir, "desktop"),
            os.path.join(home_dir, "Стол")
        ]
        
        desktop_path = home_dir
        for path in possible_desktops:
            if os.path.exists(path):
                desktop_path = path
                break
        
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
        
        # Альтернатива: создаем скрипт запуска
        script_path = os.path.join(home_dir, "Desktop", "запуск_системы.sh")
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(f"""#!/bin/bash
echo "Запуск системы работы с семьями..."
cd "{system_dir}"
python3 family_system_launcher.py
""")
            os.chmod(script_path, 0o755)
            print_colored("✅ Создан скрипт запуска на рабочем столе", "green")
            return True
        except:
            return False

def uninstall_system():
    """Удаляет систему"""
    print_colored("\n" + "="*60, "red")
    print_colored("    УДАЛЕНИЕ СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ", "red")
    print_colored("="*60, "red")
    
    # Спрашиваем путь к системе
    default_path = get_default_install_path()
    print_colored(f"📁 Путь по умолчанию: {default_path}", "cyan")
    
    response = input("Удалить из пути по умолчанию? (Y/n): ").strip().lower()
    
    if response in ['', 'y', 'yes', 'д', 'да']:
        system_dir = default_path
    else:
        # Открываем диалог выбора папки
        system_dir = select_install_directory(default_path)
        if not system_dir:
            return
    
    if not os.path.exists(system_dir):
        print_colored("❌ Указанная папка не существует!", "red")
        return
    
    # Проверяем, что это действительно папка системы
    if not os.path.exists(os.path.join(system_dir, "family_system_launcher.py")):
        print_colored("⚠️  В указанной папке не найдена система!", "yellow")
        response = input("Все равно удалить папку? (y/N): ")
        if response.lower() not in ['y', 'yes', 'д', 'да']:
            return
    
    print_colored(f"\n📁 Будет удалена папка: {system_dir}", "cyan")
    response = input("❌ Вы уверены, что хотите удалить систему? (y/N): ")
    if response.lower() not in ['y', 'yes', 'д', 'да']:
        print_colored("❌ Удаление отменено", "yellow")
        return
    
    try:
        # Удаляем папку системы
        shutil.rmtree(system_dir)
        print_colored("✅ Папка системы удалена", "green")
        
        # Также удаляем созданные подпапки, если они остались
        config_subdirs = ["config", "config/logs", "config/screenshots", "config/adpi", "config/register"]
        for subdir in config_subdirs:
            full_path = os.path.join(system_dir, subdir)
            if os.path.exists(full_path):
                shutil.rmtree(full_path)
                print_colored(f"✅ Папка {subdir} удалена", "green")
        
        # Удаляем ярлыки
        if platform.system() == "Windows":
            try:
                import winshell
                desktop = winshell.desktop()
                shortcuts = [
                    os.path.join(desktop, "Система работы с семьями.lnk"),
                    os.path.join(desktop, "Запуск_системы.bat")
                ]
                for shortcut in shortcuts:
                    if os.path.exists(shortcut):
                        os.remove(shortcut)
                        print_colored(f"✅ Удален ярлык: {os.path.basename(shortcut)}", "green")
            except:
                pass
        elif platform.system() in ["Linux", "RedOS"]:
            home_dir = os.path.expanduser("~")
            possible_desktops = [
                os.path.join(home_dir, "Рабочий стол"),
                os.path.join(home_dir, "Desktop"),
                os.path.join(home_dir, "desktop"),
                os.path.join(home_dir, "Стол")
            ]
            
            for desktop_path in possible_desktops:
                shortcuts = [
                    os.path.join(desktop_path, "family_system.desktop"),
                    os.path.join(desktop_path, "запуск_системы.sh")
                ]
                for shortcut in shortcuts:
                    if os.path.exists(shortcut):
                        os.remove(shortcut)
                        print_colored(f"✅ Удален ярлык: {os.path.basename(shortcut)}", "green")
        
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
        print_colored("4. ℹ️  Информация о системе", "cyan")
        print_colored("5. 🚪 Выход", "cyan")
        
        choice = input("\nВыберите действие [1-5]: ").strip()
        
        if choice == "1":
            install_system()
            break
        elif choice == "2":
            uninstall_system()
            break
        elif choice == "3":
            if check_dependencies():
                print_colored("\n✅ Все зависимости установлены!", "green")
            input("\nНажмите Enter для продолжения...")
        elif choice == "4":
            show_system_info()
        elif choice == "5":
            print_colored("\n👋 До свидания!", "green")
            break
        else:
            print_colored("❌ Неверный выбор!", "red")

def show_system_info():
    """Показывает информацию о системе"""
    print_colored("\n" + "="*60, "cyan")
    print_colored("    ИНФОРМАЦИЯ О СИСТЕМЕ", "cyan")
    print_colored("="*60, "cyan")
    
    print_colored(f"\n📱 Операционная система: {platform.system()} {platform.release()}", "cyan")
    print_colored(f"🐍 Python версия: {sys.version}", "cyan")
    print_colored(f"📁 Текущая папка: {os.path.abspath('.')}", "cyan")
    
    # Проверяем установленные библиотеки
    print_colored("\n📚 Проверка библиотек:", "cyan")
    
    libs_to_check = [
        ("customtkinter", "GUI интерфейс"),
        ("tkinter", "Графическая библиотека"),
        ("requests", "HTTP запросы"),
        ("selenium", "Автоматизация браузера"),
        ("pandas", "Работа с данными"),
    ]
    
    for lib_name, lib_desc in libs_to_check:
        try:
            __import__(lib_name)
            print_colored(f"  ✅ {lib_name}: {lib_desc}", "green")
        except ImportError:
            print_colored(f"  ❌ {lib_name}: {lib_desc}", "red")
    
    input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    try:
        show_menu()
    except KeyboardInterrupt:
        print_colored("\n\n❌ Установка прервана пользователем", "red")
    except Exception as e:
        print_colored(f"\n❌ Критическая ошибка: {e}", "red")
        input("Нажмите Enter для выхода...")