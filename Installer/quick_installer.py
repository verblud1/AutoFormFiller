#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
БЫСТРЫЙ УСТАНОВЩИК СИСТЕМЫ
Для Red OS и Windows 7/8 (универсальный)
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from datetime import datetime


def print_status(text):
    """Печатает статус (для терминала)"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [INFO] {text}")


def print_error(text):
    """Печатает ошибку (для терминала)"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [ERROR] {text}")


def print_success(text):
    """Печатает успех (для терминала)"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [SUCCESS] {text}")


def get_system_info():
    """Получает информацию о системе"""
    system = platform.system()
    release = platform.release()
    version = sys.version_info
    platform_info = platform.platform()
    
    return {
        'system': system,
        'release': release,
        'platform_info': platform_info,
        'python_version': f"{version.major}.{version.minor}.{version.micro}",
        'is_windows': system == "Windows",
        'is_linux': system in ["Linux", "RedOS"],
        'is_redos': "RedOS" in platform_info or system == "RedOS",
        'is_windows_7': 'Windows-7' in platform_info or '6.1.' in release,
        'is_windows_8': 'Windows-8' in platform_info or '6.2.' in release,
        'is_old_windows': 'Windows-7' in platform_info or '6.1.' in release or 'Windows-8' in platform_info or '6.2.' in release
    }


def check_python_version():
    """Проверяет версию Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print_error("Требуется Python 3.6 или выше")
        print_error(f"У вас установлен: Python {version.major}.{version.minor}.{version.micro}")
        return False
    return True


def get_default_install_path():
    """Определяет путь по умолчанию для установки"""
    system_info = get_system_info()
    
    if system_info['is_windows']:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    else:  # Linux/RedOS
        # Пробуем найти рабочий стол
        home_dir = os.path.expanduser("~")
        possible_paths = [
            os.path.join(home_dir, "Рабочий стол"),
            os.path.join(home_dir, "Desktop"),
            os.path.join(home_dir, "desktop"),
            os.path.join(home_dir, "Стол"),
            home_dir  # По умолчанию домашняя папка
        ]
        
        desktop = home_dir  # По умолчанию домашняя папка
        for path in possible_paths:
            if os.path.exists(path):
                desktop = path
                break
    
    return os.path.join(desktop, "FamilySystem")


