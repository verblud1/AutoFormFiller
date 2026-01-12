"""Утилиты для работы с файлами и конфигурацией"""

import os
import json
import shutil
from pathlib import Path


def setup_config_directory(base_dir):
    """Создание папки для конфигурационных файлов"""
    config_dir = os.path.join(base_dir, "config")
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        print(f"✅ Создана папка конфигурации: {config_dir}")
    
    screenshots_dir = os.path.join(config_dir, "screenshots")
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        print(f"✅ Создана папка для скриншотов: {screenshots_dir}")
    
    logs_dir = os.path.join(config_dir, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"✅ Создана папка для логов: {logs_dir}")
    
    return config_dir, screenshots_dir, logs_dir


def load_config(config_file, default_config):
    """Загрузка конфигурации из файла"""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # Проверяем наличие всех необходимых ключей
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                        
                return config
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}")
    
    # Возвращаем конфигурацию по умолчанию, если файл не существует или произошла ошибка
    return default_config


def save_config(config_file, config):
    """Сохранение конфигурации в файл"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения конфигурации: {e}")
        return False


def find_registry_directory(start_dir):
    """Поиск папки registry относительно текущего файла"""
    
    # Проверяем в текущей папке (рядом с json_family_creator.py)
    current_dir_registry = os.path.join(start_dir, "registry")
    if os.path.exists(current_dir_registry):
        return current_dir_registry

    # Проверяем в родительской папке (installer)
    parent_dir = os.path.dirname(start_dir)
    parent_registry = os.path.join(parent_dir, "registry")
    if os.path.exists(parent_registry):
        return parent_registry

    # Проверяем в родительской папке родительской папки (корень проекта)
    grandparent_dir = os.path.dirname(parent_dir)
    grandparent_registry = os.path.join(grandparent_dir, "registry")
    if os.path.exists(grandparent_registry):
        return grandparent_registry

    # Если не нашли, возвращаем папку рядом с json_family_creator.py
    # и она будет создана позже
    return current_dir_registry


def load_last_files(register_dir, adpi_dir):
    """Загрузка последних файлов реестра и АДПИ при запуске"""
    # Ищем последний файл реестра
    register_files = [f for f in os.listdir(register_dir) if f.lower().endswith(('.xls', '.xlsx'))]
    last_register = None
    if register_files:
        # Берем последний измененный файл
        register_files.sort(key=lambda x: os.path.getmtime(os.path.join(register_dir, x)), reverse=True)
        last_register = os.path.join(register_dir, register_files[0])

    # Ищем последний файл АДПИ
    adpi_files = [f for f in os.listdir(adpi_dir) if f.lower().endswith(('.xls', '.xlsx', '.ods'))]
    last_adpi = None
    if adpi_files:
        adpi_files.sort(key=lambda x: os.path.getmtime(os.path.join(adpi_dir, x)), reverse=True)
        last_adpi = os.path.join(adpi_dir, adpi_files[0])
    
    return last_register, last_adpi