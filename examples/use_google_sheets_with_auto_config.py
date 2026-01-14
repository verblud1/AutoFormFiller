#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример использования модуля Google Sheets с автоматическим сохранением и подстановкой ID таблицы
"""

import os
import sys

# Добавляем путь к директории utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.google_sheets_handler import (
    interactive_check_existing_colors_and_highlight_with_auto_config,
    get_spreadsheet_id_with_auto_save
)
from utils.config_manager import get_default_config_manager


def main():
    """Пример использования функций с автоматическим управлением ID таблицы"""
    
    print("Пример использования Google Sheets с автоконфигурацией")
    print("="*60)
    
    # Путь к файлу учетных данных Google
    credentials_file = "hale-sentry-478217-a7-e2f18fda44d4.json"  # Путь к вашему файлу сервисного аккаунта
    
    # Проверяем, существует ли файл учетных данных
    if not os.path.exists(credentials_file):
        print(f"❌ Файл учетных данных {credentials_file} не найден")
        # Попробуем найти файлы с расширением .json в корне проекта
        json_files = [f for f in os.listdir('.') if f.endswith('.json')]
        if json_files:
            print(f"📁 Найдены JSON файлы: {json_files}")
            credentials_file = json_files[0]  # Берем первый найденный
            print(f"🔄 Используем {credentials_file} как файл учетных данных")
        else:
            print("❌ Не найдено ни одного JSON файла с учетными данными")
            return False
    
    # Путь к JSON файлу с семьями
    json_file_path = "files for fill queue/completed/14.01.2026_completed_families.json"
    
    if not os.path.exists(json_file_path):
        print(f"❌ Файл с семьями {json_file_path} не найден")
        # Попробуем найти любой файл с completed в названии
        import glob
        completed_files = glob.glob("files for fill queue/completed/*completed_families.json")
        if completed_files:
            json_file_path = completed_files[0]
            print(f"🔄 Используем {json_file_path} как файл с семьями")
        else:
            print("❌ Не найдено ни одного файла с семьями")
            return False
    
    # Используем функцию с автоматической подстановкой ID таблицы
    success = interactive_check_existing_colors_and_highlight_with_auto_config(
        credentials_file=credentials_file,
        json_file_path=json_file_path,
        sheet_name="АСП_Многодетные"
    )
    
    if success:
        print("✅ Процесс завершен успешно!")
    else:
        print("❌ Произошла ошибка в процессе выполнения")
    
    return success


if __name__ == "__main__":
    main()