def install_dependencies():
    """Устанавливает зависимости через pip с учетом старых систем"""
    print_status("Установка зависимостей...")
    
    system_info = get_system_info()
    
    # Определяем зависимости в зависимости от ОС
    if system_info['is_redos']:
        # Для Red OS используем проверенные версии
        required_packages = [
            "selenium==3.141.0",
            "webdriver-manager==3.8.0",
            "xlrd>=1.2.0",
            "pandas>=1.3.0",
            "openpyxl>=3.0.7"
        ]
        optional_packages = [
            "customtkinter==5.2.0"
        ]
    elif 'Windows-7' in platform.platform() or '6.1.' in platform.release():
        # Для Windows 7 используем совместимые версии
        required_packages = [
            "selenium==3.141.0",
            "webdriver-manager==3.8.0",
            "xlrd>=1.2.0",
            "pandas>=1.3.0",
            "openpyxl>=3.0.7"
        ]
        optional_packages = [
            "customtkinter==4.6.3"
        ]
    else:
        # Для других систем используем последние версии
        required_packages = [
            "selenium>=3.141.0",
            "webdriver-manager>=3.8.0",
            "xlrd>=1.2.0",
            "pandas>=1.3.0",
            "openpyxl>=3.0.7"
        ]
        optional_packages = [
            "customtkinter"
        ]
    
    # Устанавливаем обязательные пакеты
    for package in required_packages:
        try:
            print_status(f"Установка обязательной зависимости: {package}...")
            # Используем --user для избежания проблем с правами
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
            print_success(f"Установлена зависимость: {package}")
        except subprocess.CalledProcessError as e:
            print_error(f"Ошибка установки обязательной зависимости {package}: {e}")
            # Пробуем установить с дополнительными флагами для старых систем
            try:
                print_status(f"Повторная попытка установки {package} с флагами для совместимости...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "--force-reinstall", "--no-cache-dir", package])
                print_success(f"Установлена зависимость: {package} (после повторной попытки)")
            except subprocess.CalledProcessError as e2:
                print_error(f"Критическая ошибка установки {package}: {e2}")
                return False
    
    # Устанавливаем необязательные пакеты
    for package in optional_packages:
        try:
            print_status(f"Установка необязательной зависимости: {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
            print_success(f"Установлена зависимость: {package}")
        except subprocess.CalledProcessError as e:
            print_error(f"Не удалось установить необязательную зависимость {package}: {e}")
            print_status("Продолжение установки без этой зависимости...")
    
    return True


def install_system():
    """Упрощенная функция установки системы"""
    print_status("=== БЫСТРАЯ УСТАНОВКА СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ ===")
    
    # Проверяем версию Python
    if not check_python_version():
        return False
        
    # Устанавливаем зависимости
    install_dependencies()
    
    # Получаем информацию о системе
    system_info = get_system_info()
    print_status(f"Операционная система: {system_info['system']} {system_info['release']}")
    
    # Получаем путь по умолчанию
    default_path = get_default_install_path()
    print_status(f"Путь установки: {default_path}")
    
    # Создаем основную папку
    os.makedirs(default_path, exist_ok=True)
    print_success("Создана папка установки")
    
    # Определяем путь к файлам установщика
    installer_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Копируем основные файлы
    files_to_copy = [
        "json_family_creator.py",
        "massform.py",
        "family_system_launcher.py",
        "chrome_driver_helper.py",
        "autosave_families.json"  # Добавляем файл автосохранения
    ]
    
    # Добавляем скрипт подключения к базе данных в зависимости от ОС
    if system_info['is_windows']:
        files_to_copy.append("database_client.bat")
    else:
        files_to_copy.append("database_client.sh")
    
    for filename in files_to_copy:
        src_path = os.path.join(installer_dir, filename)
        dst_path = os.path.join(default_path, filename)
        
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, dst_path)
                print_success(f"Скопирован: {filename}")
            except Exception as e:
                print_error(f"Ошибка копирования {filename}: {e}")
        else:
            print_error(f"Файл не найден: {filename}")
    
    # Копируем папку registry если она существует
    registry_src = os.path.join(installer_dir, "registry")
    registry_dst = os.path.join(default_path, "registry")
    if os.path.exists(registry_src):
        try:
            shutil.copytree(registry_src, registry_dst, dirs_exist_ok=True)
            print_success("Скопирована папка registry")
        except Exception as e:
            print_error(f"Ошибка копирования папки registry: {e}")
    
    # Создаем структуру папок
    subdirs = [
        "config",
        os.path.join("config", "logs"),
        os.path.join("config", "screenshots")
    ]
    
    for subdir in subdirs:
        full_path = os.path.join(default_path, subdir)
        os.makedirs(full_path, exist_ok=True)
        print_success(f"Создана папка: {full_path}")
    
    # Создаем конфигурационный файл если его нет
    config_file = os.path.join(default_path, "config.env")
    if not os.path.exists(config_file):
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("""# Конфигурация подключения к базе данных
SSH_HOST="192.168.10.59"
SSH_USER="sshuser"
SSH_PASSWORD="orsd321"
LOCAL_PORT="8080"
REMOTE_HOST="172.30.1.18"
REMOTE_PORT="80"
WEB_PATH="/aspnetkp/common/FindInfo.aspx"
""")
        print_success("Создан конфигурационный файл config.env")
    
    # Делаем скрипты исполняемыми (для Linux/RedOS)
    if system_info['is_linux']:
        script_path = os.path.join(default_path, "database_client.sh")
        if os.path.exists(script_path):
            os.chmod(script_path, 0o755)
            print_success("Сделан исполняемым: database_client.sh")
    
    # Создаем ярлык
    if system_info['is_windows']:
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            bat_path = os.path.join(desktop, "Запуск_системы.bat")
            
            with open(bat_path, 'w', encoding='cp1251') as f:
                f.write(f"""@echo off
chcp 65001 >nul
echo Запуск системы работы с семьями...
cd /D "{default_path}"
"{sys.executable}" "family_system_launcher.py"
pause
""")
            print_success("Создан BAT файл на рабочем столе")
        except Exception as e:
            print_error(f"Ошибка создания ярлыка: {e}")
    else:
        try:
            home_dir = os.path.expanduser("~")
            possible_desktops = [
                os.path.join(home_dir, "Рабочий стол"),
                os.path.join(home_dir, "Desktop"),
                os.path.join(home_dir, "desktop"),
                os.path.join(home_dir, "Стол"),
                home_dir
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
Exec=python3 {os.path.join(default_path, 'family_system_launcher.py')}
Path={default_path}
Icon=system-run
Terminal=false
Categories=Utility;Office;
StartupNotify=true
""")
            
            os.chmod(desktop_file, 0o755)
            print_success("Создан .desktop файл на рабочем столе")
        except Exception as e:
            print_error(f"Ошибка создания .desktop файла: {e}")
    
    # Создаем файл информации об установке
    info_file = os.path.join(default_path, "INSTALL_INFO.txt")
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"""БЫСТРАЯ УСТАНОВКА СИСТЕМЫ
========================

Дата установки: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
Путь установки: {default_path}
Операционная система: {system_info['system']} {system_info['release']}
Версия Python: {system_info['python_version']}

КАК ЗАПУСТИТЬ:
- Используйте ярлык на рабочем столе
- Или запустите: python3 family_system_launcher.py из папки {default_path}
""")
    
    print_success("=== УСТАНОВКА ЗАВЕРШЕНА ===")
    print_status(f"Система установлена в: {default_path}")
    print_status("Запустите систему через ярлык на рабочем столе")
    
    return True


def main():
    """Основная функция"""
    print("="*50)
    print("    БЫСТРЫЙ УСТАНОВЩИК СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ")
    print("="*50)
    
    try:
        if install_system():
            print("\n🎉 Установка завершена!")
        else:
            print("\n❌ Установка завершена с ошибками")
    except KeyboardInterrupt:
        print("\n❌ Установка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
    
    input("\nНажмите Enter для завершения...")


if __name__ == "__main__":
    main()