#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для тестирования получения ID таблицы с автоматической подстановкой
"""

import sys
import os

# Добавляем путь к директории utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from config_manager import ConfigManager


def main():
    """Проверка получения ID таблицы из конфигурации"""
    
    print("Проверка получения ID таблицы из конфигурации")
    print("="*50)
    
    # Создаем менеджер конфигурации
    config_manager = ConfigManager("config/app_config.json")
    
    # Название листа
    sheet_name = "АСП_Многодетные"
    
    # Получаем ID таблицы
    spreadsheet_id = config_manager.get_spreadsheet_id(sheet_name)
    
    print(f"Название листа: {sheet_name}")
    print(f"ID таблицы из конфигурации: {spreadsheet_id}")
    
    if spreadsheet_id:
        print("✅ ID таблицы успешно извлечен из конфигурации!")
        print(f"✅ Используется ID: {spreadsheet_id}")
    else:
        print("❌ ID таблицы не найден в конфигурации")


if __name__ == "__main__":
    main()