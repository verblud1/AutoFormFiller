#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УПРОЩЕННЫЙ УСТАНОВЩИК СИСТЕМЫ
Для Red OS и Windows 7/8
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


def check_browser_compatibility():
    """Проверяет совместимость браузеров для старых систем"""
    print_status("Проверка совместимости браузеров...")
    
    system_info = get_system_info()
    
    if system_info['is_old_windows']:
        print_status("Обнаружена старая версия Windows (7 или 8)")
        print_status("Система будет настроена для совместимости с Internet Explorer и старыми версиями Chrome/Firefox")
        
        # Для старых Windows добавляем специфичные настройки
        if system_info['is_windows_7']:
            print_status("Windows 7: учитываем ограничения по версиям браузеров")
        elif system_info['is_windows_8']:
            print_status("Windows 8: учитываем особенности системы")
    
    elif system_info['is_redos']:
        print_status("Обнаружена RedOS")
        print_status("Проверка доступных браузеров в системе...")
        
        # Проверяем доступные браузеры в RedOS
        browsers = []
        for browser in ['firefox', 'chromium', 'google-chrome', 'iceweasel']:
            try:
                result = subprocess.run(['which', browser], capture_output=True, text=True)
                if result.returncode == 0:
                    browsers.append(browser)
            except:
                pass
        
        if browsers:
            print_success(f"Найдены доступные браузеры: {', '.join(browsers)}")
        else:
            print_error("Не найдено подходящих браузеров в системе")
            print_status("Установка может продолжиться, но потребуется ручная установка браузера")
    
    else:
        print_status("Современная операционная система, проверка совместимости пройдена")
    
    return True


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


def check_basic_dependencies():
    """Проверяет основные зависимости (только встроенные библиотеки)"""
    print_status("Проверка базовых зависимостей...")
    
    # Проверяем только встроенные модули, чтобы избежать проблем с установкой
    try:
        import json
        import os
        import sys
        import platform
        import subprocess
        import shutil
        print_success("Базовые зависимости в порядке")
        return True
    except ImportError as e:
        print_error(f"Ошибка импорта базовых модулей: {e}")
        return False


def install_dependencies():
    """Устанавливает зависимости через pip с учетом старых систем"""
    print_status("Установка зависимостей...")
    
    system_info = get_system_info()
    
    # Определяем зависимости в зависимости от ОС
    if system_info['is_redos']:
        # Для Red OS используем проверенные версии
        required_packages = [
            "selenium==3.141.0",
            "webdriver-manager==3.8.0"
        ]
        optional_packages = [
            "customtkinter==5.2.0"
        ]
    elif 'Windows-7' in platform.platform() or '6.1.' in platform.release():
        # Для Windows 7 используем совместимые версии
        required_packages = [
            "selenium==3.141.0",
            "webdriver-manager==3.8.0"
        ]
        optional_packages = [
            "customtkinter==4.6.3"
        ]
    else:
        # Для других систем используем последние версии
        required_packages = [
            "selenium>=3.141.0",
            "webdriver-manager>=3.8.0"
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


def create_installation_structure(install_dir):
    """Создает структуру папок для установки"""
    print_status(f"Создание структуры папок в: {install_dir}")
    
    # Создаем основную папку
    os.makedirs(install_dir, exist_ok=True)
    
    # Создаем подпапки
    subdirs = [
        "config",
        os.path.join("config", "logs"),
        os.path.join("config", "screenshots")
    ]
    
    for subdir in subdirs:
        full_path = os.path.join(install_dir, subdir)
        os.makedirs(full_path, exist_ok=True)
        print_success(f"Создана папка: {full_path}")
    
    return True


def copy_system_files(install_dir):
    """Копирует файлы системы в папку установки"""
    print_status("Копирование файлов системы...")
    
    # Определяем путь к файлам установщика
    installer_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Список файлов для копирования
    files_to_copy = [
        ("json_family_creator.py", True),
        ("massform.py", True),
        ("family_system_launcher.py", True),
        ("chrome_driver_helper.py", True),
        ("requirements.txt", True),
    ]
    
    # Добавляем скрипты подключения к базе данных в зависимости от ОС
    system_info = get_system_info()
    if system_info['is_windows']:
        files_to_copy.append(("database_client.bat", True))
    else:
        files_to_copy.append(("database_client.sh", True))
    
    copied_files = 0
    
    for filename, required in files_to_copy:
        src_path = os.path.join(installer_dir, filename)
        dst_path = os.path.join(install_dir, filename)
        
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, dst_path)
                copied_files += 1
                print_success(f"Скопирован: {filename}")
            except Exception as e:
                print_error(f"Ошибка копирования {filename}: {e}")
                if required:
                    return False
        else:
            if required:
                print_error(f"Файл не найден: {filename}")
                return False
            else:
                print_status(f"Файл не найден (необязательный): {filename}")
    
    # Создаем конфигурационный файл если его нет
    config_file = os.path.join(install_dir, "config.env")
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
        print_success("Создан конфигурационный файл config.env")
    
    # Делаем скрипты исполняемыми (для Linux/RedOS)
    if system_info['is_linux']:
        script_path = os.path.join(install_dir, "database_client.sh")
        if os.path.exists(script_path):
            os.chmod(script_path, 0o755)
            print_success("Сделан исполняемым: database_client.sh")
    
    return True


