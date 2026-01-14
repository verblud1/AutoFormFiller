import customtkinter as ctk
from tkinter import messagebox, scrolledtext, filedialog
import threading
import json
from datetime import datetime
import os
import re
import shutil
import traceback
import pandas as pd
import numpy as np
from dateutil import parser
import subprocess
import platform

class EnhancedJSONFamilyCreatorGUI:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("📝 Улучшенный создатель JSON файлов для семей")
        self.app.geometry("1400x900")
        self.app.resizable(True, True)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
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
        self.setup_ui()
        
        # Обязательная загрузка JSON при запуске
        if self.load_on_startup:
            self.load_json_on_startup()
        
        # Загрузка последних файлов реестра и АДПИ при запуске
        self.load_last_files()
    
    def setup_config_directory(self):
        """Создание папки для конфигурационных файлов"""
        try:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir = os.path.join(app_dir, "config")
            
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                print(f"✅ Создана папка конфигурации: {self.config_dir}")
            
            # Динамическое определение папки registry относительно текущего файла
            self.registry_dir = self.find_registry_directory(app_dir)
            if not os.path.exists(self.registry_dir):
                os.makedirs(self.registry_dir)
                print(f"✅ Создана папка registry: {self.registry_dir}")
            else:
                print(f"✅ Найдена папка registry: {self.registry_dir}")
            
            self.screenshots_dir = os.path.join(self.config_dir, "screenshots")
            if not os.path.exists(self.screenshots_dir):
                os.makedirs(self.screenshots_dir)
                print(f"✅ Создана папка для скриншотов: {self.screenshots_dir}")
                
            # Используем папки installer для хранения файлов
            installer_dir = os.path.dirname(app_dir)
            self.register_dir = installer_dir
            self.adpi_dir = installer_dir
                
        except Exception as e:
            print(f"❌ Ошибка создания папки конфигурации: {e}")
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
            self.screenshots_dir = self.config_dir
            installer_dir = os.path.dirname(self.config_dir)
            self.registry_dir = self.find_registry_directory(self.config_dir)
            self.register_dir = installer_dir
            self.adpi_dir = installer_dir
    
    def find_registry_directory(self, start_dir):
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
    
    def check_registry_files(self):
        """Проверка наличия файлов в папке registry и запрос на подгрузку"""
        try:
            registry_files = [f for f in os.listdir(self.registry_dir) if f.lower().endswith(('.xls', '.xlsx', '.ods'))]
            if len(registry_files) == 2:
                # Если есть два файла в папке registry, спрашиваем пользователя
                from tkinter import messagebox
                result = messagebox.askyesno("Подгрузка файлов",
                                          f"Найдено 2 файла в папке registry:\n{registry_files[0]}\n{registry_files[1]}\n\nПодгрузить из папки?")
                if result:
                    # Подгружаем два файла с соответствующей структурой
                    return self.load_registry_files(registry_files)
            return False
        except Exception as e:
            print(f"Ошибка проверки файлов в registry: {e}")
            return False
    
    def load_registry_files(self, registry_files):
        """Загрузка файлов из папки registry с определением их типа по структуре"""
        try:
            
            
            # Определяем типы файлов по заголовкам
            register_file = None
            adpi_file = None
            files_processed = {}
            
            for file in registry_files:
                file_path = os.path.join(self.registry_dir, file)
                try:
                    # Определяем формат файла
                    if file.lower().endswith('.xls'):
                        df = pd.read_excel(file_path, header=None, engine='xlrd')
                    else:
                        df = pd.read_excel(file_path, header=None)
                    
                    # Проверяем, является ли это файлом реестра многодетных
                    if not df.empty:
                        first_row = df.iloc[0] if len(df) > 0 else pd.Series()
                        # Проверяем наличие характерных заголовков реестра многодетных
                        registry_headers = ['№ п/п', 'Фамилия', 'Имя', 'Отчество', 'Дата рождения', 'Район', 'регион', 'Адрес', 'Населенный пункт', 'Улица', 'Дом', 'корпус', 'квартира', 'Тел', 'Фамилия чл. семьи', 'Имя чл. семьи', 'Отчество чл. семьи', 'Дата рождения 2', 'Детей в семье']
                        registry_matches = sum(1 for header in registry_headers if any(str(header).lower() in str(cell).lower() for cell in first_row if pd.notna(cell)))
                        
                        # Проверяем, является ли это файлом АДПИ
                        # Учитываем полную структуру заголовка АДПИ: "№ п/п	ФИО	Кол-во детей до 18 лет	Адрес проживания (установка АДПИ)	Кол-во и марка (модель) установленных АДПИ 		Дата установки	Дата проверки работоспособности	Комментарии (исправен, неисправен/заме-нен и т.п.)	Элименты питания, шт.	Дата выдачи 		Комментарии о семье 	Примечание"
                        adpi_headers = ['ФИО', 'Кол-во детей', 'Адрес проживания', 'установка АДПИ', 'марка', 'модель', 'установки', 'работоспособности', 'Элименты питания', 'элементы питания', 'Дата установки', 'Дата проверки', 'Комментарии', 'Примечание']
                        adpi_matches = sum(1 for header in adpi_headers if any(str(header).lower() in str(cell).lower() for cell in first_row if pd.notna(cell)))
                        
                        print(f"Анализ файла {file}: реестр_многодетных={registry_matches}, адпи={adpi_matches}")
                        
                        if registry_matches > adpi_matches:
                            register_file = file_path
                            files_processed[file] = 'register'
                            print(f"Файл {file} определен как реестр многодетных")
                        elif adpi_matches > registry_matches:
                            adpi_file = file_path
                            files_processed[file] = 'adpi'
                            print(f"Файл {file} определен как АДПИ")
                        else:
                            # Если неясно, пробуем определить по содержимому
                            if len(df.columns) >= 15 and any('Фамилия' in str(col) for col in first_row[:10] if pd.notna(col)):
                                register_file = file_path
                                files_processed[file] = 'register'
                                print(f"Файл {file} определен как реестр многодетных по колонкам")
                            elif len(df.columns) >= 10 and any('ФИО' in str(col) for col in first_row[:5] if pd.notna(col)):
                                adpi_file = file_path
                                files_processed[file] = 'adpi'
                                print(f"Файл {file} определен как АДПИ по колонкам")
                            else:
                                # Если по-прежнему неясно, проверим другие признаки
                                # Для АДПИ часто есть колонки с упоминанием "АДПИ", "установки", "работоспособности", "элементы питания"
                                content_text = ' '.join([str(cell) for cell in first_row if pd.notna(cell)])
                                if any(keyword in content_text.lower() for keyword in ['адпи', 'установки', 'работоспособности', 'элементы питания', 'элименты питания', 'установк', 'проверк', 'марка', 'модель']):
                                    adpi_file = file_path
                                    files_processed[file] = 'adpi'
                                    print(f"Файл {file} определен как АДПИ по ключевым словам")
                                elif any(keyword in content_text.lower() for keyword in ['фамилия', 'имя', 'отчество', 'дата рождения', 'детей в семье']):
                                    register_file = file_path
                                    files_processed[file] = 'register'
                                    print(f"Файл {file} определен как реестр многодетных по ключевым словам")
                                else:
                                    # Если не удалось определить тип файла, сохраняем для последующей обработки
                                    files_processed[file] = 'unknown'
                                    print(f"Файл {file} не определен, отложен для обработки")
                except Exception as e:
                    print(f"Ошибка анализа файла {file}: {e}")
                    continue
            
            # Если один файл определен, а другой остался неопределенным, назначаем второй файл как оставшийся тип
            if len(files_processed) == 2:
                processed_types = list(files_processed.values())
                if 'register' in processed_types and 'adpi' not in processed_types and 'unknown' in processed_types:
                    # Назначаем оставшийся файл как adpi
                    for file in registry_files:
                        if files_processed[file] == 'unknown':
                            file_path = os.path.join(self.registry_dir, file)
                            adpi_file = file_path
                            files_processed[file] = 'adpi'
                            print(f"Неопределенный файл {file} назначен как АДПИ")
                elif 'adpi' in processed_types and 'register' not in processed_types and 'unknown' in processed_types:
                    # Назначаем оставшийся файл как register
                    for file in registry_files:
                        if files_processed[file] == 'unknown':
                            file_path = os.path.join(self.registry_dir, file)
                            register_file = file_path
                            files_processed[file] = 'register'
                            print(f"Неопределенный файл {file} назначен как реестр многодетных")
            
            # Выводим итоговую информацию
            print(f"Итог: register_file = {register_file is not None}, adpi_file = {adpi_file is not None}")
            
            # Загружаем определенные файлы
            if register_file:
                self.load_register_file(register_file, auto_load=True)
                print(f"✅ Загружен файл реестра из registry: {os.path.basename(register_file)}")
            
            if adpi_file:
                self.load_adpi_xlsx(adpi_file, auto_load=True)
                print(f"✅ Загружен файл АДПИ из registry: {os.path.basename(adpi_file)}")
                
                # После загрузки АДПИ, если уже введены данные о семье, автоматически заполняем АДПИ
                mother_fio = self.mother_fio.get().strip()
                father_fio = self.father_fio.get().strip()
                if mother_fio or father_fio:
                    self.fill_adpi_from_loaded_data()
            else:
                print("⚠️ Файл АДПИ не найден или не определен в папке registry")
            
            return True
        except Exception as e:
            print(f"Ошибка загрузки файлов из registry: {e}")
            return False
    
    def load_last_files(self):
        """Загрузка последних файлов реестра и АДПИ при запуске"""
        # Проверяем наличие файлов в папке registry
        if self.check_registry_files():
            print("✅ Файлы из папки registry успешно загружены")
            return
        
        # Ищем последний файл реестра
        register_files = [f for f in os.listdir(self.register_dir) if f.lower().endswith(('.xls', '.xlsx'))]
        if register_files:
            # Берем последний измененный файл
            register_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.register_dir, x)), reverse=True)
            last_register = os.path.join(self.register_dir, register_files[0])
            self.load_register_file(last_register, auto_load=True)
        
        # Ищем последний файл АДПИ
        adpi_files = [f for f in os.listdir(self.adpi_dir) if f.lower().endswith(('.xls', '.xlsx', '.ods'))]
        if adpi_files:
            adpi_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.adpi_dir, x)), reverse=True)
            last_adpi = os.path.join(self.adpi_dir, adpi_files[0])
            self.load_adpi_xlsx(last_adpi, auto_load=True)
    
    
    def clean_string(self, text):
        """Очистка строки от специальных символов и нормализация пробелов"""
        if not isinstance(text, str):
            return text
        text = re.sub(r'[\t\n\r\x0b\x0c]+', ' ', text)
        text = ' '.join(text.split())
        text = re.sub(r'[;.]+$', '', text)
        text = re.sub(r'\.\.+', '.', text)
        text = re.sub(r',,+', ',', text)
        text = re.sub(r'\s+([.,;])', r'\1', text)
        text = re.sub(r',\s*,', ',', text)
        return text.strip()
    
    def clean_fio(self, fio):
        """Очистка и нормализация ФИО"""
        if not isinstance(fio, str):
            return fio
        fio = self.clean_string(fio)
        parts = fio.split()
        if len(parts) == 3:
            parts = [part.capitalize() for part in parts]
            return ' '.join(parts)
        return fio
    
    def clean_address(self, address):
        """Очистка и нормализация адреса"""
        if not isinstance(address, str):
            return address
        address = self.clean_string(address)
        address = re.sub(r'г\.\s*,', 'г. ', address)
        address = re.sub(r'ул\.\s*,', 'ул. ', address)
        address = re.sub(r'д\.\s*,', 'д. ', address)
        address = re.sub(r'кв\.\s*,', 'кв. ', address)
        address = re.sub(r'\.(\s*\.)+', '.', address)
        address = re.sub(r'д\.\s*д\.', 'д.', address)
        address = re.sub(r',\s*(\d+[а-я]*)', r', \1', address)
        return address
    
    def clean_date(self, date_str):
            """Очистка и валидация даты - ИСПРАВЛЕНА ОБРАБОТКА ФОРМАТА MM/DD/YYYY"""
            if not isinstance(date_str, str):
                return date_str
            
            date_str = self.clean_string(date_str)
            
            # Обработка ошибки с датой в формате 28.12.202026 (оставляем первые 4 числа года)
            # Находим паттерн DD.MM.YYYY где YYYY содержит больше 4 цифр
            pattern = r'(\d{1,2}\.\d{1,2}\.)(\d{4})\d+'
            match = re.match(pattern, date_str)
            if match:
                day_month = match.group(1)
                year = match.group(2)
                corrected_date = day_month + year
                return corrected_date
            
            # Обработка формата MM/DD/YYYY или M/D/YYYY
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    try:
                        month, day, year = map(int, parts)
                        # Проверяем валидность
                        if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= datetime.now().year:
                            # Преобразуем в DD.MM.YYYY
                            return f"{day:02d}.{month:02d}.{year}"
                    except:
                        pass
            
            # Обработка формата DD.MM.YYYY
            if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', date_str):
                try:
                    day, month, year = map(int, date_str.split('.'))
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= datetime.now().year:
                        return f"{day:02d}.{month:02d}.{year}"
                except:
                    pass
            
            # Обработка двух дат в одной строке (например: 28.01.2024.21.05.2025)
            if date_str.count('.') >= 5:
                parts = date_str.split('.')
                if len(parts) >= 6:
                    try:
                        # Пробуем получить две даты
                        date1_str = f"{parts[0]}.{parts[1]}.{parts[2]}"
                        date2_str = f"{parts[3]}.{parts[4]}.{parts[5]}"
                        
                        date1 = datetime.strptime(date1_str, '%d.%m.%Y')
                        date2 = datetime.strptime(date2_str, '%d.%m.%Y')
                        
                        # Берем более позднюю дату
                        if date1 > date2:
                            return date1_str
                        else:
                            return date2_str
                    except:
                        pass
            
            # Убираем все лишние символы, кроме цифр и точек и слэшей
            date_str = re.sub(r'[^\d./]+', '', date_str)
            
            return date_str
    
    def clean_phone(self, phone):
        """Очистка и форматирование телефона"""
        if not isinstance(phone, str):
            return phone
        digits = re.sub(r'\D', '', phone)
        if not digits:
            return ""
        if digits.startswith('9') and len(digits) == 10:
            return '7' + digits
        elif digits.startswith('8') and len(digits) == 11:
            return '7' + digits[1:]
        elif digits.startswith('7') and len(digits) == 11:
            return digits
        elif len(digits) == 10:
            return '7' + digits
        else:
            return digits
    
    def clean_numeric_field(self, value):
        """Очистка числовых полей"""
        if not isinstance(value, str):
            return value
        cleaned = re.sub(r'[^\d.,]', '', value)
        cleaned = cleaned.replace(',', '.')
        parts = cleaned.split('.')
        if len(parts) > 1:
            cleaned = parts[0] + '.' + ''.join(parts[1:])
        return cleaned if cleaned else value
    
    def clean_family_data(self, family_data):
        """Очистка всех данных семьи"""
        if not isinstance(family_data, dict):
            return family_data
        cleaned_data = {}
        for key, value in family_data.items():
            if isinstance(value, str):
                if 'fio' in key.lower():
                    cleaned_data[key] = self.clean_fio(value)
                elif 'address' in key.lower():
                    cleaned_data[key] = self.clean_address(value)
                elif 'birth' in key.lower():
                    cleaned_data[key] = self.clean_date(value)
                elif 'phone' in key.lower() or 'tel' in key.lower():
                    cleaned_data[key] = self.clean_phone(value)
                elif 'date' in key.lower():
                    cleaned_data[key] = self.clean_date(value)
                elif any(x in key.lower() for x in ['salary', 'benefit', 'pension', 'alimony', 'rooms', 'square']):
                    cleaned_data[key] = self.clean_numeric_field(value)
                elif 'education' in key.lower() or 'work' in key.lower() or 'amenities' in key.lower() or 'ownership' in key.lower():
                    cleaned_data[key] = self.clean_string(value)
                else:
                    cleaned_data[key] = self.clean_string(value)
            elif isinstance(value, list) and key == 'children':
                cleaned_children = []
                for child in value:
                    if isinstance(child, dict):
                        cleaned_child = {}
                        for child_key, child_value in child.items():
                            if isinstance(child_value, str):
                                if 'fio' in child_key.lower():
                                    cleaned_child[child_key] = self.clean_fio(child_value)
                                elif 'birth' in child_key.lower():
                                    cleaned_child[child_key] = self.clean_date(child_value)
                                elif 'education' in child_key.lower():
                                    cleaned_child[child_key] = self.clean_string(child_value)
                                else:
                                    cleaned_child[child_key] = self.clean_string(child_value)
                            else:
                                cleaned_child[child_key] = child_value
                        cleaned_children.append(cleaned_child)
                cleaned_data[key] = cleaned_children
            else:
                cleaned_data[key] = value
        return cleaned_data
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
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
                return {}
        return {}
    
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
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        self.auto_tab = self.tabview.add("🤖 Автоопределение")
        self.family_tab = self.tabview.add("👨‍👩‍👧‍👦 Семья")
        self.children_tab = self.tabview.add("👶 Дети")
        self.housing_tab = self.tabview.add("🏠 Жилье")
        self.income_tab = self.tabview.add("💰 Доходы")
        self.adpi_tab = self.tabview.add("📟 АДПИ")
        self.manage_tab = self.tabview.add("📋 Управление")
        self.setup_auto_tab()
        self.setup_family_tab()
        self.setup_children_tab()
        self.setup_housing_tab()
        self.setup_income_tab()
        self.setup_adpi_tab()
        self.setup_manage_tab()
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Добавляем поддержку прокрутки колесиком мыши для всех вкладок
        self.setup_mouse_wheel_binding()
        
        # Улучшаем видимость полос прокрутки
        self.setup_scrollbar_visibility()
    
    def setup_scrollbar_visibility(self):
        """Улучшение видимости полос прокрутки"""
        # Настройка стиля полос прокрутки для лучшей видимости
        try:
            # Попытка настроить видимость полос прокрутки в CTk
            ctk.set_widget_scaling(1.0)  # Устанавливаем масштаб виджетов
        except:
            pass
        
        # Обновляем все виджеты для лучшей видимости полос прокрутки
        self.app.update_idletasks()
    
    def setup_mouse_wheel_binding(self):
        """Настройка прокрутки колесиком мыши для всех вкладок"""
        # Привязываем прокрутку к основному окну
        self.app.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        self.app.bind("<Button-4>", self._on_mousewheel)    # Linux
        self.app.bind("<Button-5>", self._on_mousewheel)    # Linux
        
        # Привязываем к дочерним виджетам (без tabview, так как он не поддерживает bind)
        for tab_name in ["auto_tab", "family_tab", "children_tab", "housing_tab", "income_tab", "adpi_tab", "manage_tab"]:
            if hasattr(self, tab_name):
                tab = getattr(self, tab_name)
                try:
                    tab.bind("<MouseWheel>", self._on_mousewheel)
                    tab.bind("<Button-4>", self._on_mousewheel)
                    tab.bind("<Button-5>", self._on_mousewheel)
                except:
                    # Некоторые виджеты могут не поддерживать bind
                    pass
                
                # Рекурсивно привязываем ко всем дочерним элементам
                self._bind_mousewheel_recursive(tab, self._on_mousewheel)
    
    def _bind_mousewheel_recursive(self, widget, callback):
        """Рекурсивная привязка события прокрутки ко всем дочерним виджетам"""
        try:
            for child in widget.winfo_children():
                try:
                    child.bind("<MouseWheel>", callback)  # Windows
                    child.bind("<Button-4>", callback)    # Linux
                    child.bind("<Button-5>", callback)    # Linux
                except:
                    # Некоторые виджеты могут не поддерживать bind
                    pass
                # Рекурсивный вызов для вложенных виджетов
                self._bind_mousewheel_recursive(child, callback)
        except:
            # Некоторые виджеты могут не поддерживать winfo_children()
            pass
    
    def _on_mousewheel(self, event):
        """Обработка события прокрутки колесиком мыши"""
        # Определяем направление прокрутки в зависимости от ОС
        if event.num == 4 or event.delta > 0:
            direction = -1  # Вверх
        elif event.num == 5 or event.delta < 0:
            direction = 1   # Вниз
        else:
            return
        
        # Находим виджет, над которым находится курсор
        widget = event.widget
        self._scroll_widget_if_scrollable(widget, direction)
    
    def _scroll_widget_if_scrollable(self, widget, direction):
        """Прокрутка виджета, если он поддерживает прокрутку"""
        # Проверяем, является ли виджет прокручиваемым фреймом
        if hasattr(widget, 'yview') and callable(getattr(widget, 'yview', None)):
            # Это может быть Text, Listbox, Canvas или виджет с прокруткой
            try:
                if direction == -1:
                    widget.yview_scroll(-1, "units")
                else:
                    widget.yview_scroll(1, "units")
            except:
                pass
        elif widget.__class__.__name__ in ['CTkScrollableFrame']:
            # Обработка CTkScrollableFrame - ищем внутренний canvas и прокручиваем его
            try:
                # Прокручиваем сам фрейм
                if direction == -1:
                    widget._parent_canvas.yview_scroll(-1, "units")
                else:
                    widget._parent_canvas.yview_scroll(1, "units")
            except:
                # Если прямой доступ не работает, пробуем рекурсивно найти canvas
                canvas = self._find_canvas_in_widget(widget)
                if canvas:
                    try:
                        if direction == -1:
                            canvas.yview_scroll(-1, "units")
                        else:
                            canvas.yview_scroll(1, "units")
                    except:
                        pass
        
        # Рекурсивно проверяем родительские виджеты
        parent = widget.master if hasattr(widget, 'master') else None
        if parent and parent != self.app:
            self._scroll_widget_if_scrollable(parent, direction)
    
    def _find_canvas_in_widget(self, widget):
        """Поиск canvas внутри виджета для прокрутки"""
        try:
            # Проверяем, есть ли у виджета _parent_canvas
            if hasattr(widget, '_parent_canvas'):
                return widget._parent_canvas
            # Ищем canvas рекурсивно среди дочерних элементов
            for child in widget.winfo_children():
                if child.__class__.__name__ in ['Canvas', 'tkinter.Canvas', 'customtkinter.CTkCanvas']:
                    return child
                canvas = self._find_canvas_in_widget(child)
                if canvas:
                    return canvas
        except:
            pass
        return None
    
    def _get_all_children(self, widget):
        """Получение всех дочерних виджетов рекурсивно"""
        children = [widget]
        for child in widget.winfo_children():
            children.extend(self._get_all_children(child))
        return children
    
    def on_closing(self):
        """Обработка закрытия программы"""
        if self.families:
            response = messagebox.askyesnocancel(
                "Подтверждение выхода",
                "Есть несохраненные данные. Вы хотите сохранить их перед выходом?\n"
                "Да - сохранить и выйти\n"
                "Нет - выйти без сохранения\n"
                "Отмена - остаться в программе"
            )
            if response is None:
                return
            elif response:
                self.save_to_json()
                if messagebox.askyesno("Выход", "Выйти из программы?"):
                    self.save_config()
                    self.autosave_families()
                    self.app.quit()
            else:
                if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти без сохранения?"):
                    self.save_config()
                    self.autosave_families()
                    self.app.quit()
        else:
            if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
                self.save_config()
                self.app.quit()
    
    def load_json_on_startup(self):
        """Загрузка JSON файла при запуске программы"""
        if os.path.exists(self.autosave_filename):
            try:
                with open(self.autosave_filename, 'r', encoding='utf-8') as f:
                    loaded_families = json.load(f)
                if isinstance(loaded_families, list) and loaded_families:
                    loaded_families = [self.clean_family_data(family) for family in loaded_families]
                    self.families = loaded_families
                    self.update_families_info()
                    messagebox.showinfo("Автозагрузка", 
                                      f"Загружено {len(self.families)} семей из автосохранения")
                    return True
            except Exception as e:
                print(f"Ошибка загрузки автосохранения: {e}")
        
        initial_dir = self.last_json_directory if self.last_json_directory else None
        file_path = filedialog.askopenfilename(
            title="📂 ОБЯЗАТЕЛЬНО: Выберите JSON файл с семьями",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if not file_path:
            if messagebox.askyesno("Внимание", 
                                 "JSON файл не выбран. Без загрузки данных работа невозможна.\n"
                                 "Продолжить без загрузки данных? (Это создаст пустой список семей)"):
                return True
            else:
                messagebox.showwarning("Выход", "Программа будет закрыта. Запустите снова и выберите JSON файл.")
                self.app.quit()
                return False
        try:
            self.last_json_directory = os.path.dirname(file_path)
            self.save_config()
            with open(file_path, 'r', encoding='utf-8') as file:
                loaded_families = json.load(file)
            if not isinstance(loaded_families, list):
                messagebox.showerror("Ошибка", "JSON файл должен содержать массив семей")
                return False
            loaded_families = [self.clean_family_data(family) for family in loaded_families]
            self.families = loaded_families
            self.current_file_path = file_path
            self.update_families_info()
            messagebox.showinfo("Успех", f"Загружено {len(self.families)} семей из файла")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")
            if messagebox.askyesno("Повторить", "Хотите выбрать другой файл?"):
                return self.load_json_on_startup()
            else:
                messagebox.showwarning("Выход", "Программа будет закрыта.")
                self.app.quit()
                return False
    
    def autosave_families(self):
        """Автосохранение списка семей в файл"""
        if not self.families:
            return
        try:
            cleaned_families = [self.clean_family_data(family) for family in self.families]
            with open(self.autosave_filename, 'w', encoding='utf-8') as f:
                json.dump(cleaned_families, f, ensure_ascii=False, indent=2)
            print(f"✅ Автосохранение выполнено: {len(self.families)} семей")
        except Exception as e:
            print(f"❌ Ошибка автосохранения: {e}")
    
    def setup_auto_tab(self):
        """Вкладка автоопределения и загрузки данных"""
        main_frame = ctk.CTkFrame(self.auto_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Блок автоопределения семьи
        auto_frame = ctk.CTkFrame(main_frame)
        auto_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(auto_frame, text="🤖 АВТООПРЕДЕЛЕНИЕ СЕМЬИ", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        ctk.CTkLabel(auto_frame, 
                    text="Введите ФИО матери или отца для поиска в реестре:").pack(anchor="w", padx=5)
        
        search_frame = ctk.CTkFrame(auto_frame)
        search_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(search_frame, text="ФИО:").pack(side="left", padx=5)
        self.search_fio_input = ctk.CTkEntry(search_frame, width=300, 
                                        placeholder_text="Например: Демичева Анастасия Евгеньевна")
        self.search_fio_input.pack(side="left", padx=5)
        
        # Блок загрузки реестра
        register_frame = ctk.CTkFrame(main_frame)
        register_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(register_frame, text="📋 ЗАГРУЗКА РЕЕСТРА МНОГОДЕТНЫХ", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Информация о последнем файле
        if self.last_register_directory:
            file_info_frame = ctk.CTkFrame(register_frame)
            file_info_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(file_info_frame, 
                        text=f"📁 Последний реестр: {os.path.basename(self.last_register_directory)}",
                        font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            ctk.CTkButton(file_info_frame, text="📂 Открыть", 
                        command=self.load_register_file, width=80, height=25).pack(side="right", padx=5)
        
        # ВОССТАНОВЛЕНА КНОПКА АВТООПРЕДЕЛЕНИЯ (перемещена выше)
        auto_detect_frame = ctk.CTkFrame(auto_frame)
        auto_detect_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(auto_detect_frame, text="🔄 Автоопределить семью",
                    command=self.auto_detect_family_from_register, width=200).pack(side="left", padx=5)
        
        # Кнопки загрузки реестра
        load_buttons_frame = ctk.CTkFrame(register_frame)
        load_buttons_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(load_buttons_frame, text="📋 Загрузить реестр (xls/xlsx)",
                    command=self.load_register_file, width=200).pack(side="left", padx=5)
        
        ctk.CTkButton(load_buttons_frame, text="📂 Загрузить последний реестр",
                    command=self.load_last_register, width=200).pack(side="left", padx=5)
        
        # Статус загрузки реестра
        self.register_status_label = ctk.CTkLabel(register_frame, text="Реестр не загружен")
        self.register_status_label.pack(pady=5)
        
        # Информация о загруженном реестре
        self.register_info_text = scrolledtext.ScrolledText(register_frame, height=8, width=80)
        self.register_info_text.pack(fill="x", padx=5, pady=5)
        self.register_info_text.config(state="disabled")
        
        # Привязываем прокрутку колесиком мыши к этому виджету
        try:
            self.register_info_text.bind("<MouseWheel>", self._on_mousewheel)
            self.register_info_text.bind("<Button-4>", self._on_mousewheel)
            self.register_info_text.bind("<Button-5>", self._on_mousewheel)
        except:
            # Если bind не поддерживается, пропускаем
            pass
        
        # Блок загрузки АДПИ из xlsx
        adpi_frame = ctk.CTkFrame(main_frame)
        adpi_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(adpi_frame, text="📂 ЗАГРУЗКА ДАННЫХ АДПИ", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Информация о последнем файле АДПИ
        if self.last_adpi_directory:
            adpi_info_frame = ctk.CTkFrame(adpi_frame)
            adpi_info_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(adpi_info_frame, 
                        text=f"📁 Последний АДПИ: {os.path.basename(self.last_adpi_directory)}",
                        font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            ctk.CTkButton(adpi_info_frame, text="📂 Открыть", 
                        command=self.load_adpi_xlsx, width=80, height=25).pack(side="right", padx=5)
        
        # Кнопки загрузки АДПИ
        adpi_buttons_frame = ctk.CTkFrame(adpi_frame)
        adpi_buttons_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(adpi_buttons_frame, text="📂 Загрузить новый xlsx/ods с АДПИ",
                    command=self.load_adpi_xlsx, width=200).pack(side="left", padx=5)
        ctk.CTkButton(adpi_buttons_frame, text="📂 Загрузить последний АДПИ",
                    command=self.load_last_adpi, width=200).pack(side="left", padx=5)
        
        # Статус загрузки АДПИ
        self.adpi_status_label = ctk.CTkLabel(adpi_frame, text="Файл АДПИ не загружен")
        self.adpi_status_label.pack(pady=5)
        
        # Информация о загруженных данных АДПИ
        self.adpi_info_text = scrolledtext.ScrolledText(adpi_frame, height=8, width=80)
        self.adpi_info_text.pack(fill="x", padx=5, pady=5)
        self.adpi_info_text.config(state="disabled")
        
        # Привязываем прокрутку колесиком мыши к этому виджету
        try:
            self.adpi_info_text.bind("<MouseWheel>", self._on_mousewheel)
            self.adpi_info_text.bind("<Button-4>", self._on_mousewheel)
            self.adpi_info_text.bind("<Button-5>", self._on_mousewheel)
        except:
            # Если bind не поддерживается, пропускаем
            pass
    
    def load_last_register(self):
        """Загрузка последнего файла реестра"""
        register_files = [f for f in os.listdir(self.register_dir) if f.lower().endswith(('.xls', '.xlsx'))]
        if register_files:
            register_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.register_dir, x)), reverse=True)
            last_register = os.path.join(self.register_dir, register_files[0])
            self.load_register_file(last_register, auto_load=True)
        else:
            messagebox.showwarning("Внимание", "Нет сохраненных файлов реестра")
    
    def load_last_adpi(self):
        """Загрузка последнего файла АДПИ"""
        adpi_files = [f for f in os.listdir(self.adpi_dir) if f.lower().endswith(('.xls', '.xlsx', '.ods'))]
        if adpi_files:
            adpi_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.adpi_dir, x)), reverse=True)
            last_adpi = os.path.join(self.adpi_dir, adpi_files[0])
            self.load_adpi_xlsx(last_adpi, auto_load=True)
        else:
            messagebox.showwarning("Внимание", "Нет сохраненных файлов АДПИ")
    
    def load_register_file(self, file_path=None, auto_load=False):
        """Загрузка реестра многодетных из xls/xlsx файла с копированием"""
        if not file_path and not auto_load:
            initial_dir = self.last_register_directory if self.last_register_directory else None
            file_path = filedialog.askopenfilename(
                title="Выберите файл реестра многодетных (xls, xlsx)",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
                initialdir=initial_dir
            )
        
        if not file_path:
            return
        
        try:
            self.last_register_directory = os.path.dirname(file_path)
            self.save_config()
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.xls':
                df = pd.read_excel(file_path, header=None, engine='xlrd')
            else:
                df = pd.read_excel(file_path, header=None)
            
            self.register_data = {}
            i = 1
            while i < len(df):
                try:
                    row = df.iloc[i]
                    if row.isnull().all():
                        i += 1
                        continue
                    
                    if not pd.isna(row[0]) and str(row[0]).strip() and re.match(r'^\d+$', str(row[0]).strip()):
                        phone_raw = str(row[10]) if len(row) > 10 and not pd.isna(row[10]) else ""
                        phone = self.format_phone(phone_raw)
                        
                        main_person = {
                            'surname': self.clean_string(str(row[1]).strip()) if not pd.isna(row[1]) else "",
                            'name': self.clean_string(str(row[2]).strip()) if not pd.isna(row[2]) else "",
                            'patronymic': self.clean_string(str(row[3]).strip()) if not pd.isna(row[3]) else "",
                            'birth_date': self.parse_date(str(row[4])) if not pd.isna(row[4]) else "",
                            'phone': phone
                        }
                        
                        fio_parts = [main_person['surname'], main_person['name'], main_person['patronymic']]
                        fio_full = ' '.join([p for p in fio_parts if p])
                        if not fio_full:
                            i += 1
                            continue
                        
                        address_info = {
                            'region': self.clean_string(str(row[5]).strip()) if len(row) > 5 and not pd.isna(row[5]) else "",
                            'index': self.clean_string(str(row[6]).strip()) if len(row) > 6 and not pd.isna(row[6]) else "",
                            'city': self.clean_string(str(row[7]).strip()) if len(row) > 7 and not pd.isna(row[7]) else "",
                            'street': self.clean_string(str(row[8]).strip()) if len(row) > 8 and not pd.isna(row[8]) else "",
                            'house': self.clean_string(str(row[9]).strip()) if len(row) > 9 and not pd.isna(row[9]) else ""
                        }
                        
                        family_members = []
                        
                        if len(row) > 11 and not pd.isna(row[11]) and str(row[11]).strip():
                            family_members.append({
                                'surname': self.clean_string(str(row[11]).strip()),
                                'name': self.clean_string(str(row[12]).strip()) if len(row) > 12 and not pd.isna(row[12]) else "",
                                'patronymic': self.clean_string(str(row[13]).strip()) if len(row) > 13 and not pd.isna(row[13]) else "",
                                'birth_date': self.parse_date(str(row[14])) if len(row) > 14 and not pd.isna(row[14]) else "",
                                'fio_full': self.clean_fio(f"{str(row[11]).strip()} {str(row[12]).strip() if len(row) > 12 and not pd.isna(row[12]) else ''} {str(row[13]).strip() if len(row) > 13 and not pd.isna(row[13]) else ''}".strip())
                            })
                        
                        j = i + 1
                        while j < len(df):
                            next_row = df.iloc[j]
                            if (pd.isna(next_row[0]) or str(next_row[0]).strip() == "") and \
                            len(next_row) > 11 and not pd.isna(next_row[11]) and str(next_row[11]).strip():
                                family_members.append({
                                    'surname': self.clean_string(str(next_row[11]).strip()),
                                    'name': self.clean_string(str(next_row[12]).strip()) if len(next_row) > 12 and not pd.isna(next_row[12]) else "",
                                    'patronymic': self.clean_string(str(next_row[13]).strip()) if len(next_row) > 13 and not pd.isna(next_row[13]) else "",
                                    'birth_date': self.parse_date(str(next_row[14])) if len(next_row) > 14 and not pd.isna(row[14]) else "",
                                    'fio_full': self.clean_fio(f"{str(next_row[11]).strip()} {str(next_row[12]).strip() if len(next_row) > 12 and not pd.isna(next_row[12]) else ''} {str(next_row[13]).strip() if len(next_row) > 13 and not pd.isna(next_row[13]) else ''}".strip())
                                })
                                j += 1
                            else:
                                break
                        
                        self.register_data[fio_full] = {
                            'main_person': main_person,
                            'family_members': family_members,
                            'address': address_info,
                            'row_index': i
                        }
                        
                        i = j
                    else:
                        i += 1
                except Exception as e:
                    print(f"Ошибка обработки строки {i}: {e}")
                    traceback.print_exc()
                    i += 1
                    continue
            
            self.register_status_label.configure(
                text=f"Загружено семей: {len(self.register_data)} из файла: {os.path.basename(file_path)}"
            )
            
            self.update_register_info()
            if not auto_load:
                messagebox.showinfo("Успех", f"Загружено {len(self.register_data)} семей из реестра")
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Ошибка загрузки реестра: {error_details}")
            if not auto_load:
                messagebox.showerror("Ошибка", f"Не удалось загрузить реестр: {str(e)}")
    
    def load_last_register(self):
        """Загрузка последнего файла реестра"""
        register_files = [f for f in os.listdir(self.register_dir) if f.lower().endswith(('.xls', '.xlsx'))]
        if register_files:
            register_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.register_dir, x)), reverse=True)
            last_register = os.path.join(self.register_dir, register_files[0])
            self.load_register_file(last_register, auto_load=True)
        else:
            messagebox.showwarning("Внимание", "Нет сохраненных файлов реестра")

    def load_last_adpi(self):
        """Загрузка последнего файла АДПИ"""
        adpi_files = [f for f in os.listdir(self.adpi_dir) if f.lower().endswith(('.xls', '.xlsx', '.ods'))]
        if adpi_files:
            adpi_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.adpi_dir, x)), reverse=True)
            last_adpi = os.path.join(self.adpi_dir, adpi_files[0])
            self.load_adpi_xlsx(last_adpi, auto_load=True)
        else:
            messagebox.showwarning("Внимание", "Нет сохраненных файлов АДПИ")

    def parse_date(self, date_string):
        """Парсинг даты из различных форматов"""
        if not date_string or pd.isna(date_string) or str(date_string).lower() in ['nan', 'nat', 'none', '']:
            return ""
        try:
            date_string = str(date_string).strip()
            if isinstance(date_string, (datetime, pd.Timestamp)):
                return date_string.strftime('%d.%m.%Y')
            
            formats = [
                '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y',
                '%Y.%m.%d', '%Y/%m/%d', '%Y-%m-%d',
                '%d.%m.%y', '%d/%m/%y', '%d-%m-%y',
                '%m/%d/%Y', '%m/%d/%y'  # Добавлен формат MM/DD/YYYY
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    if 1900 <= dt.year <= datetime.now().year:
                        return dt.strftime('%d.%m.%Y')
                except:
                    continue
            
            dt = parser.parse(date_string, dayfirst=True, yearfirst=False, fuzzy=True)
            if 1900 <= dt.year <= datetime.now().year:
                return dt.strftime('%d.%m.%Y')
        except:
            pass
        return self.clean_date(date_string)
    
    def format_phone(self, phone_string):
        """Форматирование телефона в формат 7XXXXXXXXXX"""
        return self.clean_phone(phone_string)
    
    def update_register_info(self):
        """Обновление информации о загруженном реестре"""
        if not self.register_data:
            self.register_info_text.config(state="normal")
            self.register_info_text.delete("1.0", "end")
            self.register_info_text.insert("1.0", "Реестр многодетных не загружен")
            self.register_info_text.config(state="disabled")
            return
        
        info_text = f"Загружено {len(self.register_data)} семей из реестра:\n"
        for i, (fio, data) in enumerate(list(self.register_data.items())[:5]):
            info_text += f"{i+1}. {fio}\n"
            if data['main_person']['phone']:
                info_text += f"   📱 Телефон: {data['main_person']['phone']}\n"
            if data['main_person']['birth_date']:
                info_text += f"   Дата рождения: {data['main_person']['birth_date']}\n"
            
            address_parts = []
            if data['address']['city']:
                address_parts.append(f"г. {data['address']['city']}")
            if data['address']['street']:
                address_parts.append(f"ул. {data['address']['street']}")
            if data['address']['house']:
                address_parts.append(f"д. {data['address']['house']}")
            if address_parts:
                info_text += f"   Адрес: {', '.join(address_parts)}\n"
            
            info_text += f"   Всего членов семьи: {len(data['family_members']) + 1} (основной + {len(data['family_members'])} членов)\n"
            
            info_text += "   Члены семьи:\n"
            info_text += f"   1. {fio} (основной)\n"
            for j, member in enumerate(data['family_members'][:6]):
                member_info = f"{member['fio_full']}"
                if member['birth_date']:
                    member_info += f" ({member['birth_date']})"
                info_text += f"   {j+2}. {member_info}\n"
            if len(data['family_members']) > 6:
                info_text += f"   ... и еще {len(data['family_members']) - 6} чел.\n"
            info_text += "\n"
        
        if len(self.register_data) > 5:
            info_text += f"... и еще {len(self.register_data) - 5} семей\n"
        
        self.register_info_text.config(state="normal")
        self.register_info_text.delete("1.0", "end")
        self.register_info_text.insert("1.0", info_text)
        self.register_info_text.config(state="disabled")
    
    def normalize_fio(self, fio):
        """Нормализация ФИО для сравнения"""
        fio = self.clean_fio(fio)
        return ' '.join(fio.lower().split())
    
    def is_fio_similar(self, search_fio, target_fio):
        """Проверка похожести ФИО"""
        search_fio = self.clean_fio(search_fio)
        target_fio = self.clean_fio(target_fio)
        
        search_parts = self.normalize_fio(search_fio).split()
        target_parts = self.normalize_fio(target_fio).split()
        
        if not search_parts or not target_parts:
            return False
        
        if search_parts[0] != target_parts[0]:
            return False
        
        if len(search_parts) > 1:
            for part in search_parts[1:]:
                if part in target_parts:
                    return True
            return False
        return True
    
    def fill_from_register_data(self, register_data, fio):
        """Заполнение формы данными из реестра с обработкой возраста"""
        mother = None
        father = None
        children = []
        potential_fathers = []
        potential_children = []
        
        main_person = register_data['main_person']
        
        # Проверка года рождения основного лица
        if main_person['birth_date']:
            try:
                birth_dt = datetime.strptime(main_person['birth_date'], '%d.%m.%Y')
                # НОВОЕ: родитель не может родиться после 2003
                if birth_dt.year > 2003:
                    # Это может быть ребенок старше 18 лет
                    if birth_dt.year >= 2000:  # Родился после 2000
                        potential_children.append(main_person)
                    else:
                        # Родился до 2000 - это родитель
                        if main_person['patronymic'].endswith(('на', 'вна', 'ична')):
                            mother = main_person
                        else:
                            potential_fathers.append(main_person)
                else:
                    # Родился до или в 2003 - это родитель
                    if main_person['patronymic'].endswith(('на', 'вна', 'ична')):
                        mother = main_person
                    else:
                        potential_fathers.append(main_person)
            except:
                # Если дата некорректна, определяем по отчеству
                if main_person['patronymic'].endswith(('на', 'вна', 'ична')):
                    mother = main_person
                else:
                    potential_fathers.append(main_person)
        
        # Анализируем членов семьи
        for member in register_data['family_members']:
            if member['birth_date']:
                try:
                    birth_dt = datetime.strptime(member['birth_date'], '%d.%m.%Y')
                    
                    # НОВОЕ: ребенок не может родиться до 2000
                    if birth_dt.year < 2000:
                        # Родился до 2000 - это родитель
                        if member['patronymic'].endswith(('на', 'вна', 'ична')):
                            if not mother:
                                mother = member
                        else:
                            potential_fathers.append(member)
                        continue
                    
                    # Родитель не может родиться после 2003
                    if birth_dt.year > 2003:
                        # Это ребенок
                        potential_children.append(member)
                        continue
                    
                    # Для 2000-2003 определяем по отчеству
                    if member['patronymic'].endswith(('на', 'вна', 'ична')):
                        # Женский пол
                        if not mother:
                            mother = member
                        elif not father and birth_dt.year <= 2003:
                            # Если отчества нет, но год подходит для отца
                            potential_fathers.append(member)
                        else:
                            potential_children.append(member)
                    elif member['patronymic'].endswith(('ич', 'вич', 'ыч')):
                        # Мужской пол
                        if birth_dt.year <= 2003:  # Может быть отцом
                            if not father and birth_dt.year >= 1980:  # Разумный возраст для отца
                                potential_fathers.append(member)
                            else:
                                potential_children.append(member)
                        else:
                            potential_children.append(member)
                    else:
                        # Неопределенное отчество
                        if birth_dt.year <= 2003 and not mother:
                            mother = member
                        else:
                            potential_children.append(member)
                            
                except:
                    # Если дата некорректна, определяем по отчеству
                    if member['patronymic'].endswith(('на', 'вна', 'ична')):
                        if not mother:
                            mother = member
                        else:
                            potential_children.append(member)
                    elif member['patronymic'].endswith(('ич', 'вич', 'ыч')):
                        potential_fathers.append(member)
                    else:
                        potential_children.append(member)
        
        # Выбираем отца из потенциальных кандидатов
        if potential_fathers:
            # Ищем наиболее подходящего (старше, но не слишком)
            potential_fathers.sort(key=lambda x: datetime.strptime(x['birth_date'], '%d.%m.%Y') if x['birth_date'] else datetime(1900, 1, 1))
            father = potential_fathers[0]
        
        # Все остальные - дети
        children = potential_children
        
        # НОВОЕ: проверяем, не попал ли ребенок старше 2010 года в отцы
        if father:
            try:
                birth_dt = datetime.strptime(father['birth_date'], '%d.%m.%Y')
                if birth_dt.year > 2010:
                    # Это слишком молодой для отца - перемещаем в дети
                    children.append(father)
                    father = None
            except:
                pass
        
        # Заполняем форму
        self.clear_form()
        
        # Заполняем мать
        if mother:
            mother_fio = f"{mother['surname']} {mother['name']} {mother['patronymic']}"
            mother_fio = self.clean_fio(mother_fio)
            self.mother_fio.delete(0, 'end')
            self.mother_fio.insert(0, mother_fio)
            self.mother_birth.delete(0, 'end')
            self.mother_birth.insert(0, mother['birth_date'])
        
        # Заполняем отца
        if father:
            father_fio = f"{father['surname']} {father['name']} {father['patronymic']}"
            father_fio = self.clean_fio(father_fio)
            self.father_fio.delete(0, 'end')
            self.father_fio.insert(0, father_fio)
            self.father_birth.delete(0, 'end')
            self.father_birth.insert(0, father['birth_date'])
        
        # Заполняем детей
        self.clear_all_children()
        for i, child in enumerate(children):
            if i >= 20:  # Ограничение на количество детей
                break
            self.add_child_entry()
            child_fio = f"{child['surname']} {child['name']} {child['patronymic']}"
            child_fio = self.clean_fio(child_fio)
            self.children_entries[i]['fio'].delete(0, 'end')
            self.children_entries[i]['fio'].insert(0, child_fio)
            self.children_entries[i]['birth'].delete(0, 'end')
            self.children_entries[i]['birth'].insert(0, child['birth_date'])
        
        # Заполняем телефон
        if register_data['main_person']['phone']:
            phone = self.clean_phone(register_data['main_person']['phone'])
            self.family_phone = phone
            self.phone_entry.delete(0, 'end')
            self.phone_entry.insert(0, phone)
            self.log_message(f"📱 Телефон семьи: {phone}")
        
        # Заполняем адрес
        address_parts = []
        if register_data['address']['city']:
            address_parts.append(f"г. {register_data['address']['city']}")
        if register_data['address']['street']:
            address_parts.append(f"ул. {register_data['address']['street']}")
        if register_data['address']['house']:
            address_parts.append(f"д. {register_data['address']['house']}")
        if address_parts:
            address = ', '.join(address_parts)
            address = self.clean_address(address)
            self.address.delete(0, 'end')
            self.address.insert(0, address)
        
        # НОВОЕ: Устанавливаем пособие по многодетности по умолчанию 1900
        self.large_family_benefit_var.set("1900")
        self.large_family_benefit_entry.delete(0, 'end')
        self.large_family_benefit_entry.insert(0, "1900")
        
        # Автоматически заполняем АДПИ
        self.fill_adpi_from_loaded_data()
        return True
    
    def is_adult(self, birth_date):
        """Проверка, является ли человек взрослым"""
        try:
            if not birth_date:
                return False
            dt = datetime.strptime(birth_date, '%d.%m.%Y')
            today = datetime.now()
            age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
            return 16 <= age <= 65
        except:
            return False
    
    def is_child(self, birth_date):
        """Проверка, является ли человек ребенком"""
        try:
            if not birth_date:
                return False
            dt = datetime.strptime(birth_date, '%d.%m.%Y')
            today = datetime.now()
            age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
            return age < 25
        except:
            return False
    
    def auto_detect_family_from_register(self):
        """Автоматическое определение семьи из реестра с обработкой дубликатов"""
        if not self.register_data:
            messagebox.showwarning("Предупреждение", "Сначала загрузите реестр многодетных")
            return
        
        search_fio = self.search_fio_input.get().strip()
        search_fio = self.clean_fio(search_fio)
        if not search_fio:
            mother_fio = self.mother_fio.get().strip()
            father_fio = self.father_fio.get().strip()
            search_fio = mother_fio or father_fio
        
        if not search_fio:
            messagebox.showwarning("Предупреждение", "Введите ФИО матери или отца в форме или в поле поиска")
            return
        
        # Ищем все совпадения
        exact_matches = []
        similar_matches = []
        
        for fio_key in self.register_data.keys():
            if self.normalize_fio(search_fio) == self.normalize_fio(fio_key):
                exact_matches.append((fio_key, self.register_data[fio_key]))
            elif self.is_fio_similar(search_fio, fio_key):
                similar_matches.append((fio_key, self.register_data[fio_key]))
        
        # НОВОЕ: Обработка случая, когда найдено несколько семей
        if len(exact_matches) > 1:
            messagebox.showerror("Ошибка", 
                               f"Найдено {len(exact_matches)} семей с одинаковыми ФИО:\n" +
                               "\n".join([f"{i+1}. {fio}" for i, (fio, _) in enumerate(exact_matches)]) +
                               "\n\nПожалуйста, уточните поиск.")
            return
        elif len(exact_matches) == 1:
            found_data = exact_matches[0][1]
            found_fio = exact_matches[0][0]
        elif similar_matches:
            if len(similar_matches) > 1:
                # Предлагаем выбрать из похожих
                families_list = "\n".join([f"{i+1}. {fio}" for i, (fio, _) in enumerate(similar_matches)])
                choice = messagebox.askquestion("Выбор семьи", 
                                              f"Найдено {len(similar_matches)} похожих семей:\n{families_list}\n\nИспользовать первую?")
                if choice == 'yes':
                    found_data = similar_matches[0][1]
                    found_fio = similar_matches[0][0]
                else:
                    return
            else:
                found_data = similar_matches[0][1]
                found_fio = similar_matches[0][0]
        else:
            messagebox.showwarning("Не найдено", 
                                 f"Семья с ФИО '{search_fio}' не найдена в реестре")
            return
        
        # Заполняем данные из реестра
        success = self.fill_from_register_data(found_data, found_fio)
        if success:
            messagebox.showinfo("Успех", f"Семья автоопределена: {found_fio}")
            self.tabview.set("👨‍👩‍👧‍👦 Семья")
    
    def load_adpi_xlsx(self, file_path=None, auto_load=False):
        """Загрузка данных АДПИ из xlsx файла с копированием"""
        if not file_path and not auto_load:
            initial_dir = self.last_adpi_directory if self.last_adpi_directory else None
            file_path = filedialog.askopenfilename(
                title="Выберите файл с данными АДПИ (xlsx, ods)",
                filetypes=[("Excel files", "*.xlsx *.xls"), ("OpenOffice files", "*.ods"), ("All files", "*.*")],
                initialdir=initial_dir
            )
        
        if not file_path:
            return
        
        try:
            self.last_adpi_directory = os.path.dirname(file_path)
            self.save_config()
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.ods':
                df = pd.read_excel(file_path, header=None, engine='odf')
            else:
                df = pd.read_excel(file_path, header=None)
            
            self.adpi_data = {}
            
            for index, row in df.iterrows():
                try:
                    if row.isnull().all():
                        continue
                    
                    fio_cell = str(row[1]).strip() if len(row) > 1 and not pd.isna(row[1]) else ""
                    if not fio_cell or fio_cell.lower() in ['nan', 'none', '']:
                        continue
                    
                    address_cell = str(row[3]).strip() if len(row) > 3 and not pd.isna(row[3]) else ""
                    
                    install_date_raw = ""
                    if len(row) > 6:
                        install_cell = row[6]
                        if not pd.isna(install_cell):
                            install_date_raw = str(install_cell).strip()
                    
                    check_dates_raw = ""
                    if len(row) > 7:
                        check_cell = row[7]
                        if not pd.isna(check_cell):
                            check_dates_raw = str(check_cell).strip()
                    
                    # НОВОЕ: Обработка двух дат (берем последнюю)
                    install_date = self.parse_adpi_date(install_date_raw)
                    check_date = self.parse_adpi_date(check_dates_raw)
                    
                    fio_normalized = self.clean_fio(fio_cell)
                    address_cell = self.clean_address(address_cell)
                    
                    self.adpi_data[fio_normalized] = {
                        'address': address_cell,
                        'install_date': install_date,
                        'check_date': check_date
                    }
                except Exception as e:
                    print(f"Ошибка обработки строки {index}: {e}")
                    continue
            
            self.adpi_status_label.configure(
                text=f"Загружено записей: {len(self.adpi_data)} из файла: {os.path.basename(file_path)}"
            )
            
            self.update_adpi_info()
            if not auto_load:
                messagebox.showinfo("Успех", f"Загружено {len(self.adpi_data)} записей из файла АДПИ")
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Ошибка загрузки файла АДПИ: {error_details}")
            if not auto_load:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл АДПИ: {str(e)}")
    
    def parse_adpi_date(self, date_string):
        """Парсинг даты из АДПИ файла с обработкой двух дат"""
        if not date_string:
            return ""
        
        # НОВОЕ: Обработка случая с двумя датами (например: 28.01.2024.21.05.2025)
        if '.' in date_string:
            parts = date_string.split('.')
            if len(parts) >= 6:  # Есть две полные даты
                try:
                    # Пробуем получить две даты
                    date1_str = '.'.join(parts[:3])
                    date2_str = '.'.join(parts[3:6])
                    
                    # Парсим даты
                    date1 = self.parse_single_date(date1_str)
                    date2 = self.parse_single_date(date2_str)
                    
                    # Если обе даты валидны, берем более позднюю
                    if date1 and date2:
                        try:
                            dt1 = datetime.strptime(date1, '%d.%m.%Y')
                            dt2 = datetime.strptime(date2, '%d.%m.%Y')
                            return date1 if dt1 > dt2 else date2
                        except:
                            return date1  # Если не удалось сравнить, возвращаем первую
                    elif date1:
                        return date1
                    elif date2:
                        return date2
                except:
                    pass
        
        # Обычная обработка одной даты
        return self.parse_single_date(date_string)
    
    def parse_single_date(self, date_string):
        """Парсинг одной даты"""
        try:
            # Пробуем разные форматы
            formats = [
                '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y',
                '%Y.%m.%d', '%Y/%m/%d', '%Y-%m-%d',
                '%d.%m.%y', '%d/%m/%y', '%d-%m-%y',
                '%m/%d/%Y', '%m/%d/%y'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_string, fmt)
                    if 1900 <= dt.year <= datetime.now().year:
                        return dt.strftime('%d.%m.%Y')
                except:
                    continue
            
            # Пробуем с dateutil
            dt = parser.parse(date_string, dayfirst=True, yearfirst=False, fuzzy=True)
            if 1900 <= dt.year <= datetime.now().year:
                return dt.strftime('%d.%m.%Y')
        except:
            pass
        
        return self.clean_date(date_string)
    
    def update_adpi_info(self):
        """Обновление информации о загруженных данных АДПИ"""
        if not self.adpi_data:
            self.adpi_info_text.config(state="normal")
            self.adpi_info_text.delete("1.0", "end")
            self.adpi_info_text.insert("1.0", "Данные АДПИ не загружены")
            self.adpi_info_text.config(state="disabled")
            return
        
        info_text = f"Загружено {len(self.adpi_data)} записей АДПИ:\n"
        for i, (fio, data) in enumerate(list(self.adpi_data.items())[:5]):
            info_text += f"{i+1}. {fio}\n"
            if data['address']:
                address_display = data['address']
                if len(address_display) > 50:
                    address_display = address_display[:47] + "..."
                info_text += f"   Адрес: {address_display}\n"
            if data['install_date']:
                info_text += f"   Установка: {data['install_date']}\n"
            if data['check_date']:
                info_text += f"   Проверка: {data['check_date']}\n"
            info_text += "\n"
        
        if len(self.adpi_data) > 5:
            info_text += f"... и еще {len(self.adpi_data) - 5} записей\n"
        
        self.adpi_info_text.config(state="normal")
        self.adpi_info_text.delete("1.0", "end")
        self.adpi_info_text.insert("1.0", info_text)
        self.adpi_info_text.config(state="disabled")
    
    def fill_adpi_from_loaded_data(self):
        """Заполнение данных АДПИ из загруженного файла по ФИО"""
        if not self.adpi_data:
            messagebox.showwarning("Предупреждение", "Сначала загрузите файл АДПИ")
            return
        
        mother_fio = self.mother_fio.get().strip()
        mother_fio = self.clean_fio(mother_fio)
        father_fio = self.father_fio.get().strip()
        father_fio = self.clean_fio(father_fio)
        
        found_data = None
        found_for = ""
        
        for fio in [mother_fio, father_fio]:
            if fio and fio in self.adpi_data:
                found_data = self.adpi_data[fio]
                found_for = fio
                break
        
        if not found_data:
            for fio_key in self.adpi_data.keys():
                for search_fio in [mother_fio, father_fio]:
                    if search_fio and self.is_fio_similar(search_fio, fio_key):
                        found_data = self.adpi_data[fio_key]
                        found_for = fio_key
                        break
                if found_data:
                    break
        
        if found_data:
            if found_data['address']:
                address = self.clean_address(found_data['address'])
                self.address.delete(0, 'end')
                self.address.insert(0, address)
            
            if found_data['install_date'] or found_data['check_date']:
                self.adpi_var.set("да")
                if found_data['install_date']:
                    install_date = self.clean_date(found_data['install_date'])
                    self.install_date.delete(0, 'end')
                    self.install_date.insert(0, install_date)
                else:
                    self.install_date.delete(0, 'end')
                if found_data['check_date']:
                    check_date = self.clean_date(found_data['check_date'])
                    self.check_date.delete(0, 'end')
                    self.check_date.insert(0, check_date)
                else:
                    self.check_date.delete(0, 'end')
            else:
                self.adpi_var.set("нет")
                self.install_date.delete(0, 'end')
                self.check_date.delete(0, 'end')
            
            messagebox.showinfo("Успех", f"Данные АДПИ и адрес заполнены для: {found_for}")
            self.tabview.set("📟 АДПИ")
        else:
            messagebox.showwarning("Не найдено", 
                                 f"Не найдены данные АДПИ для:\nМать: {mother_fio}\nОтец: {father_fio}")
    
    def setup_family_tab(self):
        """Вкладка информации о родителях"""
        main_frame = ctk.CTkFrame(self.family_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Мать
        mother_frame = ctk.CTkFrame(main_frame)
        mother_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(mother_frame, text="👩 МАТЬ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        mother_fio_frame = ctk.CTkFrame(mother_frame)
        mother_fio_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(mother_fio_frame, text="ФИО матери:").pack(anchor="w", padx=5)
        self.mother_fio = ctk.CTkEntry(mother_fio_frame, placeholder_text="Фамилия Имя Отчество")
        self.mother_fio.pack(fill="x", padx=5, pady=2)
        
        mother_birth_frame = ctk.CTkFrame(mother_frame)
        mother_birth_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(mother_birth_frame, text="Дата рождения (ДД.ММ.ГГГГ):").pack(anchor="w", padx=5)
        self.mother_birth = ctk.CTkEntry(mother_birth_frame, placeholder_text="Например: 15.03.1985")
        self.mother_birth.pack(fill="x", padx=5, pady=2)
        
        mother_work_frame = ctk.CTkFrame(mother_frame)
        mother_work_frame.pack(fill="x", padx=5, pady=5)
        
        # Чекбоксы для матери
        mother_checkboxes_frame = ctk.CTkFrame(mother_work_frame, fg_color="transparent")
        mother_checkboxes_frame.pack(fill="x", padx=5, pady=2)
        
        self.mother_disability_care_var = ctk.BooleanVar(value=False)
        self.mother_disability_care_checkbox = ctk.CTkCheckBox(
            mother_checkboxes_frame, 
            text="уход за ребенком-инвалидом",
            variable=self.mother_disability_care_var,
            command=self.on_mother_disability_care_toggle
        )
        self.mother_disability_care_checkbox.pack(side="left", padx=5, pady=2)
        
        # НОВОЕ: Чекбокс "Не работает" для матери
        self.mother_not_working_var = ctk.BooleanVar(value=False)
        self.mother_not_working_checkbox = ctk.CTkCheckBox(
            mother_checkboxes_frame,
            text="Не работает",
            variable=self.mother_not_working_var,
            command=self.on_mother_not_working_toggle
        )
        self.mother_not_working_checkbox.pack(side="left", padx=5, pady=2)
        
        ctk.CTkLabel(mother_work_frame, text="Место работы:").pack(anchor="w", padx=5)
        self.mother_work = ctk.CTkEntry(mother_work_frame, placeholder_text="ООО 'Ромашка' или ИП Иванова")
        self.mother_work.pack(fill="x", padx=5, pady=2)
        
        # Отец
        father_frame = ctk.CTkFrame(main_frame)
        father_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(father_frame, text="👨 ОТЕЦ (опционально)", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        father_fio_frame = ctk.CTkFrame(father_frame)
        father_fio_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(father_fio_frame, text="ФИО отца:").pack(anchor="w", padx=5)
        self.father_fio = ctk.CTkEntry(father_fio_frame, placeholder_text="Фамилия Имя Отчество (оставьте пустым если нет отца)")
        self.father_fio.pack(fill="x", padx=5, pady=2)
        
        father_birth_frame = ctk.CTkFrame(father_frame)
        father_birth_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(father_birth_frame, text="Дата рождения (ДД.ММ.ГГГГ):").pack(anchor="w", padx=5)
        self.father_birth = ctk.CTkEntry(father_birth_frame, placeholder_text="Например: 10.05.1982")
        self.father_birth.pack(fill="x", padx=5, pady=2)
        
        father_work_frame = ctk.CTkFrame(father_frame)
        father_work_frame.pack(fill="x", padx=5, pady=5)
        
        # Чекбоксы для отца
        father_checkboxes_frame = ctk.CTkFrame(father_work_frame, fg_color="transparent")
        father_checkboxes_frame.pack(fill="x", padx=5, pady=2)
        
        # НОВОЕ: Чекбокс "Не работает" для отца
        self.father_not_working_var = ctk.BooleanVar(value=False)
        self.father_not_working_checkbox = ctk.CTkCheckBox(
            father_checkboxes_frame,
            text="Не работает",
            variable=self.father_not_working_var,
            command=self.on_father_not_working_toggle
        )
        self.father_not_working_checkbox.pack(side="left", padx=5, pady=2)
        
        ctk.CTkLabel(father_work_frame, text="Место работы:").pack(anchor="w", padx=5)
        self.father_work = ctk.CTkEntry(father_work_frame, placeholder_text="ЗАО 'Тюльпан' или не работает")
        self.father_work.pack(fill="x", padx=5, pady=2)
        
        # Телефон
        phone_frame = ctk.CTkFrame(main_frame)
        phone_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(phone_frame, text="📱 ТЕЛЕФОН", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        phone_entry_frame = ctk.CTkFrame(phone_frame)
        phone_entry_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(phone_entry_frame, text="Номер телефона:").pack(anchor="w", padx=5)
        self.phone_entry = ctk.CTkEntry(phone_entry_frame, placeholder_text="7XXXXXXXXXX (автозаполнение из реестра)")
        self.phone_entry.pack(fill="x", padx=5, pady=2)
        
        self.phone_info_label = ctk.CTkLabel(phone_frame, 
                                            text="Телефон будет автоматически сохранен в общий JSON с семьей")
        self.phone_info_label.pack(pady=5)
    
    def on_mother_disability_care_toggle(self):
        """Обработчик чекбокса 'уход за ребенком-инвалидом'"""
        if self.mother_disability_care_var.get():
            self.mother_work.delete(0, 'end')
            self.mother_work.insert(0, "уход за ребенком-инвалидом")
            # НОВОЕ: Автоматически заполняем доходы
            self.income_fields['child_disability_care'].delete(0, 'end')
            self.income_fields['child_disability_care'].insert(0, "10000")
            self.income_fields['child_disability_pension'].delete(0, 'end')
            self.income_fields['child_disability_pension'].insert(0, "25000")
        else:
            current_text = self.mother_work.get().strip()
            if current_text == "уход за ребенком-инвалидом":
                self.mother_work.delete(0, 'end')
            # НОВОЕ: Очищаем доходы, если они равны стандартным значениям
            if self.income_fields['child_disability_care'].get() == "10000":
                self.income_fields['child_disability_care'].delete(0, 'end')
            if self.income_fields['child_disability_pension'].get() == "25000":
                self.income_fields['child_disability_pension'].delete(0, 'end')
    
    def on_mother_not_working_toggle(self):
        """Обработчик чекбокса 'Не работает' для матери"""
        if self.mother_not_working_var.get():
            # Устанавливаем значение "не работает" в поле работы
            self.mother_work.delete(0, 'end')
            self.mother_work.insert(0, "не работает")
            # Также устанавливаем значение 0 в поле зарплаты
            self.income_fields['mother_salary'].delete(0, 'end')
            self.income_fields['mother_salary'].insert(0, "0")
        else:
            # Очищаем поле работы, если там было "не работает"
            current_text = self.mother_work.get().strip()
            if current_text.lower() == "не работает":
                self.mother_work.delete(0, 'end')
            # Очищаем поле зарплаты, если оно содержит 0
            if self.income_fields['mother_salary'].get() == "0":
                self.income_fields['mother_salary'].delete(0, 'end')
    
    def on_father_not_working_toggle(self):
        """Обработчик чекбокса 'Не работает' для отца"""
        if self.father_not_working_var.get():
            # Устанавливаем значение "не работает" в поле работы
            self.father_work.delete(0, 'end')
            self.father_work.insert(0, "не работает")
            # Также устанавливаем значение 0 в поле зарплаты
            self.income_fields['father_salary'].delete(0, 'end')
            self.income_fields['father_salary'].insert(0, "0")
        else:
            # Очищаем поле работы, если там было "не работает"
            current_text = self.father_work.get().strip()
            if current_text.lower() == "не работает":
                self.father_work.delete(0, 'end')
            # Очищаем поле зарплаты, если оно содержит 0
            if self.income_fields['father_salary'].get() == "0":
                self.income_fields['father_salary'].delete(0, 'end')
    
    def setup_children_tab(self):
        """Вкладка информации о детях"""
        main_frame = ctk.CTkFrame(self.children_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="👶 ДЕТИ",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        
        self.children_scrollframe = ctk.CTkScrollableFrame(main_frame, height=400)
        self.children_scrollframe.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Привязываем прокрутку колесиком мыши к этому фрейму
        try:
            self.children_scrollframe.bind("<MouseWheel>", self._on_mousewheel)
            self.children_scrollframe.bind("<Button-4>", self._on_mousewheel)
            self.children_scrollframe.bind("<Button-5>", self._on_mousewheel)
        except:
            # Если bind не поддерживается, пропускаем
            pass
        
        self.children_entries = []
        
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(buttons_frame, text="➕ Добавить ребенка",
                     command=self.add_child_entry, width=150).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="➖ Удалить последнего",
                     command=self.remove_child_entry, width=150).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="🧹 Очистить всех детей",
                     command=self.clear_all_children, width=150, fg_color="orange").pack(side="left", padx=5)
        
        self.add_child_entry()
    
    def on_individual_home_education_toggle(self, var, education_field):
        """Обработчик индивидуального чекбокса 'Домашний' для конкретного ребенка"""
        if var.get():
            education_field.delete(0, 'end')
            education_field.insert(0, "домашний")
        else:
            current_text = education_field.get().strip()
            if current_text.lower() == "домашний":
                education_field.delete(0, 'end')
    
    def add_child_entry(self):
        """Добавление полей для ввода информации о ребенке"""
        child_frame = ctk.CTkFrame(self.children_scrollframe)
        child_frame.pack(fill="x", padx=5, pady=5)
        child_number = len(self.children_entries) + 1
        
        header_frame = ctk.CTkFrame(child_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(header_frame, text=f"👶 Ребенок {child_number}:",
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        fio_frame = ctk.CTkFrame(child_frame, fg_color="transparent")
        fio_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(fio_frame, text="ФИО ребенка:").pack(side="left", padx=5)
        child_fio = ctk.CTkEntry(fio_frame)
        child_fio.pack(side="left", fill="x", expand=True, padx=5)
        
        birth_frame = ctk.CTkFrame(child_frame, fg_color="transparent")
        birth_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(birth_frame, text="Дата рождения:").pack(side="left", padx=5)
        child_birth = ctk.CTkEntry(birth_frame, placeholder_text="ДД.ММ.ГГГГ")
        child_birth.pack(side="left", fill="x", expand=True, padx=5)
        
        edu_frame = ctk.CTkFrame(child_frame, fg_color="transparent")
        edu_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(edu_frame, text="Место учебы:").pack(side="left", padx=5)
        child_education = ctk.CTkEntry(edu_frame, placeholder_text="Школа №123 или детский сад")
        child_education.pack(side="left", fill="x", expand=True, padx=5)
        
        # Чекбокс "Домашний" для конкретного ребенка
        home_edu_checkbox_frame = ctk.CTkFrame(child_frame, fg_color="transparent")
        home_edu_checkbox_frame.pack(fill="x", padx=5, pady=2)
        child_home_edu_var = ctk.BooleanVar(value=False)
        child_home_edu_checkbox = ctk.CTkCheckBox(
            home_edu_checkbox_frame,
            text="Домашний",
            variable=child_home_edu_var,
            command=lambda var=child_home_edu_var, edu=child_education: self.on_individual_home_education_toggle(var, edu)
        )
        child_home_edu_checkbox.pack(side="left", padx=5, pady=2)
        
        # НОВОЕ: Кнопка удаления конкретного ребенка
        delete_button = ctk.CTkButton(child_frame, text="🗑️ Удалить", width=80,
                                     command=lambda f=child_frame: self.remove_specific_child(f))
        delete_button.pack(side="right", padx=5, pady=2)
        
        self.children_entries.append({
            'frame': child_frame,
            'fio': child_fio,
            'birth': child_birth,
            'education': child_education,
            'home_edu_var': child_home_edu_var
        })
    
    def remove_specific_child(self, child_frame):
        """Удаление конкретного ребенка"""
        for i, child in enumerate(self.children_entries):
            if child['frame'] == child_frame:
                self.children_entries.pop(i)
                child_frame.destroy()
                self.renumber_children()
                break
    
    def renumber_children(self):
        """Перенумерация детей после удаления"""
        for i, child in enumerate(self.children_entries):
            header_label = child['frame'].winfo_children()[0].winfo_children()[0]
            if hasattr(header_label, 'configure'):
                header_label.configure(text=f"👶 Ребенок {i+1}:")
    
    def remove_child_entry(self):
        """Удаление последнего ребенка"""
        if len(self.children_entries) > 0:
            child = self.children_entries.pop()
            child['frame'].destroy()
    
    def clear_all_children(self):
        """Очистка всех детей"""
        if messagebox.askyesno("Подтверждение", "Удалить всех детей?"):
            while len(self.children_entries) > 0:
                child = self.children_entries.pop()
                child['frame'].destroy()
            self.add_child_entry()
    
    def setup_housing_tab(self):
        """Вкладка информации о жилье"""
        main_frame = ctk.CTkFrame(self.housing_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="🏠 ИНФОРМАЦИЯ О ЖИЛЬЕ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        address_frame = ctk.CTkFrame(main_frame)
        address_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(address_frame, text="Адрес проживания:").pack(anchor="w", padx=5)
        self.address = ctk.CTkEntry(address_frame, placeholder_text="Автоматически заполняется из реестра или АДПИ")
        self.address.pack(fill="x", padx=5, pady=2)
        
        rooms_frame = ctk.CTkFrame(main_frame)
        rooms_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(rooms_frame, text="Количество комнат:").pack(anchor="w", padx=5)
        self.rooms = ctk.CTkEntry(rooms_frame, placeholder_text="Например: 3")
        self.rooms.pack(fill="x", padx=5, pady=2)
        
        square_frame = ctk.CTkFrame(main_frame)
        square_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(square_frame, text="Площадь (кв.м.):").pack(anchor="w", padx=5)
        self.square = ctk.CTkEntry(square_frame, placeholder_text="Например: 65")
        self.square.pack(fill="x", padx=5, pady=2)
        
        amenities_frame = ctk.CTkFrame(main_frame)
        amenities_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(amenities_frame, text="Удобства:").pack(anchor="w", padx=5)
        self.amenities_var = ctk.StringVar(value="со всеми удобствами")
        amenities_options = ["со всеми удобствами", "с частичными удобствами", "без удобств"]
        for option in amenities_options:
            ctk.CTkRadioButton(amenities_frame, text=option, 
                              variable=self.amenities_var, value=option).pack(anchor="w", padx=20, pady=2)
        
        ownership_frame = ctk.CTkFrame(main_frame)
        ownership_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(ownership_frame, text="Собственность:").pack(anchor="w", padx=5)
        self.ownership = ctk.CTkEntry(ownership_frame,
                                     placeholder_text="Например: Иванова М.П., муниципальная, долевая и т.д.")
        self.ownership.pack(fill="x", padx=5, pady=2)
        
        # Чекбокс "Долевая собственность"
        self.shared_ownership_var = ctk.BooleanVar(value=False)
        self.shared_ownership_checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Долевая собственность",
            variable=self.shared_ownership_var,
            command=self.on_shared_ownership_toggle
        )
        self.shared_ownership_checkbox.pack(anchor="w", padx=10, pady=5)
    
    def setup_income_tab(self):
        """Вкладка информации о доходах"""
        main_frame = ctk.CTkFrame(self.income_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="💰 ДОХОДЫ СЕМЬИ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        income_scrollframe = ctk.CTkScrollableFrame(main_frame, height=500)
        income_scrollframe.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Привязываем прокрутку колесиком мыши к этому фрейму
        try:
            income_scrollframe.bind("<MouseWheel>", self._on_mousewheel)
            income_scrollframe.bind("<Button-4>", self._on_mousewheel)
            income_scrollframe.bind("<Button-5>", self._on_mousewheel)
        except:
            # Если bind не поддерживается, пропускаем
            pass
        
        self.income_fields = {}
        
        # Зарплата матери
        self.income_fields['mother_salary'] = self.create_income_field(
            income_scrollframe, "Зарплата матери (руб.):", "mother_salary"
        )
        
        # Зарплата отца
        self.income_fields['father_salary'] = self.create_income_field(
            income_scrollframe, "Зарплата отца (руб.):", "father_salary"
        )
        
        # Единое пособие
        unified_benefit_frame = ctk.CTkFrame(income_scrollframe)
        unified_benefit_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(unified_benefit_frame, text="Единое пособие (руб.):").pack(anchor="w", padx=5)
        
        unified_entry_frame = ctk.CTkFrame(unified_benefit_frame, fg_color="transparent")
        unified_entry_frame.pack(fill="x", padx=5, pady=2)
        self.unified_benefit_entry = ctk.CTkEntry(unified_entry_frame, placeholder_text="Автоподсчет или введите сумму")
        self.unified_benefit_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(unified_entry_frame, text="0", width=40,
                     command=lambda: self.unified_benefit_entry.delete(0, 'end')).pack(side="left", padx=5)
        
        calculation_frame = ctk.CTkFrame(income_scrollframe)
        calculation_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(calculation_frame, text="📊 Автоподсчет единого пособия:",
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=2)
        
        children_count_frame = ctk.CTkFrame(calculation_frame, fg_color="transparent")
        children_count_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(children_count_frame, text="Количество детей:").pack(side="left", padx=5)
        self.unified_children_count = ctk.CTkEntry(children_count_frame, width=50, placeholder_text="Введите число")
        self.unified_children_count.pack(side="left", padx=5)
        
        percentage_frame = ctk.CTkFrame(calculation_frame, fg_color="transparent")
        percentage_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(percentage_frame, text="Процент пособия:").pack(side="left", padx=5)
        self.unified_percentage_var = ctk.StringVar(value="100%")
        percentages = ["100%", "75", "50%"]
        for perc in percentages:
            ctk.CTkRadioButton(percentage_frame, text=perc,
                              variable=self.unified_percentage_var, value=perc,
                              command=self.calculate_unified_benefit).pack(side="left", padx=10)
        
        calculate_button_frame = ctk.CTkFrame(calculation_frame, fg_color="transparent")
        calculate_button_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(calculate_button_frame, text="🧮 Рассчитать пособие",
                     command=self.calculate_unified_benefit, width=150).pack(side="left", padx=5)
        
        large_family_frame = ctk.CTkFrame(income_scrollframe)
        large_family_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(large_family_frame, text="Пособие по многодетности (руб.):").pack(anchor="w", padx=5)
        
        large_family_checkboxes_frame = ctk.CTkFrame(large_family_frame, fg_color="transparent")
        large_family_checkboxes_frame.pack(fill="x", padx=5, pady=2)
        
        self.large_family_benefit_var = ctk.StringVar(value="")
        large_family_options = ["1900", "2700", "3500"]
        for option in large_family_options:
            ctk.CTkRadioButton(large_family_checkboxes_frame, text=option,
                              variable=self.large_family_benefit_var, value=option,
                              command=self.on_large_family_benefit_change).pack(side="left", padx=10)
        
        large_family_entry_frame = ctk.CTkFrame(large_family_frame, fg_color="transparent")
        large_family_entry_frame.pack(fill="x", padx=5, pady=2)
        self.large_family_benefit_entry = ctk.CTkEntry(large_family_entry_frame,
                                                      placeholder_text="Или введите другую сумму")
        self.large_family_benefit_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(large_family_entry_frame, text="0", width=40,
                     command=lambda: self.clear_large_family_benefit()).pack(side="left", padx=5)
        
        # НОВОЕ: Общие доходы семьи
        self.income_fields['general_income'] = self.create_income_field(
            income_scrollframe, "Общие доходы семьи (руб.):", "general_income"
        )
        
        # НОВОЕ: Пенсия матери (перемещена ниже пособия по многодетности)
        self.income_fields['mother_pension'] = self.create_income_field(
            income_scrollframe, "Пенсия матери (руб.):", "mother_pension"
        )
        
        # НОВОЕ: Пенсия отца (перемещена ниже пособия по многодетности)
        self.income_fields['father_pension'] = self.create_income_field(
            income_scrollframe, "Пенсия отца (руб.):", "father_pension"
        )
        
        self.income_fields['survivor_pension'] = self.create_income_field(
            income_scrollframe, "Пенсия по потере кормильца (руб.):", "survivor_pension"
        )
        
        self.income_fields['alimony'] = self.create_income_field(
            income_scrollframe, "Алименты (руб.):", "alimony"
        )
        
        self.income_fields['disability_pension'] = self.create_income_field(
            income_scrollframe, "Пенсия по инвалидности (руб.):", "disability_pension"
        )
        
        self.income_fields['child_disability_care'] = self.create_income_field(
            income_scrollframe, "Уход за ребенком-инвалидом (руб.):", "child_disability_care"
        )
        
        self.income_fields['child_disability_pension'] = self.create_income_field(
            income_scrollframe, "Пенсия ребенка-инвалида (руб.):", "child_disability_pension"
        )
        
        other_frame = ctk.CTkFrame(income_scrollframe)
        other_frame.pack(fill="x", padx=5, pady=10)
        ctk.CTkLabel(other_frame, text="📝 Другие доходы (укажите в свободной форме):", 
                    font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=5)
        self.other_incomes_text = ctk.CTkTextbox(other_frame, height=100)
        self.other_incomes_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        clear_frame = ctk.CTkFrame(main_frame)
        clear_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(clear_frame, text="🧹 Очистить все доходы", 
                     command=self.clear_all_incomes, fg_color="orange").pack()
    
    def on_large_family_benefit_change(self):
        """Обработчик изменения чекбокса пособия по многодетности"""
        selected_value = self.large_family_benefit_var.get()
        if selected_value:
            self.large_family_benefit_entry.delete(0, 'end')
            self.large_family_benefit_entry.insert(0, selected_value)
    
    def clear_large_family_benefit(self):
        """Очистка пособия по многодетности"""
        self.large_family_benefit_var.set("")
        self.large_family_benefit_entry.delete(0, 'end')
    
    def calculate_unified_benefit(self):
        """Автоподсчет единого пособия"""
        try:
            children_count_str = self.unified_children_count.get().strip()
            children_count_str = self.clean_numeric_field(children_count_str)
            if not children_count_str:
                messagebox.showwarning("Внимание", "Введите количество детей для расчета пособия")
                return
            children_count = int(children_count_str)
            if children_count <= 0:
                messagebox.showwarning("Внимание", "Количество детей должно быть положительным числом")
                return
            
            percentage_str = self.unified_percentage_var.get()
            percentage = float(percentage_str.replace('%', '')) / 100
            
            benefit_per_child = self.BASE_UNIFIED_BENEFIT * percentage
            total_benefit = benefit_per_child * children_count
            
            total_benefit = round(total_benefit)
            
            self.unified_benefit_entry.delete(0, 'end')
            self.unified_benefit_entry.insert(0, str(total_benefit))
            
            messagebox.showinfo("Расчет пособия", 
                              f"Расчет единого пособия:\n"
                              f"Количество детей: {children_count}\n"
                              f"Процент: {percentage_str}\n"
                              f"На одного ребенка: {benefit_per_child:.0f} руб.\n"
                              f"Общая сумма: {total_benefit} руб.")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество детей (целое число)")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка расчета: {str(e)}")
    
    def create_income_field(self, parent, label, key):
        """Создание поля для ввода дохода"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(frame, text=label).pack(anchor="w", padx=5)
        
        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x", padx=5, pady=2)
        entry = ctk.CTkEntry(entry_frame, placeholder_text="Введите сумму или оставьте пустым")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(entry_frame, text="0", width=40,
                     command=lambda e=entry: e.delete(0, 'end')).pack(side="left", padx=5)
        
        return entry
    
    def clear_all_incomes(self):
        """Очистка всех полей доходов"""
        if messagebox.askyesno("Подтверждение", "Очистить все поля доходов?"):
            for entry in self.income_fields.values():
                entry.delete(0, 'end')
            self.unified_benefit_entry.delete(0, 'end')
            self.unified_children_count.delete(0, 'end')
            self.unified_percentage_var.set("100%")
            self.large_family_benefit_var.set("")
            self.large_family_benefit_entry.delete(0, 'end')
            if 'general_income' in self.income_fields:
                self.income_fields['general_income'].delete(0, 'end')
            self.other_incomes_text.delete("1.0", "end")
    
    def setup_adpi_tab(self):
        """Вкладка информации об АДПИ"""
        main_frame = ctk.CTkFrame(self.adpi_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="📟 ИНФОРМАЦИЯ ОБ АДПИ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        has_adpi_frame = ctk.CTkFrame(main_frame)
        has_adpi_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(has_adpi_frame, text="АДПИ установлен?").pack(anchor="w", padx=5)
        self.adpi_var = ctk.StringVar(value="нет")
        ctk.CTkRadioButton(has_adpi_frame, text="Да", 
                          variable=self.adpi_var, value="да").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(has_adpi_frame, text="Нет", 
                          variable=self.adpi_var, value="нет").pack(anchor="w", padx=20, pady=2)
        
        install_frame = ctk.CTkFrame(main_frame)
        install_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(install_frame, text="Дата установки АДПИ (ДД.ММ.ГГГГ):").pack(anchor="w", padx=5)
        self.install_date = ctk.CTkEntry(install_frame, placeholder_text="Автоматически заполняется из файла АДПИ")
        self.install_date.pack(fill="x", padx=5, pady=2)
        
        check_frame = ctk.CTkFrame(main_frame)
        check_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(check_frame, text="Дата проверки АДПИ (ДД.ММ.ГГГГ):").pack(anchor="w", padx=5)
        self.check_date = ctk.CTkEntry(check_frame, placeholder_text="Автоматически заполняется из файла АДПИ")
        self.check_date.pack(fill="x", padx=5, pady=2)
        
        clear_dates_frame = ctk.CTkFrame(main_frame)
        clear_dates_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(clear_dates_frame, text="🧹 Очистить даты АДПИ", 
                     command=self.clear_adpi_dates, fg_color="orange").pack()
    
    def clear_adpi_dates(self):
        """Очистка дат АДПИ"""
        self.install_date.delete(0, 'end')
        self.check_date.delete(0, 'end')
        self.adpi_var.set("нет")
    
    def on_shared_ownership_toggle(self):
        """Обработчик чекбокса 'Долевая собственность'"""
        ownership_text = self.ownership.get().strip()
        if self.shared_ownership_var.get():
            # Если чекбокс отмечен, добавляем "долевая" в поле собственности
            if "долевая" not in ownership_text.lower():
                if ownership_text:
                    self.ownership.delete(0, 'end')
                    self.ownership.insert(0, f"{ownership_text}, долевая")
                else:
                    self.ownership.insert(0, "долевая")
        else:
            # Если чекбокс снят, убираем "долевая" из поля собственности
            if "долевая" in ownership_text.lower():
                # Убираем "долевая" и лишние запятые
                import re
                updated_text = re.sub(r',\s*долевая\b', '', ownership_text, flags=re.IGNORECASE)
                updated_text = re.sub(r'\bдолевая\s*,?', '', updated_text, flags=re.IGNORECASE)
                updated_text = updated_text.strip().strip(',')
                self.ownership.delete(0, 'end')
                self.ownership.insert(0, updated_text.strip())
    
    def setup_manage_tab(self):
        """Вкладка управления JSON файлом"""
        main_frame = ctk.CTkFrame(self.manage_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Информация о семьях наверху
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(info_frame, text="📋 СПИСОК СЕМЕЙ",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Создаем фрейм со скроллом для списка семей
        families_scroll_frame = ctk.CTkScrollableFrame(info_frame, height=150)
        families_scroll_frame.pack(fill="x", padx=10, pady=5)
        
        # Добавляем метку с информацией о семьях внутрь скроллируемого фрейма
        self.families_info = ctk.CTkLabel(families_scroll_frame, text="Список семей пуст", justify="left", anchor="nw")
        self.families_info.pack(fill="x")
        
        # Основной фрейм для остальных элементов
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Фрейм для кнопок
        buttons_frame = ctk.CTkFrame(content_frame)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        row1_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row1_frame.pack(fill="x", pady=5)
        ctk.CTkButton(row1_frame, text="💾 Сохранить в JSON",
                    command=self.save_to_json, width=200, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(row1_frame, text="➕ Добавить семью в список",
                    command=self.add_to_families_list, width=200).pack(side="left", padx=5)
        ctk.CTkButton(row1_frame, text="📋 Просмотр всего списка",
                    command=self.preview_all_families, width=200).pack(side="left", padx=5)
        
        row2_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row2_frame.pack(fill="x", pady=5)
        ctk.CTkButton(row2_frame, text="📄 Просмотр текущей семьи",
                    command=self.preview_current_family, width=200).pack(side="left", padx=5)
        ctk.CTkButton(row2_frame, text="📂 Загрузить JSON",
                    command=self.load_json, width=200).pack(side="left", padx=5)
        ctk.CTkButton(row2_frame, text="🔄 Загрузить семью из списка",
                    command=self.load_family_from_list, width=200).pack(side="left", padx=5)
        
        row3_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row3_frame.pack(fill="x", pady=5)
        ctk.CTkButton(row3_frame, text="🧹 Очистить форму",
                    command=self.clear_form, width=200, fg_color="orange").pack(side="left", padx=5)
        ctk.CTkButton(row3_frame, text="🗑️ Удалить семью из списка",
                    command=self.delete_family_from_list, width=200, fg_color="red").pack(side="left", padx=5)
        
        row4_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row4_frame.pack(fill="x", pady=5)
        ctk.CTkButton(row4_frame, text="🗑️ Очистить список семей",
                    command=self.clear_families_list, width=200, fg_color="darkred").pack(side="left", padx=5)
        
        row5_frame = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row5_frame.pack(fill="x", pady=10)
        ctk.CTkButton(row5_frame, text="🚀 Старт базы данных",
                    command=self.start_database_system, width=200,
                    fg_color="purple", hover_color="#6a0dad").pack(side="left", padx=5)
        
        # Фрейм для предпросмотра JSON (уменьшенный)
        preview_frame = ctk.CTkFrame(content_frame)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(preview_frame, text="📋 ПРЕДПРОСМОТР JSON",
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        preview_text_frame = ctk.CTkFrame(preview_frame)
        preview_text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.preview_text = scrolledtext.ScrolledText(preview_text_frame, height=8, width=80)  # Уменьшенная высота
        self.preview_text.pack(fill="both", expand=True)
        self.preview_text.config(state="normal")
        self.preview_text.insert("1.0", "Здесь будет отображаться JSON структура...")
        self.preview_text.config(state="disabled")
        
        # Привязываем прокрутку колесиком мыши к этому виджету
        try:
            self.preview_text.bind("<MouseWheel>", self._on_mousewheel)
            self.preview_text.bind("<Button-4>", self._on_mousewheel)
            self.preview_text.bind("<Button-5>", self._on_mousewheel)
        except:
            # Если bind не поддерживается, пропускаем
            pass
    
    def start_database_system(self):
        """Запуск базы данных и массового обработчика"""
        try:
            if self.families:
                self.autosave_families()
            
            current_os = platform.system()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            def run_database():
                try:
                    if current_os == "Linux" or current_os == "RedOS":
                        db_script = os.path.join(script_dir, "database_client.sh")
                        if os.path.exists(db_script):
                            os.chmod(db_script, 0o755)
                            subprocess.Popen(["bash", db_script])
                        else:
                            messagebox.showerror("Ошибка", f"Файл database_client.sh не найден в {script_dir}")
                    elif current_os == "Windows":
                        db_script = os.path.join(script_dir, "database_client.bat")
                        if os.path.exists(db_script):
                            subprocess.Popen([db_script], shell=True)
                        else:
                            messagebox.showerror("Ошибка", f"Файл database_client.bat не найден в {script_dir}")
                    else:
                        messagebox.showwarning("Предупреждение", 
                                            f"Операционная система {current_os} не поддерживается")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось запустить базу данных: {str(e)}")
            
            def run_mass_processor():
                try:
                    mass_processor_script = os.path.join(script_dir, "massform.py")
                    if os.path.exists(mass_processor_script):
                        if current_os == "Windows":
                            subprocess.Popen(['python', mass_processor_script])
                        else:
                            subprocess.Popen(["python3", mass_processor_script])
                    else:
                        messagebox.showerror("Ошибка", f"Файл massform.py не найден в {script_dir}")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось запустить массовый обработчик: {str(e)}")
            
            db_thread = threading.Thread(target=run_database, daemon=True)
            db_thread.start()
            
            import time
            self.log_message("⏳ Запускаю базу данных...")
            time.sleep(3)
            
            self.log_message("🚀 Запускаю массовый обработчик...")
            run_mass_processor()
            
            messagebox.showinfo("Успех", 
                            "✅ База данных запущена\n"
                            "📦 Массовый обработчик запущен\n"
                            "Теперь вы можете работать с базой данных.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить систему: {str(e)}")
    
    def validate_date(self, date_string):
        """Проверка корректности даты"""
        try:
            date_string = self.clean_date(date_string)
            dt = datetime.strptime(date_string, '%d.%m.%Y')
            current_year = datetime.now().year
            if dt.year < 1900 or dt.year > current_year + 1:
                return False
            if dt.month < 1 or dt.month > 12:
                return False
            if dt.day < 1 or dt.day > 31:
                return False
            return True
        except ValueError:
            return False
    
    def validate_number(self, value):
        """Проверка корректности числа"""
        try:
            if not value:
                return True
            value = self.clean_numeric_field(value)
            float(value)
            return True
        except ValueError:
            return False
    
    def validate_phone(self, phone):
        """Проверка корректности телефона"""
        if not phone:
            return True
        phone = self.clean_phone(phone)
        if len(phone) != 11:
            return False
        if not phone.startswith('7'):
            return False
        if not phone.isdigit():
            return False
        return True
    
    def validate_family_data(self):
        """Проверка данных семьи"""
        errors = []
        
        mother_fio = self.mother_fio.get().strip()
        mother_fio = self.clean_fio(mother_fio)
        # ИЗМЕНЕНО: Поле матери больше не является обязательным
        # if not mother_fio:
        #     errors.append("Не указано ФИО матери")
        
        # Проверяем, что хотя бы одно из полей (мать или отец) заполнено
        father_fio = self.father_fio.get().strip()
        father_fio = self.clean_fio(father_fio)
        if not mother_fio and not father_fio:
            errors.append("Должно быть указано ФИО матери или отца")
        
        mother_birth = self.mother_birth.get().strip()
        mother_birth = self.clean_date(mother_birth)
        if mother_birth:
            try:
                birth_dt = datetime.strptime(mother_birth, '%d.%m.%Y')
                if birth_dt.year > 2003:
                    errors.append(f"Мать не может родиться после 2003 года (указан {birth_dt.year})")
                elif birth_dt.year > 2000:
                    if not messagebox.askyesno("Подтверждение",
                                              f"Год рождения матери {birth_dt.year} > 2000.\n"
                                              "Это очень редко встречается для родителя.\n"
                                              "Продолжить использование этой даты?"):
                        errors.append("Некорректная дата рождения матери")
            except:
                errors.append("Неверный формат даты рождения матери")
        
        father_fio = self.father_fio.get().strip()
        father_fio = self.clean_fio(father_fio)
        father_birth = self.father_birth.get().strip()
        father_birth = self.clean_date(father_birth)
        if father_fio and father_birth:
            try:
                birth_dt = datetime.strptime(father_birth, '%d.%m.%Y')
                if birth_dt.year > 2003:
                    errors.append(f"Отец не может родиться после 2003 года (указан {birth_dt.year})")
                elif birth_dt.year > 2000:
                    if not messagebox.askyesno("Подтверждение",
                                              f"Год рождения отца {birth_dt.year} > 2000.\n"
                                              "Это очень редко встречается для родителя.\n"
                                              "Продолжить использование этой даты?"):
                        errors.append("Некорректная дата рождения отца")
            except:
                errors.append("Неверный формат даты рождения отца")
        
        for i, child in enumerate(self.children_entries):
            child_fio = child['fio'].get().strip()
            child_fio = self.clean_fio(child_fio)
            child_birth = child['birth'].get().strip()
            child_birth = self.clean_date(child_birth)
            if child_fio and child_birth:
                try:
                    birth_dt = datetime.strptime(child_birth, '%d.%m.%Y')
                    # НОВОЕ: Ребенок не может родиться до 2000 года
                    if birth_dt.year < 2000:
                        errors.append(f"Ребенок {i+1} не может родиться до 2000 года (указан {birth_dt.year})")
                except:
                    errors.append(f"Неверный формат даты рождения ребенка {i+1}")
        
        rooms = self.rooms.get().strip()
        rooms = self.clean_numeric_field(rooms)
        if rooms and not self.validate_number(rooms):
            errors.append("Количество комнат должно быть числом")
        
        square = self.square.get().strip()
        square = self.clean_numeric_field(square)
        if square and not self.validate_number(square):
            errors.append("Площадь должна быть числом")
        
        install_date = self.install_date.get().strip()
        install_date = self.clean_date(install_date)
        if install_date and not self.validate_date(install_date):
            errors.append("Неверный формат даты установки АДПИ")
        
        check_date = self.check_date.get().strip()
        check_date = self.clean_date(check_date)
        if check_date and not self.validate_date(check_date):
            errors.append("Неверный формат даты проверки АДПИ")
        
        for key, entry in self.income_fields.items():
            value = entry.get().strip()
            value = self.clean_numeric_field(value)
            if value and not self.validate_number(value):
                errors.append(f"Доход '{key}' должен быть числом")
        
        unified_benefit = self.unified_benefit_entry.get().strip()
        unified_benefit = self.clean_numeric_field(unified_benefit)
        if unified_benefit and not self.validate_number(unified_benefit):
            errors.append("Единое пособие должно быть числом")
        
        large_family_benefit = self.large_family_benefit_entry.get().strip()
        large_family_benefit = self.clean_numeric_field(large_family_benefit)
        if large_family_benefit and not self.validate_number(large_family_benefit):
            errors.append("Пособие по многодетности должно быть числом")
        
        phone = self.phone_entry.get().strip()
        phone = self.clean_phone(phone)
        if phone and not self.validate_phone(phone):
            errors.append("Неверный формат телефона. Должен быть в формате 7XXXXXXXXXX")
        
        return errors
    
    def collect_family_data(self):
        """Сбор данных из формы в словарь"""
        family_data = {}
        
        family_data['mother_fio'] = self.clean_fio(self.mother_fio.get().strip())
        family_data['mother_birth'] = self.clean_date(self.mother_birth.get().strip())
        family_data['mother_work'] = self.clean_string(self.mother_work.get().strip())
        
        family_data['mother_disability_care'] = self.mother_disability_care_var.get()
        
        # НОВОЕ: Сохраняем информацию о том, что мать не работает
        family_data['mother_not_working'] = self.mother_not_working_var.get()
        
        father_fio = self.clean_fio(self.father_fio.get().strip())
        if father_fio:
            family_data['father_fio'] = father_fio
            family_data['father_birth'] = self.clean_date(self.father_birth.get().strip())
            family_data['father_work'] = self.clean_string(self.father_work.get().strip())
            
            # НОВОЕ: Сохраняем информацию о том, что отец не работает
            family_data['father_not_working'] = self.father_not_working_var.get()
        
        children = []
        for child in self.children_entries:
            child_fio = self.clean_fio(child['fio'].get().strip())
            if child_fio:
                child_data = {
                    'fio': child_fio,
                    'birth': self.clean_date(child['birth'].get().strip()),
                    'education': self.clean_string(child['education'].get().strip())
                }
                # Добавляем информацию о домашнем ребенке, если чекбокс установлен
                if 'home_edu_var' in child and child['home_edu_var'].get():
                    child_data['home_education'] = True
                children.append(child_data)
        if children:
            family_data['children'] = children
        
        phone = self.clean_phone(self.phone_entry.get().strip())
        if phone:
            family_data['phone_number'] = phone
        
        address = self.clean_address(self.address.get().strip())
        if address:
            family_data['address'] = address
        
        rooms = self.clean_numeric_field(self.rooms.get().strip())
        if rooms:
            family_data['rooms'] = rooms
        
        square = self.clean_numeric_field(self.square.get().strip())
        if square:
            family_data['square'] = square
        
        family_data['amenities'] = self.amenities_var.get()
        
        ownership = self.clean_string(self.ownership.get().strip())
        if ownership:
            family_data['ownership'] = ownership
        
        # Обработка долевой собственности
        ownership_text = self.ownership.get().strip()
        if self.shared_ownership_var.get():
            # Если отмечен чекбокс "Долевая собственность", добавляем это в поле собственности
            if "долевая" not in ownership_text.lower():
                if ownership_text:
                    ownership_text += ", долевая"
                else:
                    ownership_text = "долевая"
        family_data['ownership'] = self.clean_string(ownership_text)
        
        family_data['adpi'] = self.adpi_var.get()
        
        install_date = self.clean_date(self.install_date.get().strip())
        if install_date:
            family_data['install_date'] = install_date
        
        check_date = self.clean_date(self.check_date.get().strip())
        if check_date:
            family_data['check_date'] = check_date
        
        incomes = {}
        
        # НОВОЕ: Сохраняем рассчитанное единое пособие, а не проценты
        unified_benefit = self.clean_numeric_field(self.unified_benefit_entry.get().strip())
        if unified_benefit:
            incomes['unified_benefit'] = unified_benefit
        
        large_family_benefit = self.clean_numeric_field(self.large_family_benefit_entry.get().strip())
        if large_family_benefit:
            incomes['large_family_benefit'] = large_family_benefit
        
        for key, entry in self.income_fields.items():
            value = self.clean_numeric_field(entry.get().strip())
            if value:
                incomes[key] = value
        
        if incomes:
            family_data.update(incomes)
        
        # НОВОЕ: Сохраняем общие доходы семьи
        general_income_value = self.clean_numeric_field(self.income_fields['general_income'].get().strip())
        if general_income_value:
            family_data['general_income'] = general_income_value
        
        children_count = self.clean_numeric_field(self.unified_children_count.get().strip())
        if children_count:
            family_data['unified_children_count'] = children_count
        
        percentage = self.unified_percentage_var.get()
        family_data['unified_percentage'] = percentage
        
        other_incomes = self.other_incomes_text.get("1.0", "end-1c").strip()
        other_incomes = self.clean_string(other_incomes)
        if other_incomes:
            family_data['other_incomes'] = other_incomes
        
        family_data = self.clean_family_data(family_data)
        return family_data
    
    def preview_current_family(self):
        """Предпросмотр текущей семьи в формате JSON"""
        errors = self.validate_family_data()
        if errors:
            messagebox.showerror("Ошибки валидации", "\n".join(errors))
            return
        
        family_data = self.collect_family_data()
        try:
            json_str = json.dumps(family_data, ensure_ascii=False, indent=2)
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", "end")
            self.preview_text.insert("1.0", json_str)
            self.preview_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сформировать JSON: {str(e)}")
    
    def add_to_families_list(self):
        """Добавление текущей семьи в список с автосохранением"""
        errors = self.validate_family_data()
        if errors:
            messagebox.showerror("Ошибки валидации", "\n".join(errors))
            return
        
        family_data = self.collect_family_data()
        
        for i, existing_family in enumerate(self.families):
            if existing_family.get('mother_fio') == family_data.get('mother_fio'):
                if messagebox.askyesno("Подтверждение", 
                                      f"Семья с матерью {family_data.get('mother_fio')} уже есть в списке.\nЗаменить?"):
                    self.families[i] = family_data
                    messagebox.showinfo("Успех", "Семья обновлена в списке")
                    self.update_families_info()
                    self.autosave_families()
                    
                    return
                else:
                    return
        
        self.families.append(family_data)
        messagebox.showinfo("Успех", f"Семья добавлена в список. Всего семей: {len(self.families)}")
        
        self.clear_form_for_new_family()
        self.update_families_info()
        
        self.autosave_families()
        
    
    def delete_family_from_list(self):
        """Удаление конкретной семьи из списка"""
        if not self.families:
            messagebox.showwarning("Предупреждение", "Список семей пуст")
            return
        
        families_list = ""
        for i, family in enumerate(self.families):
            mother_name = family.get('mother_fio', 'Без имени')
            children_count = len(family.get('children', []))
            phone = family.get('phone_number', 'нет телефона')
            families_list += f"{i+1}. {mother_name} (детей: {children_count}, тел: {phone})\n"
        
        dialog = ctk.CTkInputDialog(
            text=f"Введите номер семьи для удаления (1-{len(self.families)}):\n{families_list}",
            title="Удаление семьи из списка"
        )
        
        try:
            family_num = int(dialog.get_input())
            if 1 <= family_num <= len(self.families):
                family_to_delete = self.families[family_num - 1]
                mother_name = family_to_delete.get('mother_fio', 'Без имени')
                if messagebox.askyesno("Подтверждение", 
                                     f"Вы уверены, что хотите удалить семью {family_num}?\n"
                                     f"Мать: {mother_name}\n"
                                     f"Всего семей в списке: {len(self.families)}"):
                    deleted_family = self.families.pop(family_num - 1)
                    
                    if self.current_family_index >= len(self.families):
                        self.current_family_index = max(0, len(self.families) - 1)
                    
                    messagebox.showinfo("Успех", f"Семья удалена: {mother_name}\nОсталось семей: {len(self.families)}")
                    
                    self.update_families_info()
                    self.autosave_families()
                    
                    if self.families:
                        self.load_family_into_form(self.families[0])
                        self.current_family_index = 0
                    else:
                        self.clear_form()
                else:
                    return
            else:
                messagebox.showerror("Ошибка", f"Номер должен быть от 1 до {len(self.families)}")
        except (ValueError, TypeError):
            messagebox.showerror("Ошибка", "Введите корректный номер")
    
    def clear_form_for_new_family(self):
        """Очистка полей для ввода новой семьи"""
        self.mother_fio.delete(0, 'end')
        self.mother_birth.delete(0, 'end')
        self.mother_work.delete(0, 'end')
        self.mother_disability_care_var.set(False)
        self.mother_not_working_var.set(False)
        self.father_fio.delete(0, 'end')
        self.father_birth.delete(0, 'end')
        self.father_work.delete(0, 'end')
        self.father_not_working_var.set(False)
        self.phone_entry.delete(0, 'end')
        
        self.search_fio_input.delete(0, 'end')
        
        while len(self.children_entries) > 1:
            self.remove_child_entry()
        if self.children_entries:
            self.children_entries[0]['fio'].delete(0, 'end')
            self.children_entries[0]['birth'].delete(0, 'end')
            self.children_entries[0]['education'].delete(0, 'end')
        
        self.clear_all_incomes()
        
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "Форма очищена. Можно вводить новую семью.")
        self.preview_text.config(state="disabled")
        
        self.tabview.set("🤖 Автоопределение")
    
    def update_families_info(self):
        """Обновление информации о списке семей"""
        if not self.families:
            self.families_info.configure(text="Список семей пуст")
        else:
            families_text = f"Семей в списке: {len(self.families)}"
            for i, family in enumerate(self.families[:3]):
                mother_name = family.get('mother_fio', 'Без имени')
                children_count = len(family.get('children', []))
                phone = family.get('phone_number', 'нет телефона')
                families_text += f"\n{i+1}. {mother_name} (детей: {children_count}, тел: {phone})"
            if len(self.families) > 3:
                families_text += f"\n... и еще {len(self.families) - 3} семей"
            self.families_info.configure(text=families_text)
    
    def preview_all_families(self):
        """Предпросмотр всего списка семей"""
        if not self.families:
            messagebox.showinfo("Информация", "Список семей пуст")
            return
        
        try:
            cleaned_families = [self.clean_family_data(family) for family in self.families]
            json_str = json.dumps(cleaned_families, ensure_ascii=False, indent=2)
            
            preview_window = ctk.CTkToplevel(self.app)
            preview_window.title(f"Просмотр всех семей ({len(self.families)} шт.)")
            preview_window.geometry("800x600")
            
            text_widget = scrolledtext.ScrolledText(preview_window, width=90, height=30)
            text_widget.pack(fill="both", expand=True, padx=20, pady=20)
            text_widget.insert("1.0", json_str)
            text_widget.config(state="disabled")
            
            # Привязываем прокрутку колесиком мыши к этому виджету
            try:
                text_widget.bind("<MouseWheel>", self._on_mousewheel)
                text_widget.bind("<Button-4>", self._on_mousewheel)
                text_widget.bind("<Button-5>", self._on_mousewheel)
            except:
                # Если bind не поддерживается, пропускаем
                pass
            
            save_button = ctk.CTkButton(preview_window, text="💾 Сохранить как JSON",
                                       command=lambda: self.save_json_from_preview(json_str, preview_window))
            save_button.pack(pady=10)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сформировать JSON: {str(e)}")
    
    def save_json_from_preview(self, json_str, window):
        """Сохранение JSON из окна предпросмотра"""
        initial_dir = self.last_json_directory if self.last_json_directory else None
        file_path = filedialog.asksaveasfilename(
            title="Сохранить JSON файл",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if file_path:
            try:
                self.last_json_directory = os.path.dirname(file_path)
                self.save_config()
                
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(json_str)
                
                messagebox.showinfo("Успех", f"Файл сохранен:\n{file_path}")
                window.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def save_to_json(self):
        """Сохранение списка семей в JSON файл"""
        if not self.families:
            messagebox.showwarning("Предупреждение", "Список семей пуст")
            return
        
        initial_dir = self.last_json_directory if self.last_json_directory else None
        file_path = filedialog.asksaveasfilename(
            title="Сохранить JSON файл",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=initial_dir
        )
        if not file_path:
            return
        
        try:
            self.last_json_directory = os.path.dirname(file_path)
            self.save_config()
            
            cleaned_families = [self.clean_family_data(family) for family in self.families]
            
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(cleaned_families, file, ensure_ascii=False, indent=2)
            
            self.current_file_path = file_path
            
            self.clear_form_for_new_family()
            
            messagebox.showinfo("Успех", f"Файл сохранен успешно!\n{file_path}\nСемей: {len(self.families)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def load_json(self, file_path=None):
        """Загрузка JSON файла"""
        if not file_path:
            initial_dir = self.last_json_directory if self.last_json_directory else None
            file_path = filedialog.askopenfilename(
                title="Выберите JSON файл",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=initial_dir
            )
        if not file_path:
            return
        
        try:
            self.last_json_directory = os.path.dirname(file_path)
            self.save_config()
            
            with open(file_path, 'r', encoding='utf-8') as file:
                loaded_families = json.load(file)
            
            if not isinstance(loaded_families, list):
                messagebox.showerror("Ошибка", "JSON файл должен содержать массив семей")
                return
            
            loaded_families = [self.clean_family_data(family) for family in loaded_families]
            
            if self.families:
                result = messagebox.askyesnocancel(
                    "Подтверждение",
                    f"Найдено {len(loaded_families)} семей в файле.\n"
                    f"В текущем списке {len(self.families)} семей.\n"
                    "Выберите действие:\n"
                    "Да - заменить текущий список\n"
                    "Нет - добавить к текущему списку\n"
                    "Отмена - отменить загрузку"
                )
                if result is None:
                    return
                elif result:
                    self.families = loaded_families
                    messagebox.showinfo("Успех", f"Список заменен. Теперь {len(self.families)} семей")
                else:
                    cleaned_new_families = [self.clean_family_data(family) for family in loaded_families]
                    self.families.extend(cleaned_new_families)
                    messagebox.showinfo("Успех", f"Семьи добавлены. Теперь {len(self.families)} семей")
            else:
                self.families = loaded_families
                messagebox.showinfo("Успех", f"Загружено {len(self.families)} семей")
            
            self.current_file_path = file_path
            self.update_families_info()
            
            self.autosave_families()
            
            if self.families:
                cleaned_family = self.clean_family_data(self.families[0])
                self.load_family_into_form(cleaned_family)
                self.current_family_index = 0
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")
    
    def load_family_from_list(self):
        """Загрузка семьи из списка в форму"""
        if not self.families:
            messagebox.showwarning("Предупреждение", "Список семей пуст")
            return
        
        dialog = ctk.CTkInputDialog(
            text=f"Введите номер семьи (1-{len(self.families)}):",
            title="Выбор семьи"
        )
        
        try:
            family_num = int(dialog.get_input())
            if 1 <= family_num <= len(self.families):
                family_data = self.clean_family_data(self.families[family_num - 1])
                self.load_family_into_form(family_data)
                self.current_family_index = family_num - 1
                messagebox.showinfo("Успех", f"Загружена семью {family_num}: {family_data.get('mother_fio', 'Без имени')}")
            else:
                messagebox.showerror("Ошибка", f"Номер должен быть от 1 до {len(self.families)}")
        except (ValueError, TypeError):
            messagebox.showerror("Ошибка", "Введите корректный номер")
    
    def load_family_into_form(self, family_data):
        """Загрузка данных семьи в форму"""
        self.clear_form()
        
        if 'mother_fio' in family_data:
            mother_fio = self.clean_fio(family_data['mother_fio'])
            self.mother_fio.insert(0, mother_fio)
        if 'mother_birth' in family_data:
            mother_birth = self.clean_date(family_data['mother_birth'])
            self.mother_birth.insert(0, mother_birth)
        if 'mother_work' in family_data:
            mother_work = self.clean_string(family_data['mother_work'])
            self.mother_work.insert(0, mother_work)
        
        if 'mother_disability_care' in family_data:
            self.mother_disability_care_var.set(family_data['mother_disability_care'])
            if family_data['mother_disability_care'] and not self.mother_work.get().strip():
                self.mother_work.insert(0, "уход за ребенком-инвалидом")
        
        # НОВОЕ: Загрузка чекбокса "Не работает" для матери
        if 'mother_not_working' in family_data:
            self.mother_not_working_var.set(family_data['mother_not_working'])
            if family_data['mother_not_working']:
                self.on_mother_not_working_toggle()
        
        if 'father_fio' in family_data:
            father_fio = self.clean_fio(family_data['father_fio'])
            self.father_fio.insert(0, father_fio)
        if 'father_birth' in family_data:
            father_birth = self.clean_date(family_data['father_birth'])
            self.father_birth.insert(0, father_birth)
        if 'father_work' in family_data:
            father_work = self.clean_string(family_data['father_work'])
            self.father_work.insert(0, father_work)
        
        # НОВОЕ: Загрузка чекбокса "Не работает" для отца
        if 'father_not_working' in family_data:
            self.father_not_working_var.set(family_data['father_not_working'])
            if family_data['father_not_working']:
                self.on_father_not_working_toggle()
        
        if 'children' in family_data:
            self.clear_all_children()
            for i, child in enumerate(family_data['children']):
                if i >= len(self.children_entries):
                    self.add_child_entry()
                if 'fio' in child:
                    child_fio = self.clean_fio(child['fio'])
                    self.children_entries[i]['fio'].insert(0, child_fio)
                if 'birth' in child:
                    child_birth = self.clean_date(child['birth'])
                    self.children_entries[i]['birth'].insert(0, child_birth)
                if 'education' in child:
                    child_education = self.clean_string(child['education'])
                    self.children_entries[i]['education'].insert(0, child_education)
                # Загружаем информацию о домашнем ребенке
                if 'home_education' in child and child['home_education'] and 'home_edu_var' in self.children_entries[i]:
                    self.children_entries[i]['home_edu_var'].set(True)
                    self.on_individual_home_education_toggle(self.children_entries[i]['home_edu_var'],
                                                            self.children_entries[i]['education'])
        
        if 'phone_number' in family_data:
            phone = self.clean_phone(family_data['phone_number'])
            self.phone_entry.insert(0, phone)
        
        if 'address' in family_data:
            address = self.clean_address(family_data['address'])
            self.address.insert(0, address)
        if 'rooms' in family_data:
            rooms = self.clean_numeric_field(str(family_data['rooms']))
            self.rooms.insert(0, rooms)
        if 'square' in family_data:
            square = self.clean_numeric_field(str(family_data['square']))
            self.square.insert(0, square)
        if 'amenities' in family_data:
            self.amenities_var.set(family_data['amenities'])
        if 'ownership' in family_data:
            ownership = self.clean_string(family_data['ownership'])
            self.ownership.delete(0, 'end')
            self.ownership.insert(0, ownership)
            # Автоматически установим чекбокс "долевая собственность", если в тексте есть "долевая"
            if "долевая" in ownership.lower():
                self.shared_ownership_var.set(True)
            else:
                self.shared_ownership_var.set(False)
        
        # Обновляем состояние чекбокса в соответствии с содержимым поля собственности
        ownership_text = self.ownership.get().strip()
        if "долевая" in ownership_text.lower():
            self.shared_ownership_var.set(True)
        else:
            self.shared_ownership_var.set(False)
        
        if 'adpi' in family_data:
            self.adpi_var.set(family_data['adpi'])
        if 'install_date' in family_data:
            install_date = self.clean_date(family_data['install_date'])
            self.install_date.insert(0, install_date)
        if 'check_date' in family_data:
            check_date = self.clean_date(family_data['check_date'])
            self.check_date.insert(0, check_date)
        
        income_fields_mapping = {
            'mother_salary': self.income_fields.get('mother_salary'),
            'father_salary': self.income_fields.get('father_salary'),
            'mother_pension': self.income_fields.get('mother_pension'),
            'father_pension': self.income_fields.get('father_pension'),
            'unified_benefit': self.unified_benefit_entry,
            'large_family_benefit': self.large_family_benefit_entry,
            'survivor_pension': self.income_fields.get('survivor_pension'),
            'alimony': self.income_fields.get('alimony'),
            'disability_pension': self.income_fields.get('disability_pension'),
            'child_disability_care': self.income_fields.get('child_disability_care'),
            'child_disability_pension': self.income_fields.get('child_disability_pension')
        }
        
        for key, field in income_fields_mapping.items():
            if key in family_data and field:
                value = self.clean_numeric_field(str(family_data[key]))
                field.delete(0, 'end')
                field.insert(0, value)
                if key == 'large_family_benefit':
                    benefit_value = str(family_data[key])
                    if benefit_value in ["1900", "2700", "3500"]:
                        self.large_family_benefit_var.set(benefit_value)
        
        # НОВОЕ: Загрузка общих доходов семьи
        if 'general_income' in family_data:
            general_income_value = self.clean_numeric_field(str(family_data['general_income']))
            if 'general_income' in self.income_fields:
                self.income_fields['general_income'].delete(0, 'end')
                self.income_fields['general_income'].insert(0, general_income_value)
        
        if 'unified_children_count' in family_data:
            children_count = self.clean_numeric_field(str(family_data['unified_children_count']))
            self.unified_children_count.delete(0, 'end')
            self.unified_children_count.insert(0, children_count)
        if 'unified_percentage' in family_data:
            self.unified_percentage_var.set(family_data['unified_percentage'])
        
        if 'other_incomes' in family_data:
            other_incomes = self.clean_string(family_data['other_incomes'])
            self.other_incomes_text.delete("1.0", "end")
            self.other_incomes_text.insert("1.0", other_incomes)
    
    def clear_form(self):
        """Очистка всех полей формы"""
        self.mother_fio.delete(0, 'end')
        self.mother_birth.delete(0, 'end')
        self.mother_work.delete(0, 'end')
        self.mother_disability_care_var.set(False)
        self.mother_not_working_var.set(False)
        self.father_fio.delete(0, 'end')
        self.father_birth.delete(0, 'end')
        self.father_work.delete(0, 'end')
        self.father_not_working_var.set(False)
        self.phone_entry.delete(0, 'end')
        
        for child in self.children_entries:
            child['fio'].delete(0, 'end')
            child['birth'].delete(0, 'end')
            child['education'].delete(0, 'end')
        
        self.address.delete(0, 'end')
        self.rooms.delete(0, 'end')
        self.square.delete(0, 'end')
        self.amenities_var.set("со всеми удобствами")
        self.ownership.delete(0, 'end')
        self.adpi_var.set("нет")
        self.install_date.delete(0, 'end')
        self.check_date.delete(0, 'end')
        
        self.clear_all_incomes()
        
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "Форма очищена. Заполните данные семьи.")
        self.preview_text.config(state="disabled")
    
    def clear_families_list(self):
        """Очистка списка семей"""
        if not self.families:
            return
        if messagebox.askyesno("Подтверждение", f"Удалить все {len(self.families)} семей из списка?"):
            self.families = []
            self.current_family_index = 0
            self.update_families_info()
            self.autosave_families()
            messagebox.showinfo("Успех", "Список семей очищен")
    
    def log_message(self, message):
        """Логирование сообщений в предпросмотр"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_text = f"[{timestamp}] {message}\n"
            
            self.preview_text.config(state="normal")
            self.preview_text.insert("end", log_text)
            self.preview_text.see("end")
            self.preview_text.config(state="disabled")
            
            print(log_text)
        except:
            pass
    
    def run(self):
        """Запуск приложения"""
        self.app.mainloop()

if __name__ == "__main__":
    app = EnhancedJSONFamilyCreatorGUI()
    app.run()