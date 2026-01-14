#!/usr/bin/env python3
"""Модуль для управления конфигурацией приложения"""

import json
import os
from typing import Dict, Optional


class ConfigManager:
    """Класс для управления конфигурацией приложения"""
    
    def __init__(self, config_file_path: str = "config.json"):
        """
        Инициализация менеджера конфигурации
        
        Args:
            config_file_path: Путь к файлу конфигурации
        """
        self.config_file_path = config_file_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """
        Загрузка конфигурации из файла
        
        Returns:
            Словарь с конфигурацией
        """
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки конфигурации: {e}")
                return {}
        return {}
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True) if os.path.dirname(self.config_file_path) else None
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"✅ Конфигурация сохранена в {self.config_file_path}")
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
    
    def get_spreadsheet_id(self, default_sheet_name: str = "АСП_Многодетные") -> Optional[str]:
        """
        Получение ID таблицы из конфигурации
        
        Args:
            default_sheet_name: Название листа по умолчанию
            
        Returns:
            ID таблицы или None
        """
        return self.config.get('spreadsheet_ids', {}).get(default_sheet_name)
    
    def set_spreadsheet_id(self, sheet_name: str, spreadsheet_id: str):
        """
        Сохранение ID таблицы в конфигурацию
        
        Args:
            sheet_name: Название листа
            spreadsheet_id: ID электронной таблицы
        """
        if 'spreadsheet_ids' not in self.config:
            self.config['spreadsheet_ids'] = {}
        
        self.config['spreadsheet_ids'][sheet_name] = spreadsheet_id
        self.save_config()
    
    def get_credentials_file(self) -> Optional[str]:
        """
        Получение пути к файлу учетных данных
        
        Returns:
            Путь к файлу учетных данных или None
        """
        return self.config.get('credentials_file')
    
    def set_credentials_file(self, credentials_file: str):
        """
        Сохранение пути к файлу учетных данных
        
        Args:
            credentials_file: Путь к файлу учетных данных
        """
        self.config['credentials_file'] = credentials_file
        self.save_config()


def get_default_config_manager() -> ConfigManager:
    """Получение экземпляра менеджера конфигурации с путем по умолчанию"""
    return ConfigManager("config/app_config.json")


class ConfigManager:
    """Класс для управления конфигурацией приложения"""
    
    def __init__(self, config_file_path: str = "config.json"):
        """
        Инициализация менеджера конфигурации
        
        Args:
            config_file_path: Путь к файлу конфигурации
        """
        self.config_file_path = config_file_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """
        Загрузка конфигурации из файла
        
        Returns:
            Словарь с конфигурацией
        """
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки конфигурации: {e}")
                return {}
        return {}
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True) if os.path.dirname(self.config_file_path) else None
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"✅ Конфигурация сохранена в {self.config_file_path}")
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
    
    def get_spreadsheet_id(self, default_sheet_name: str = "АСП_Многодетные") -> Optional[str]:
        """
        Получение ID таблицы из конфигурации
        
        Args:
            default_sheet_name: Название листа по умолчанию
            
        Returns:
            ID таблицы или None
        """
        return self.config.get('spreadsheet_ids', {}).get(default_sheet_name)
    
    def set_spreadsheet_id(self, sheet_name: str, spreadsheet_id: str):
        """
        Сохранение ID таблицы в конфигурацию
        
        Args:
            sheet_name: Название листа
            spreadsheet_id: ID электронной таблицы
        """
        if 'spreadsheet_ids' not in self.config:
            self.config['spreadsheet_ids'] = {}
        
        self.config['spreadsheet_ids'][sheet_name] = spreadsheet_id
        self.save_config()
    
    def get_credentials_file(self) -> Optional[str]:
        """
        Получение пути к файлу учетных данных
        
        Returns:
            Путь к файлу учетных данных или None
        """
        return self.config.get('credentials_file')
    
    def set_credentials_file(self, credentials_file: str):
        """
        Сохранение пути к файлу учетных данных
        
        Args:
            credentials_file: Путь к файлу учетных данных
        """
        self.config['credentials_file'] = credentials_file
        self.save_config()
    
    def get_sheet_name(self, default_sheet_name: str = "АСП_Многодетные") -> Optional[str]:
        """
        Получение названия листа из конфигурации
        
        Args:
            default_sheet_name: Название листа по умолчанию
            
        Returns:
            Название листа или None
        """
        return self.config.get('sheet_names', {}).get(default_sheet_name, default_sheet_name)

    def set_sheet_name(self, original_name: str, new_name: str):
        """
        Сохранение названия листа в конфигурацию
        
        Args:
            original_name: Оригинальное название листа
            new_name: Новое название листа для сохранения
        """
        if 'sheet_names' not in self.config:
            self.config['sheet_names'] = {}
        
        self.config['sheet_names'][original_name] = new_name
        self.save_config()


if __name__ == "__main__":
    # Пример использования
    config_manager = get_default_config_manager()
    
    # Установка ID таблицы
    config_manager.set_spreadsheet_id("АСП_Многодетные", "1REAUDJZCLqu7Vn_UcIGiVG9CqPWpNnGrD-luCIrDz2c")
    
    # Установка названия листа
    config_manager.set_sheet_name("АСП_Многодетные", "Список граждан (Лист 1)")
    
    # Получение ID таблицы
    spreadsheet_id = config_manager.get_spreadsheet_id("АСП_Многодетные")
    print(f"ID таблицы: {spreadsheet_id}")
    
    # Получение названия листа
    sheet_name = config_manager.get_sheet_name("АСП_Многодетные")
    print(f"Название листа: {sheet_name}")