#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сохранения ID таблицы в конфигурацию
"""

import sys
import os

# Добавляем путь к директории utils
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from utils.config_manager import get_default_config_manager


def main():
    """Сохранение ID таблицы в конфигурацию"""
    
    print("Сохранение ID таблицы в конфигурацию")
    print("="*40)
    
    # Создаем менеджер конфигурации
    config_manager = get_default_config_manager()
    
    # ID таблицы, которое нужно сохранить
    spreadsheet_id = "1REAUDJZCLqu7Vn_UcIGiVG9CqPWpNnGrD-luCIrDz2c"
    sheet_name = "АСП_Многодетные"
    
    print(f"Сохраняем ID таблицы: {spreadsheet_id}")
    print(f"Для листа: {sheet_name}")
    
    # Сохраняем ID таблицы
    config_manager.set_spreadsheet_id(sheet_name, spreadsheet_id)
    
    print("✅ ID таблицы успешно сохранен в конфигурацию!")
    
    # Проверим, что ID можно получить обратно
    retrieved_id = config_manager.get_spreadsheet_id(sheet_name)
    print(f"Полученный ID из конфигурации: {retrieved_id}")
    
    if retrieved_id == spreadsheet_id:
        print("✅ ID таблицы корректно сохранен и может быть извлечен")
    else:
        print("❌ Ошибка при извлечении ID таблицы")


if __name__ == "__main__":
    main()