def create_shortcut(install_dir):
    """Создает ярлык на рабочем столе"""
    print_status("Создание ярлыка на рабочем столе...")
    
    system_info = get_system_info()
    
    if system_info['is_windows']:
        return create_windows_shortcut(install_dir)
    elif system_info['is_linux']:
        return create_linux_shortcut(install_dir)
    else:
        print_error("Неподдерживаемая операционная система")
        return False


def create_windows_shortcut(install_dir):
    """Создает ярлык на рабочем столе Windows"""
    # Сначала пробуем создать .bat файл, так как он не требует дополнительных библиотек
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        bat_path = os.path.join(desktop, "Запуск_системы.bat")
        
        with open(bat_path, 'w', encoding='cp1251') as f:
            f.write(f"""@echo off
chcp 65001 >nul
echo Запуск системы работы с семьями...
cd /D "{install_dir}"
"{sys.executable}" "family_system_launcher.py"
pause
""")
        print_success("Создан BAT файл на рабочем столе")
        
        # Если есть winshell и win32com, пробуем создать .lnk
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Система работы с семьями.lnk")
            
            target = sys.executable
            arguments = os.path.join(install_dir, "family_system_launcher.py")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.Arguments = f'"{arguments}"'
            shortcut.WorkingDirectory = install_dir
            shortcut.IconLocation = target
            shortcut.save()
            
            print_success("Создан ярлык .lnk на рабочем столе Windows")
            return True
        except ImportError:
            print_status("Библиотеки winshell или pywin32 не установлены, используется BAT файл")
            return True
        except Exception as e:
            print_error(f"Ошибка создания .lnk ярлыка: {e}, но BAT файл создан")
            return True
            
    except Exception as e:
        print_error(f"Ошибка создания ярлыка Windows: {e}")
        return False


def create_linux_shortcut(install_dir):
    """Создает .desktop файл для Linux/RedOS"""
    try:
        # Определяем путь к рабочему столу
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
Exec=python3 {os.path.join(install_dir, 'family_system_launcher.py')}
Path={install_dir}
Icon=system-run
Terminal=false
Categories=Utility;Office;
StartupNotify=true
""")
        
        os.chmod(desktop_file, 0o755)
        print_success("Создан .desktop файл на рабочем столе")
        return True
        
    except Exception as e:
        print_error(f"Ошибка создания .desktop файла: {e}")
        return False


def create_install_info(install_dir):
    """Создает файл информации об установке"""
    print_status("Создание информации об установке...")
    
    system_info = get_system_info()
    
    install_info = {
        "install_path": install_dir,
        "install_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "os": system_info['system'],
        "os_release": system_info['release'],
        "python_version": system_info['python_version'],
        "version": "1.0",
        "components": {
            "json_family_creator": "v1.0",
            "massform": "v1.0",
            "family_system_launcher": "v1.0",
            "database_client": "v1.0"
        }
    }
    
    info_json = os.path.join(install_dir, "install_info.json")
    with open(info_json, 'w', encoding='utf-8') as f:
        json.dump(install_info, f, indent=2, ensure_ascii=False)
    
    # Создаем файл информации в текстовом формате
    info_file = os.path.join(install_dir, "INSTALL_INFO.txt")
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"""ИНФОРМАЦИЯ ОБ УСТАНОВКЕ
=================================
СИСТЕМА РАБОТЫ С СЕМЬЯМИ
=================================

Дата установки: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}
Путь установки: {install_dir}
Операционная система: {system_info['system']} {system_info['release']}
Версия Python: {system_info['python_version']}

