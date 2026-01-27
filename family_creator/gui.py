"""GUI компоненты для генератора JSON файлов"""

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
from utils.data_processing import clean_string, clean_fio, clean_address, clean_date, clean_phone, clean_numeric_field, clean_family_data
from utils.file_utils import setup_config_directory
from utils.validation import validate_family_data
from utils.excel_utils import load_register_file, load_adpi_file, parse_adpi_date, parse_single_date, normalize_fio, is_fio_similar
from utils.family_processor import FamilyDataProcessor
from common.gui_components import BaseGUI
from family_creator.json_generator import JSONFamilyCreator


class JSONFamilyCreatorGUI(BaseGUI):
    def __init__(self):
        super().__init__()
        self.app.title("📝 Улучшенный создатель JSON файлов для семей")
        self.app.geometry("1400x900")
        self.app.resizable(True, True)
        
        # Инициализация процессора данных
        self.processor = FamilyDataProcessor()
        
        # Инициализация генератора JSON
        self.json_creator = JSONFamilyCreator()
        
        # Инициализация переменных
        self.families = self.json_creator.families
        self.current_family_index = self.json_creator.current_family_index
        self.current_file_path = self.json_creator.current_file_path
        self.last_json_directory = self.json_creator.last_json_directory
        self.last_adpi_directory = self.json_creator.last_adpi_directory
        self.last_register_directory = self.json_creator.last_register_directory
        self.adpi_data = self.json_creator.adpi_data
        self.register_data = self.json_creator.register_data
        self.processed_families = self.json_creator.processed_families
        self.autosave_filename = self.json_creator.autosave_filename
        self.load_on_startup = self.json_creator.load_on_startup
        self.BASE_UNIFIED_BENEFIT = self.json_creator.BASE_UNIFIED_BENEFIT
        self.config_file = self.json_creator.config_file
        self.config = self.json_creator.config
        self.config_dir = self.json_creator.config_dir
        self.screenshots_dir = self.json_creator.screenshots_dir
        # Инициализация директорий для файлов реестра и АДПИ
        # Определяем путь к папке registry - используем правильную логику из старой версии
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.registry_dir = self.find_registry_directory(current_dir)
        self.register_dir = self.registry_dir
        self.adpi_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "adpi")
        
        # Инициализация переменных, которые могли быть пропущены
        self.last_register_directory = None
        self.last_adpi_directory = None
        
        # Настройка интерфейса
        self.setup_ui()
        
        # Загрузка начальных данных
        if self.load_on_startup:
            self.load_json_on_startup()
        
        # Загрузка последних файлов реестра и АДПИ
        self.load_last_files()
    
    def find_registry_directory(self, start_dir):
        """Поиск папки registry относительно текущего файла"""
        # Проверяем в текущей папке (рядом с gui.py)
        current_dir_registry = os.path.join(start_dir, "registry")
        if os.path.exists(current_dir_registry):
            return current_dir_registry
        
        # Проверяем в родительской папке
        parent_dir = os.path.dirname(start_dir)
        parent_registry = os.path.join(parent_dir, "registry")
        if os.path.exists(parent_registry):
            return parent_registry
        
        # Проверяем в родительской папке родительской папки (корень проекта)
        grandparent_dir = os.path.dirname(parent_dir)
        grandparent_registry = os.path.join(grandparent_dir, "registry")
        if os.path.exists(grandparent_registry):
            return grandparent_registry
        
        # Если не нашли, возвращаем папку рядом с gui.py
        # и она будет создана позже
        return current_dir_registry
    
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
        
        # Восстановлена кнопка автоопределения (перемещена выше)
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
            # Синхронизируем данные с процессором
            self.processor.register_data = self.register_data
        else:
            messagebox.showwarning("Внимание", "Нет сохраненных файлов реестра")
    
    def load_last_adpi(self):
        """Загрузка последнего файла АДПИ"""
        adpi_files = [f for f in os.listdir(self.adpi_dir) if f.lower().endswith(('.xls', '.xlsx', '.ods'))]
        if adpi_files:
            adpi_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.adpi_dir, x)), reverse=True)
            last_adpi = os.path.join(self.adpi_dir, adpi_files[0])
            self.load_adpi_xlsx(last_adpi, auto_load=True)
            # Синхронизируем данные с процессором
            self.processor.adpi_data = self.adpi_data
        else:
            messagebox.showwarning("Внимание", "Нет сохраненных файлов АДПИ")
    
    def load_register_file(self, file_path=None, auto_load=False):
        """Загрузка реестра многодетных из xls/xlsx файла"""
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
            self.json_creator.last_register_directory = self.last_register_directory
            self.json_creator.save_config()
            
            self.register_data = load_register_file(file_path)
            
            # Синхронизируем данные с процессором
            self.processor.register_data = self.register_data
            
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
    
    def load_adpi_xlsx(self, file_path=None, auto_load=False):
        """Загрузка данных АДПИ из xlsx файла"""
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
            self.json_creator.last_adpi_directory = self.last_adpi_directory
            self.json_creator.save_config()
            
            loaded_adpi_data = load_adpi_file(file_path)
            if loaded_adpi_data is not None:
                self.adpi_data = loaded_adpi_data
                # Синхронизируем данные с процессором
                self.processor.adpi_data = self.adpi_data
            else:
                self.adpi_data = {}
                self.processor.adpi_data = {}
                if not auto_load:
                    messagebox.showerror("Ошибка", "Не удалось загрузить данные АДПИ из файла")
                return
            
            
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
            # В любом случае сбрасываем данные, чтобы избежать использования старых
            self.adpi_data = {}
            self.processor.adpi_data = {}
    
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
    
    def auto_detect_family_from_register(self):
        """Автоматическое определение семьи из реестра с обработкой дубликатов"""
        # Проверяем, загружены ли данные реестра
        if not self.register_data:
            messagebox.showwarning("Предупреждение", "Сначала загрузите реестр многодетных")
            return
        
        search_fio = self.search_fio_input.get().strip()
        search_fio = clean_fio(search_fio)
        if not search_fio:
            mother_fio = self.mother_fio.get().strip()
            father_fio = self.father_fio.get().strip()
            search_fio = mother_fio or father_fio
        
        if not search_fio:
            messagebox.showwarning("Предупреждение", "Введите ФИО матери или отца в форме или в поле поиска")
            return
        
        # Используем процессор для автоопределения
        result, message = self.processor.auto_detect_family_from_register(search_fio)
        
        if result:
            # Заполняем данные из реестра
            self.fill_from_register_data(result)
            messagebox.showinfo("Успех", f"Семья автоопределена: {search_fio}")
            self.tabview.set("👨‍👩‍👧‍👦 Семья")
        else:
            messagebox.showwarning("Не найдено", message)
    
    def fill_from_register_data(self, filled_data):
        """Заполнение формы данными из реестра"""
        # Очищаем форму
        self.clear_form()
        
        # Заполняем мать
        if filled_data['mother_fio']:
            self.mother_fio.insert(0, filled_data['mother_fio'])
        if filled_data['mother_birth']:
            self.mother_birth.insert(0, filled_data['mother_birth'])
        
        # Заполняем отца
        if filled_data['father_fio']:
            self.father_fio.insert(0, filled_data['father_fio'])
        if filled_data['father_birth']:
            self.father_birth.insert(0, filled_data['father_birth'])
        
        # Заполняем детей
        self.clear_all_children()
        for i, child in enumerate(filled_data['children']):
            if i >= 20:  # Ограничение на количество детей
                break
            self.add_child_entry()
            if 'fio' in child:
                self.children_entries[i]['fio'].insert(0, child['fio'])
            if 'birth' in child:
                self.children_entries[i]['birth'].insert(0, child['birth'])
        
        # Заполняем телефон
        if filled_data['phone_number']:
            self.phone_entry.insert(0, filled_data['phone_number'])
            self.log_message(f"📱 Телефон семьи: {filled_data['phone_number']}")
        
        # Заполняем адрес
        if filled_data['address']:
            self.address.insert(0, filled_data['address'])
        
        # Устанавливаем пособие по многодетности по умолчанию 1900
        self.large_family_benefit_var.set("1900")
        self.large_family_benefit_entry.delete(0, 'end')
        self.large_family_benefit_entry.insert(0, "1900")
        
        # Автоматически заполняем АДПИ
        self.fill_adpi_from_loaded_data()
    
    def fill_adpi_from_loaded_data(self):
        """Заполнение данных АДПИ из загруженного файла по ФИО"""
        if not self.adpi_data:
            messagebox.showwarning("Предупреждение", "Сначала загрузите файл АДПИ")
            return
        
        mother_fio = self.mother_fio.get().strip()
        mother_fio = clean_fio(mother_fio)
        father_fio = self.father_fio.get().strip()
        father_fio = clean_fio(father_fio)
        
        # Используем процессор для заполнения АДПИ
        result, message = self.processor.fill_adpi_from_loaded_data(mother_fio, father_fio)
        
        if result:
            if result['address']:
                self.address.delete(0, 'end')
                self.address.insert(0, result['address'])
            
            if 'install_date' in result or 'check_date' in result:
                self.adpi_var.set(result['adpi'])
                if result['install_date']:
                    self.install_date.delete(0, 'end')
                    self.install_date.insert(0, result['install_date'])
                else:
                    self.install_date.delete(0, 'end')
                if result['check_date']:
                    self.check_date.delete(0, 'end')
                    self.check_date.insert(0, result['check_date'])
                else:
                    self.check_date.delete(0, 'end')
            else:
                self.adpi_var.set("нет")
                self.install_date.delete(0, 'end')
                self.check_date.delete(0, 'end')
            
            messagebox.showinfo("Успех", message)
            self.tabview.set("📟 АДПИ")
        else:
            messagebox.showwarning("Не найдено", message)
    
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
            children_count_str = clean_numeric_field(children_count_str)
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
                self.json_creator.autosave_families()
            
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
    
    def load_json_on_startup(self):
        """Загрузка JSON файла при запуске программы"""
        if os.path.exists(self.autosave_filename):
            try:
                with open(self.autosave_filename, 'r', encoding='utf-8') as f:
                    loaded_families = json.load(f)
                if isinstance(loaded_families, list) and loaded_families:
                    loaded_families = [clean_family_data(family) for family in loaded_families]
                    self.families[:] = loaded_families
                    self.json_creator.families[:] = loaded_families
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
                                 "Продолжить без загрузки данных? (Это создаст пустый список семей)"):
                return True
            else:
                messagebox.showwarning("Выход", "Программа будет закрыта. Запустите снова и выберите JSON файл.")
                self.app.quit()
                return False
        try:
            self.last_json_directory = os.path.dirname(file_path)
            self.json_creator.last_json_directory = self.last_json_directory
            self.json_creator.save_config()
            with open(file_path, 'r', encoding='utf-8') as file:
                loaded_families = json.load(file)
            if not isinstance(loaded_families, list):
                messagebox.showerror("Ошибка", "JSON файл должен содержать массив семей")
                return False
            loaded_families = [clean_family_data(family) for family in loaded_families]
            self.families[:] = loaded_families
            self.json_creator.families[:] = loaded_families
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
    
    def load_last_files(self):
        """Загрузка последних файлов реестра и АДПИ при запуске"""
        # Проверяем наличие файлов в папке registry
        if os.path.exists(self.registry_dir):
            registry_files = [f for f in os.listdir(self.registry_dir) if f.lower().endswith(('.xls', '.xlsx', '.ods'))]
            if len(registry_files) >= 2:
                # Если есть как минимум два файла в папке registry, спрашиваем пользователя
                from tkinter import messagebox
                result = messagebox.askyesno("Подгрузка файлов",
                                          f"Найдено {len(registry_files)} файлов в папке registry:\n{', '.join(registry_files[:3])}{'...' if len(registry_files) > 3 else ''}\n\nПодгрузить из папки?")
                if result:
                    # Пытаемся определить, какие из них являются реестром и АДПИ
                    register_file = None
                    adpi_file = None
                    
                    for file in registry_files:
                        file_path = os.path.join(self.registry_dir, file)
                        try:
                            # Пробуем определить тип файла по структуре
                            df = pd.read_excel(file_path, header=None)
                            first_row = df.iloc[0] if len(df) > 0 else pd.Series()
                            
                            # Проверяем наличие характерных заголовков
                            registry_keywords = ['фамилия', 'имя', 'отчество', 'дата рождения', 'детей']
                            adpi_keywords = ['фио', 'адпи', 'установк', 'проверк', 'марка', 'модель']
                            
                            registry_matches = sum(1 for header in first_row if pd.notna(header) and any(kw in str(header).lower() for kw in registry_keywords))
                            adpi_matches = sum(1 for header in first_row if pd.notna(header) and any(kw in str(header).lower() for kw in adpi_keywords))
                            
                            if registry_matches > adpi_matches and register_file is None:
                                register_file = file_path
                            elif adpi_matches > registry_matches and adpi_file is None:
                                adpi_file = file_path
                        except:
                            continue
                    
                    if register_file:
                        self.load_register_file(register_file, auto_load=True)
                        # После загрузки файла реестра синхронизируем данные с процессором
                        self.processor.register_data = self.register_data
                    if adpi_file:
                        self.load_adpi_xlsx(adpi_file, auto_load=True)
                        # После загрузки файла АДПИ синхронизируем данные с процессором
                        self.processor.adpi_data = self.adpi_data
        
        # Ищем последний файл реестра
        register_files = [f for f in os.listdir(self.register_dir) if f.lower().endswith(('.xls', '.xlsx'))]
        if register_files:
            # Берем последний измененный файл
            register_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.register_dir, x)), reverse=True)
            last_register = os.path.join(self.register_dir, register_files[0])
            self.load_register_file(last_register, auto_load=True)
            # Синхронизируем данные с процессором
            self.processor.register_data = self.register_data
        
        # Ищем последний файл АДПИ
        adpi_files = [f for f in os.listdir(self.adpi_dir) if f.lower().endswith(('.xls', '.xlsx', '.ods'))]
        if adpi_files:
            adpi_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.adpi_dir, x)), reverse=True)
            last_adpi = os.path.join(self.adpi_dir, adpi_files[0])
            self.load_adpi_xlsx(last_adpi, auto_load=True)
            # Синхронизируем данные с процессором
            self.processor.adpi_data = self.adpi_data
    
    def preview_current_family(self):
        """Предпросмотр текущей семьи в формате JSON"""
        # Собираем данные из формы
        family_data = self.collect_family_data()
        errors = validate_family_data(family_data)
        if errors:
            messagebox.showerror("Ошибки валидации", "\n".join(errors))
            return
        
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
        # Собираем данные из формы
        family_data = self.collect_family_data()
        errors = validate_family_data(family_data)
        if errors:
            messagebox.showerror("Ошибки валидации", "\n".join(errors))
            return
        
        # Проверяем, есть ли уже такая семья в списке
        for i, existing_family in enumerate(self.families):
            if existing_family.get('mother_fio') == family_data.get('mother_fio'):
                if messagebox.askyesno("Подтверждение", 
                                      f"Семья с матерью {family_data.get('mother_fio')} уже есть в списке.\nЗаменить?"):
                    self.families[i] = family_data
                    messagebox.showinfo("Успех", "Семья обновлена в списке")
                    self.update_families_info()
                    self.json_creator.autosave_families()
                    return
                else:
                    return
        
        self.families.append(family_data)
        messagebox.showinfo("Успех", f"Семья добавлена в список. Всего семей: {len(self.families)}")
        
        self.clear_form_for_new_family()
        self.update_families_info()
        
        self.json_creator.autosave_families()
    
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
                    self.json_creator.autosave_families()
                    
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
            cleaned_families = [clean_family_data(family) for family in self.families]
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
                self.json_creator.last_json_directory = self.last_json_directory
                self.json_creator.save_config()
                
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
        
        # Используем метод из JSONFamilyCreator
        success = self.json_creator.save_to_json(file_path)
        if success:
            self.clear_form_for_new_family()
    
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
        
        # Используем метод из JSONFamilyCreator
        success = self.json_creator.load_from_json(file_path)
        if success:
            self.families[:] = self.json_creator.families
            self.current_file_path = self.json_creator.current_file_path
            self.update_families_info()
            
            if self.families:
                cleaned_family = clean_family_data(self.families[0])
                self.load_family_into_form(cleaned_family)
                self.current_family_index = 0
    
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
                family_data = clean_family_data(self.families[family_num - 1])
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
            mother_fio = clean_fio(family_data['mother_fio'])
            self.mother_fio.insert(0, mother_fio)
        if 'mother_birth' in family_data:
            mother_birth = clean_date(family_data['mother_birth'])
            self.mother_birth.insert(0, mother_birth)
        if 'mother_work' in family_data:
            mother_work = clean_string(family_data['mother_work'])
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
            father_fio = clean_fio(family_data['father_fio'])
            self.father_fio.insert(0, father_fio)
        if 'father_birth' in family_data:
            father_birth = clean_date(family_data['father_birth'])
            self.father_birth.insert(0, father_birth)
        if 'father_work' in family_data:
            father_work = clean_string(family_data['father_work'])
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
                    child_fio = clean_fio(child['fio'])
                    self.children_entries[i]['fio'].insert(0, child_fio)
                if 'birth' in child:
                    child_birth = clean_date(child['birth'])
                    self.children_entries[i]['birth'].insert(0, child_birth)
                if 'education' in child:
                    child_education = clean_string(child['education'])
                    self.children_entries[i]['education'].insert(0, child_education)
                # Загружаем информацию о домашнем ребенке
                if 'home_education' in child and child['home_education'] and 'home_edu_var' in self.children_entries[i]:
                    self.children_entries[i]['home_edu_var'].set(True)
                    self.on_individual_home_education_toggle(self.children_entries[i]['home_edu_var'],
                                                           self.children_entries[i]['education'])
        
        if 'phone_number' in family_data:
            phone = clean_phone(family_data['phone_number'])
            self.phone_entry.insert(0, phone)
        
        if 'address' in family_data:
            address = clean_address(family_data['address'])
            self.address.insert(0, address)
        if 'rooms' in family_data:
            rooms = clean_numeric_field(str(family_data['rooms']))
            self.rooms.insert(0, rooms)
        if 'square' in family_data:
            square = clean_numeric_field(str(family_data['square']))
            self.square.insert(0, square)
        if 'amenities' in family_data:
            self.amenities_var.set(family_data['amenities'])
        if 'ownership' in family_data:
            ownership = clean_string(family_data['ownership'])
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
            install_date = clean_date(family_data['install_date'])
            self.install_date.insert(0, install_date)
        if 'check_date' in family_data:
            check_date = clean_date(family_data['check_date'])
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
                value = clean_numeric_field(str(family_data[key]))
                field.delete(0, 'end')
                field.insert(0, value)
                if key == 'large_family_benefit':
                    benefit_value = str(family_data[key])
                    if benefit_value in ["1900", "2700", "3500"]:
                        self.large_family_benefit_var.set(benefit_value)
        
        # НОВОЕ: Загрузка общих доходов семьи
        if 'general_income' in family_data:
            general_income_value = clean_numeric_field(str(family_data['general_income']))
            if 'general_income' in self.income_fields:
                self.income_fields['general_income'].delete(0, 'end')
                self.income_fields['general_income'].insert(0, general_income_value)
        
        if 'unified_children_count' in family_data:
            children_count = clean_numeric_field(str(family_data['unified_children_count']))
            self.unified_children_count.delete(0, 'end')
            self.unified_children_count.insert(0, children_count)
        if 'unified_percentage' in family_data:
            self.unified_percentage_var.set(family_data['unified_percentage'])
        
        if 'other_incomes' in family_data:
            other_incomes = clean_string(family_data['other_incomes'])
            self.other_incomes_text.delete("1.0", "end")
            self.other_incomes_text.insert("1.0", other_incomes)
    
    def collect_family_data(self):
        """Сбор данных из формы в словарь"""
        # Создаем словарь с данными из формы
        family_data = {
            'mother_fio': clean_fio(self.mother_fio.get().strip()),
            'mother_birth': clean_date(self.mother_birth.get().strip()),
            'mother_work': clean_string(self.mother_work.get().strip()),
            'mother_disability_care': self.mother_disability_care_var.get(),
            'mother_not_working': self.mother_not_working_var.get(),
        }
        
        father_fio = clean_fio(self.father_fio.get().strip())
        if father_fio:
            family_data.update({
                'father_fio': father_fio,
                'father_birth': clean_date(self.father_birth.get().strip()),
                'father_work': clean_string(self.father_work.get().strip()),
                'father_not_working': self.father_not_working_var.get(),
            })
        
        children = []
        for child in self.children_entries:
            child_fio = clean_fio(child['fio'].get().strip())
            if child_fio:
                child_data = {
                    'fio': child_fio,
                    'birth': clean_date(child['birth'].get().strip()),
                    'education': clean_string(child['education'].get().strip())
                }
                # Добавляем информацию о домашнем ребенке, если чекбокс установлен
                if 'home_edu_var' in child and child['home_edu_var'].get():
                    child_data['home_education'] = True
                children.append(child_data)
        if children:
            family_data['children'] = children
        
        phone = clean_phone(self.phone_entry.get().strip())
        if phone:
            family_data['phone_number'] = phone
        
        address = clean_address(self.address.get().strip())
        if address:
            family_data['address'] = address
        
        rooms = clean_numeric_field(self.rooms.get().strip())
        if rooms:
            family_data['rooms'] = rooms
        
        square = clean_numeric_field(self.square.get().strip())
        if square:
            family_data['square'] = square
        
        family_data['amenities'] = self.amenities_var.get()
        
        ownership = clean_string(self.ownership.get().strip())
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
        family_data['ownership'] = clean_string(ownership_text)
        
        family_data['adpi'] = self.adpi_var.get()
        
        install_date = clean_date(self.install_date.get().strip())
        if install_date:
            family_data['install_date'] = install_date
        
        check_date = clean_date(self.check_date.get().strip())
        if check_date:
            family_data['check_date'] = check_date
        
        incomes = {}
        
        # Сохраняем рассчитанное единое пособие, а не проценты
        unified_benefit = clean_numeric_field(self.unified_benefit_entry.get().strip())
        if unified_benefit:
            incomes['unified_benefit'] = unified_benefit
        
        large_family_benefit = clean_numeric_field(self.large_family_benefit_entry.get().strip())
        if large_family_benefit:
            incomes['large_family_benefit'] = large_family_benefit
        
        for key, entry in self.income_fields.items():
            value = clean_numeric_field(entry.get().strip())
            if value:
                incomes[key] = value
        
        if incomes:
            family_data.update(incomes)
        
        # Сохраняем общие доходы семьи
        general_income_value = clean_numeric_field(self.income_fields['general_income'].get().strip())
        if general_income_value:
            family_data['general_income'] = general_income_value
        
        children_count = clean_numeric_field(self.unified_children_count.get().strip())
        if children_count:
            family_data['unified_children_count'] = children_count
        
        percentage = self.unified_percentage_var.get()
        family_data['unified_percentage'] = percentage
        
        other_incomes = self.other_incomes_text.get("1.0", "end-1c").strip()
        other_incomes = clean_string(other_incomes)
        if other_incomes:
            family_data['other_incomes'] = other_incomes
        
        family_data = clean_family_data(family_data)
        return family_data
    
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
            self.json_creator.clear_families()
            self.families[:] = self.json_creator.families
            self.current_family_index = 0
            self.update_families_info()
    
    def run(self):
        """Запуск приложения"""
        self.app.mainloop()