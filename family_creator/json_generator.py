"""Модуль для генерации JSON файлов с семьями"""

import json
import os
from datetime import datetime
from utils.data_processing import clean_family_data
from utils.validation import validate_family_data
from utils.file_utils import setup_config_directory


class JSONFamilyCreator:
    def __init__(self):
        self.families = []
        self.current_family_index = 0
        self.current_file_path = None
        self.last_json_directory = None
        self.last_adpi_directory = None
        self.last_register_directory = None
        self.adpi_data = {}
        self.register_data = {}
        self.processed_families = set()
        
        # Организация конфигурационных файлов в отдельную папку
        self.setup_config_directory()
        
        # Автосохранение
        self.autosave_filename = os.path.join(self.config_dir, "autosave_families.json")
        self.load_on_startup = True
        
        # Константа для единого пособия
        self.BASE_UNIFIED_BENEFIT = 17000
        
        # Конфигурационный файл
        self.config_file = os.path.join(self.config_dir, "family_creator_config.json")
        self.config = self.load_config()
    
    def setup_config_directory(self):
        """Создание папки для конфигурационных файлов"""
        try:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir, self.screenshots_dir, _ = setup_config_directory(app_dir)
                
        except Exception as e:
            print(f"❌ Ошибка создания папки конфигурации: {e}")
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
            self.screenshots_dir = self.config_dir
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
        default_config = {
            "last_json_directory": "",
            "last_adpi_directory": "",
            "last_register_directory": ""
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.last_json_directory = config.get("last_json_directory", "")
                    self.last_adpi_directory = config.get("last_adpi_directory", "")
                    self.last_register_directory = config.get("last_register_directory", "")
                    return config
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return default_config
        return default_config
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            config = {
                "last_json_directory": self.last_json_directory,
                "last_adpi_directory": self.last_adpi_directory,
                "last_register_directory": self.last_register_directory
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def autosave_families(self):
        """Автосохранение списка семей в файл"""
        if not self.families:
            return
        try:
            cleaned_families = [clean_family_data(family) for family in self.families]
            with open(self.autosave_filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_families, f, ensure_ascii=False, indent=2)
            print(f"✅ Автосохранение выполнено: {len(self.families)} семей")
        except Exception as e:
            print(f"❌ Ошибка автосохранения: {e}")
    
    def save_to_json(self, file_path=None):
        """Сохранение списка семей в JSON файл"""
        if not self.families:
            print("⚠️ Список семей пуст")
            return False
        
        if not file_path:
            print("⚠️ Не указан путь к файлу")
            return False
        
        try:
            self.last_json_directory = os.path.dirname(file_path)
            self.save_config()
            
            cleaned_families = [clean_family_data(family) for family in self.families]
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(cleaned_families, file, ensure_ascii=False, indent=2)
            
            self.current_file_path = file_path
            
            print(f"✅ Файл сохранен успешно!\n{file_path}\nСемей: {len(self.families)}")
            return True
        except Exception as e:
            print(f"❌ Не удалось сохранить файл: {str(e)}")
            return False
    
    def load_from_json(self, file_path=None):
        """Загрузка JSON файла"""
        if not file_path:
            print("⚠️ Не указан путь к файлу")
            return False
        
        try:
            self.last_json_directory = os.path.dirname(file_path)
            self.save_config()
            
            with open(file_path, 'r', encoding='utf-8') as file:
                loaded_families = json.load(file)
            
            if not isinstance(loaded_families, list):
                print("❌ JSON файл должен содержать массив семей")
                return False
            
            loaded_families = [clean_family_data(family) for family in loaded_families]
            
            if self.families:
                print(f"Найдено {len(loaded_families)} семей в файле.")
                print(f"В текущем списке {len(self.families)} семей.")
                # В реальном приложении здесь будет диалог с пользователем
                # Пока просто добавим к существующему списку
                self.families.extend(loaded_families)
                print(f"Семьи добавлены. Теперь {len(self.families)} семей")
            else:
                self.families = loaded_families
                print(f"Загружено {len(self.families)} семей")
            
            self.current_file_path = file_path
            
            self.autosave_families()
            
            if self.families:
                cleaned_family = clean_family_data(self.families[0])
                self.current_family_index = 0
            
            return True
        except Exception as e:
            print(f"❌ Не удалось загрузить файл: {str(e)}")
            return False
    
    def add_family(self, family_data):
        """Добавление семьи в список"""
        errors = validate_family_data(family_data)
        if errors:
            print("❌ Ошибки валидации:", errors)
            return False
        
        # Проверяем, есть ли уже такая семья в списке
        for i, existing_family in enumerate(self.families):
            if existing_family.get('mother_fio') == family_data.get('mother_fio'):
                print(f"Семья с матерью {family_data.get('mother_fio')} уже есть в списке.")
                # В реальном приложении здесь будет диалог с пользователем
                # Пока просто заменим
                self.families[i] = family_data
                print("Семья обновлена в списке")
                self.autosave_families()
                return True
        
        self.families.append(family_data)
        print(f"Семья добавлена в список. Всего семей: {len(self.families)}")
        self.autosave_families()
        return True
    
    def get_family(self, index):
        """Получение семьи по индексу"""
        if 0 <= index < len(self.families):
            return self.families[index]
        return None
    
    def get_families_count(self):
        """Получение количества семей"""
        return len(self.families)
    
    def remove_family(self, index):
        """Удаление семьи по индексу"""
        if 0 <= index < len(self.families):
            removed_family = self.families.pop(index)
            print(f"Семья удалена: {removed_family.get('mother_fio', 'Без имени')}")
            print(f"Осталось семей: {len(self.families)}")
            self.autosave_families()
            return True
        return False
    
    def clear_families(self):
        """Очистка списка семей"""
        self.families = []
        self.current_family_index = 0
        print("Список семей очищен")
        self.autosave_families()
    
    def calculate_unified_benefit(self, children_count, percentage_str):
        """Расчет единого пособия"""
        try:
            children_count = int(children_count)
            if children_count <= 0:
                return None
            
            percentage = float(percentage_str.replace('%', '')) / 100
            
            benefit_per_child = self.BASE_UNIFIED_BENEFIT * percentage
            total_benefit = benefit_per_child * children_count
            
            total_benefit = round(total_benefit)
            
            return total_benefit
        except ValueError:
            return None