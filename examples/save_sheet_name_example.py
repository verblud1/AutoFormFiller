#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для сохранения названия листа "Список граждан (Лист 1)" в конфигурацию
"""

import sys
import os

# Добавляем путь к директории utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.config_manager import get_default_config_manager


def main():
    """Сохранение названия листа в конфигурацию"""
    
    print("Сохранение названия листа в конфигурацию")
    print("="*40)
    
    # Создаем менеджер конфигурации
    config_manager = get_default_config_manager()
    
    # Оригинальное и новое название листа
    original_name = "АСП_Многодетные"
    new_name = "Список граждан (Лист 1)"
    
    print(f"Сохраняем название листа:")
    print(f"Оригинальное название: {original_name}")
    print(f"Новое название: {new_name}")
    
    # Сохраняем новое название листа
    config_manager.set_sheet_name(original_name, new_name)
    
    print("✅ Название листа успешно сохранено в конфигурацию!")
    
    # Проверим, что название можно получить обратно
    retrieved_name = config_manager.get_sheet_name(original_name)
    print(f"Полученное название из конфигурации: {retrieved_name}")
    
    if retrieved_name == new_name:
        print("✅ Название листа корректно сохранено и может быть извлечено")
    else:
        print("❌ Ошибка при извлечении названия листа")


if __name__ == "__main__":
    main()