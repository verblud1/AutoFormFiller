#!/usr/bin/env python3
"""Модуль для управления конфигурацией приложения"""

import json
import os
from typing import Dict


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


def get_default_config_manager() -> ConfigManager:
    """Получение экземпляра менеджера конфигурации с путем по умолчанию"""
    return ConfigManager("config/app_config.json")