=================================
КАК ЗАПУСТИТЬ СИСТЕМУ:
=================================

1. НАСТОЯТЕЛЬНО РЕКОМЕНДУЕТСЯ:
- Найдите на рабочем столе ярлык "Система работы с семьями"
- Запустите его двойным щелчком
- Используйте лаунчер для запуска всех компонентов системы

2. АЛЬТЕРНАТИВНЫЙ СПОСОБ:
- Откройте папку: {install_dir}
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

1. Откройте файл: {install_dir}/config.env
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
""")
    
    print_success("Файл информации об установке создан")
    return True


def install_system():
    """Основная функция установки системы"""
    print_status("Начало установки системы работы с семьями")
    
    # Проверяем версию Python
    if not check_python_version():
        return False
    
    # Проверяем базовые зависимости
    if not check_basic_dependencies():
        return False
    
    # Проверяем совместимость браузеров
    check_browser_compatibility()
    
    # Получаем информацию о системе
    system_info = get_system_info()
    print_status(f"Операционная система: {system_info['system']} {system_info['release']}")
    print_status(f"Версия Python: {system_info['python_version']}")
    print_status(f"Платформа: {system_info['platform_info']}")
    
    # Получаем путь по умолчанию
    default_path = get_default_install_path()
    print_status(f"Путь по умолчанию: {default_path}")
    
    # Запрашиваем путь установки
    install_path = input(f"Введите путь для установки (Enter для {default_path}): ").strip()
    if not install_path:
        install_path = default_path
    
    # Подтверждение установки
    print_status(f"Будет установлено в: {install_path}")
    confirm = input("Продолжить установку? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes', 'д', 'да']:
        print_error("Установка отменена пользователем")
        return False
    
    # Проверяем, существует ли уже система
    if os.path.exists(install_path):
        print_status("Папка уже существует!")
        overwrite = input("Переустановить? (y/N): ").strip().lower()
        if overwrite not in ['y', 'yes', 'д', 'да']:
            print_error("Установка отменена")
            return False
        
        # Создаем резервную копию конфига
        config_file = os.path.join(install_path, "config.env")
        backup_file = os.path.join(install_path, "config.env.backup")
        if os.path.exists(config_file):
            try:
                shutil.copy2(config_file, backup_file)
                print_success("Создана резервная копия конфигурации")
            except Exception as e:
                print_error(f"Ошибка создания резервной копии: {e}")
    
    # Создаем структуру папок
    if not create_installation_structure(install_path):
        print_error("Ошибка создания структуры папок")
        return False
    
    # Копируем файлы системы
    if not copy_system_files(install_path):
        print_error("Ошибка копирования файлов системы")
        return False
    
    # Создаем ярлык
    if not create_shortcut(install_path):
        print_error("Ошибка создания ярлыка")
        # Не прерываем установку, так как ярлык не является критичным
    
    # Создаем информацию об установке
    if not create_install_info(install_path):
        print_error("Ошибка создания информации об установке")
        return False
    
    print_success("Установка завершена успешно!")
    print_status(f"Папка системы: {install_path}")
    print_status("Теперь вы можете запустить систему через ярлык на рабочем столе")
    
    # Предлагаем запустить систему
    run_now = input("Запустить систему сейчас? (Y/n): ").strip().lower()
    if run_now in ['', 'y', 'yes', 'д', 'да']:
        launcher_path = os.path.join(install_path, "family_system_launcher.py")
        try:
            subprocess.Popen([sys.executable, launcher_path])
            print_success("Система запущена!")
        except Exception as e:
            print_error(f"Ошибка запуска системы: {e}")
            print_status(f"Вы можете запустить вручную: python {launcher_path}")
    
    return True


def main():
    """Основная функция"""
    print("="*60)
    print("    УПРОЩЕННЫЙ УСТАНОВЩИК СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ")
    print("="*60)
    
    try:
        if install_system():
            print("\n🎉 Установка успешно завершена!")
            print("==========================================")
            print("Следующие шаги:")
            print("1. Настройте файл config.env")
            print("2. Запустите ярлык на рабочем столе")
            print("3. Начните работать с системой!")
            print("==========================================")
        else:
            print("\n❌ Установка завершена с ошибками")
    except KeyboardInterrupt:
        print("\n❌ Установка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
    
    input("\nНажмите Enter для завершения...")


if __name__ == "__main__":
    main()