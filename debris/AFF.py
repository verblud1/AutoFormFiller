import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import threading
import sys
import os
from datetime import datetime, date
import time
import re

# Импортируем ваш существующий код
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import platform

class AutoFormFillerGUI:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("🤖 Автоматизатор форм")
        self.app.geometry("1200x800")
        self.app.resizable(True, True)
        
        # Настройка темы
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.family_data = {}
        self.auto_filler = None
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной контейнер с вкладками
        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Создаем вкладки
        self.family_tab = self.tabview.add("👨‍👩‍👧‍👦 Семья")
        self.housing_tab = self.tabview.add("🏠 Жилье")
        self.income_tab = self.tabview.add("💰 Доходы")
        self.adpi_tab = self.tabview.add("📟 АДПИ")
        self.control_tab = self.tabview.add("⚙️ Управление")
        
        self.setup_family_tab()
        self.setup_housing_tab()
        self.setup_income_tab()
        self.setup_adpi_tab()
        self.setup_control_tab()
        
    def setup_family_tab(self):
        """Вкладка информации о семье"""
        # Блок автоопределения
        auto_detect_frame = ctk.CTkFrame(self.family_tab)
        auto_detect_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(auto_detect_frame, text="🔄 АВТООПРЕДЕЛЕНИЕ СЕМЬИ", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        # Поле для ввода данных
        ctk.CTkLabel(auto_detect_frame, 
                    text="Введите данные (Фамилия Имя Отчество ДД.ММ.ГГГГ):").pack(anchor="w")
        
        self.family_input_textbox = ctk.CTkTextbox(auto_detect_frame, height=100)
        self.family_input_textbox.pack(fill="x", padx=5, pady=5)
        
        # Устанавливаем пример данных
        example_data = """Налоев	Арсений	Владимирович	06.09.2009
Налоев	Владимир	Евгеньевич	12.04.1969
Налоева	Елизавета	Владимировна	05.03.2003
Налоева	Вероника	Владимировна	12.03.2013
Налоева	Елена	Михайловна	14.12.1971"""
        
        self.family_input_textbox.insert("1.0", example_data)
        
        # Кнопка автоопределения
        ctk.CTkButton(auto_detect_frame, 
                     text="🔍 Автоопределить семью", 
                     command=self.auto_detect_family,
                     fg_color="#2E8B57",
                     hover_color="#228B22").pack(pady=5)
        
        # Родители
        parents_frame = ctk.CTkFrame(self.family_tab)
        parents_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(parents_frame, text="👨‍👩‍👧‍👦 ИНФОРМАЦИЯ О РОДИТЕЛЯХ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Мать
        mother_frame = ctk.CTkFrame(parents_frame)
        mother_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(mother_frame, text="Мать:").pack(anchor="w")
        self.mother_fio = ctk.CTkEntry(mother_frame, placeholder_text="ФИО матери")
        self.mother_fio.pack(fill="x", padx=5, pady=2)
        
        self.mother_birth = ctk.CTkEntry(mother_frame, placeholder_text="Дата рождения (ДД.ММ.ГГГГ)")
        self.mother_birth.pack(fill="x", padx=5, pady=2)
        
        self.mother_work = ctk.CTkEntry(mother_frame, placeholder_text="Место работы")
        self.mother_work.pack(fill="x", padx=5, pady=2)
        
        # Отец
        father_frame = ctk.CTkFrame(parents_frame)
        father_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(father_frame, text="Отец:").pack(anchor="w")
        self.father_fio = ctk.CTkEntry(father_frame, placeholder_text="ФИО отца")
        self.father_fio.pack(fill="x", padx=5, pady=2)
        
        self.father_birth = ctk.CTkEntry(father_frame, placeholder_text="Дата рождения (ДД.ММ.ГГГГ)")
        self.father_birth.pack(fill="x", padx=5, pady=2)
        
        self.father_work = ctk.CTkEntry(father_frame, placeholder_text="Место работы")
        self.father_work.pack(fill="x", padx=5, pady=2)
        
        # Дети
        children_frame = ctk.CTkFrame(self.family_tab)
        children_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(children_frame, text="👶 ДЕТИ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Прокручиваемая область для детей
        self.children_scrollframe = ctk.CTkScrollableFrame(children_frame, height=200)
        self.children_scrollframe.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.children_entries = []
        
        # Кнопки управления детьми
        children_buttons_frame = ctk.CTkFrame(children_frame)
        children_buttons_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(children_buttons_frame, text="➕ Добавить ребенка", 
                     command=self.add_child_entry).pack(side="left", padx=5)
        ctk.CTkButton(children_buttons_frame, text="➖ Удалить ребенка", 
                     command=self.remove_child_entry).pack(side="left", padx=5)
        
        # Добавляем первого ребенка по умолчанию
        self.add_child_entry()

    def auto_detect_family(self):
        """Автоматическое определение семьи из введенных данных"""
        try:
            # Получаем текст из поля ввода
            input_text = self.family_input_textbox.get("1.0", "end-1c").strip()
            if not input_text:
                messagebox.showwarning("Предупреждение", "Введите данные для автоопределения")
                return
                
            lines = input_text.split('\n')
            people = []
            
            # Парсим введенные данные
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 4:
                    surname = parts[0]
                    name = parts[1]
                    patronymic = parts[2]
                    birth_date = parts[3]
                    
                    # Проверяем корректность даты
                    if not self.validate_date(birth_date):
                        continue
                    
                    people.append({
                        'full_name': f"{surname} {name} {patronymic}",
                        'surname': surname,
                        'name': name,
                        'patronymic': patronymic,
                        'birth_date': birth_date,
                        'birth_year': int(birth_date.split('.')[2])
                    })
            
            if not people:
                messagebox.showwarning("Предупреждение", "Не удалось распознать данные")
                return
            
            # Определяем родителей и детей
            parents = []
            children = []
            
            for person in people:
                if person['birth_year'] <= 2002:
                    parents.append(person)
                else:
                    children.append(person)
            
            # Сортируем родителей по полу (по фамилии)
            father = None
            mother = None
            
            for parent in parents:
                # Определяем пол по окончанию фамилии
                if parent['surname'].endswith('а') or parent['surname'].endswith('я'):
                    mother = parent
                else:
                    father = parent
            
            # Заполняем поля отца
            if father:
                self.father_fio.delete(0, 'end')
                self.father_fio.insert(0, father['full_name'])
                self.father_birth.delete(0, 'end')
                self.father_birth.insert(0, father['birth_date'])
            else:
                self.father_fio.delete(0, 'end')
                self.father_birth.delete(0, 'end')
            
            # Заполняем поля матери
            if mother:
                self.mother_fio.delete(0, 'end')
                self.mother_fio.insert(0, mother['full_name'])
                self.mother_birth.delete(0, 'end')
                self.mother_birth.insert(0, mother['birth_date'])
            else:
                self.mother_fio.delete(0, 'end')
                self.mother_birth.delete(0, 'end')
            
            # Очищаем текущих детей и добавляем новых
            while len(self.children_entries) > 1:
                self.remove_child_entry()
            
            # Если нет детей в данных, оставляем одно пустое поле
            if not children:
                if self.children_entries:
                    self.children_entries[0]['fio'].delete(0, 'end')
                    self.children_entries[0]['birth'].delete(0, 'end')
                    self.children_entries[0]['education'].delete(0, 'end')
            else:
                # Заполняем детей
                for i, child in enumerate(children):
                    if i >= len(self.children_entries):
                        self.add_child_entry()
                    
                    self.children_entries[i]['fio'].delete(0, 'end')
                    self.children_entries[i]['fio'].insert(0, child['full_name'])
                    self.children_entries[i]['birth'].delete(0, 'end')
                    self.children_entries[i]['birth'].insert(0, child['birth_date'])
                    self.children_entries[i]['education'].delete(0, 'end')
            
            messagebox.showinfo("Успех", f"Автоопределение завершено:\n"
                                       f"Родителей: {len(parents)}\n"
                                       f"Детей: {len(children)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка автоопределения: {str(e)}")

    def clear_input_fields(self):
        """Очистка всех полей ввода"""
        # Очищаем поля родителей
        self.mother_fio.delete(0, 'end')
        self.mother_birth.delete(0, 'end')
        self.mother_work.delete(0, 'end')
        self.father_fio.delete(0, 'end')
        self.father_birth.delete(0, 'end')
        self.father_work.delete(0, 'end')
        
        # Очищаем поля детей
        for child in self.children_entries:
            child['fio'].delete(0, 'end')
            child['birth'].delete(0, 'end')
            child['education'].delete(0, 'end')
        
        # Очищаем остальные поля
        self.rooms.delete(0, 'end')
        self.square.delete(0, 'end')
        self.ownership.delete(0, 'end')
        self.amenities_var.set("со всеми удобствами")
        self.adpi_var.set("нет")
        self.install_date.delete(0, 'end')
        self.check_date.delete(0, 'end')
        
        # Очищаем доходы
        self.mother_salary.delete(0, 'end')
        self.father_salary.delete(0, 'end')
        self.unified_benefit.delete(0, 'end')
        self.large_family_benefit.delete(0, 'end')
        self.survivor_pension.delete(0, 'end')
        self.alimony.delete(0, 'end')
        self.disability_pension.delete(0, 'end')
        
        # Очищаем поле автоопределения
        self.family_input_textbox.delete("1.0", "end")
        
        self.log_message("🧹 Поля очищены, готовы для ввода новой семьи")
        
    def add_child_entry(self):
        """Добавление полей для ввода информации о ребенке"""
        child_frame = ctk.CTkFrame(self.children_scrollframe)
        child_frame.pack(fill="x", padx=5, pady=2)
        
        child_number = len(self.children_entries) + 1
        
        ctk.CTkLabel(child_frame, text=f"Ребенок {child_number}:").pack(anchor="w")
        
        child_fio = ctk.CTkEntry(child_frame, placeholder_text="ФИО ребенка")
        child_fio.pack(fill="x", padx=5, pady=2)
        
        child_birth = ctk.CTkEntry(child_frame, placeholder_text="Дата рождения (ДД.ММ.ГГГГ)")
        child_birth.pack(fill="x", padx=5, pady=2)
        
        child_education = ctk.CTkEntry(child_frame, placeholder_text="Место учебы")
        child_education.pack(fill="x", padx=5, pady=2)
        
        self.children_entries.append({
            'frame': child_frame,
            'fio': child_fio,
            'birth': child_birth,
            'education': child_education
        })
        
    def remove_child_entry(self):
        """Удаление последнего ребенка"""
        if len(self.children_entries) > 1:
            child = self.children_entries.pop()
            child['frame'].destroy()
        
    def setup_housing_tab(self):
        """Вкладка информации о жилье"""
        housing_frame = ctk.CTkFrame(self.housing_tab)
        housing_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(housing_frame, text="🏠 ИНФОРМАЦИЯ О ЖИЛЬЕ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Комнаты и площадь
        basic_frame = ctk.CTkFrame(housing_frame)
        basic_frame.pack(fill="x", padx=10, pady=5)
        
        self.rooms = ctk.CTkEntry(basic_frame, placeholder_text="Количество комнат")
        self.rooms.pack(fill="x", padx=5, pady=2)
        
        self.square = ctk.CTkEntry(basic_frame, placeholder_text="Площадь (кв.м.)")
        self.square.pack(fill="x", padx=5, pady=2)
        
        # Удобства
        amenities_frame = ctk.CTkFrame(housing_frame)
        amenities_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(amenities_frame, text="Удобства:").pack(anchor="w")
        
        self.amenities_var = ctk.StringVar(value="со всеми удобствами")
        ctk.CTkRadioButton(amenities_frame, text="Со всеми удобствами", 
                          variable=self.amenities_var, value="со всеми удобствами").pack(anchor="w")
        ctk.CTkRadioButton(amenities_frame, text="С частичными удобствами", 
                          variable=self.amenities_var, value="с частичными удобствами").pack(anchor="w")
        ctk.CTkRadioButton(amenities_frame, text="Без удобств", 
                          variable=self.amenities_var, value="без удобств").pack(anchor="w")
        
        # Собственность
        ownership_frame = ctk.CTkFrame(housing_frame)
        ownership_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(ownership_frame, text="Собственность:").pack(anchor="w")
        self.ownership = ctk.CTkEntry(ownership_frame, 
                                     placeholder_text="ФИО собственника, 'муниципальная', 'долевая' и т.д.")
        self.ownership.pack(fill="x", padx=5, pady=2)
        
    def setup_income_tab(self):
        """Вкладка информации о доходах"""
        income_frame = ctk.CTkFrame(self.income_tab)
        income_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(income_frame, text="💰 ДОХОДЫ СЕМЬИ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Прокручиваемая область для доходов
        income_scrollframe = ctk.CTkScrollableFrame(income_frame, height=300)
        income_scrollframe.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Поля для доходов
        self.mother_salary = self.create_income_field(income_scrollframe, "Зарплата матери")
        self.father_salary = self.create_income_field(income_scrollframe, "Зарплата отца")
        self.unified_benefit = self.create_income_field(income_scrollframe, "Единое пособие")
        self.large_family_benefit = self.create_income_field(income_scrollframe, "Пособие по многодетности")
        self.survivor_pension = self.create_income_field(income_scrollframe, "Пенсия по потере кормильца")
        self.alimony = self.create_income_field(income_scrollframe, "Алименты")
        self.disability_pension = self.create_income_field(income_scrollframe, "Пенсия по инвалидности")
        
    def create_income_field(self, parent, label):
        """Создание поля для ввода дохода"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(frame, text=label).pack(anchor="w")
        entry = ctk.CTkEntry(frame, placeholder_text="Сумма (Enter - пропустить)")
        entry.pack(fill="x", padx=5, pady=2)
        
        return entry
        
    def setup_adpi_tab(self):
        """Вкладка информации об АДПИ"""
        adpi_frame = ctk.CTkFrame(self.adpi_tab)
        adpi_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(adpi_frame, text="📟 ИНФОРМАЦИЯ ОБ АДПИ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Наличие АДПИ
        has_adpi_frame = ctk.CTkFrame(adpi_frame)
        has_adpi_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(has_adpi_frame, text="АДПИ установлен?").pack(anchor="w")
        
        self.adpi_var = ctk.StringVar(value="нет")
        ctk.CTkRadioButton(has_adpi_frame, text="Да", 
                          variable=self.adpi_var, value="да").pack(anchor="w")
        ctk.CTkRadioButton(has_adpi_frame, text="Нет", 
                          variable=self.adpi_var, value="нет").pack(anchor="w")
        
        # Даты АДПИ
        dates_frame = ctk.CTkFrame(adpi_frame)
        dates_frame.pack(fill="x", padx=10, pady=5)
        
        self.install_date = ctk.CTkEntry(dates_frame, placeholder_text="Дата установки АДПИ (ДД.ММ.ГГГГ)")
        self.install_date.pack(fill="x", padx=5, pady=2)
        
        self.check_date = ctk.CTkEntry(dates_frame, placeholder_text="Дата проверки АДПИ (ДД.ММ.ГГГГ)")
        self.check_date.pack(fill="x", padx=5, pady=2)
        
    def setup_control_tab(self):
        """Вкладка управления"""
        control_frame = ctk.CTkFrame(self.control_tab)
        control_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Область для логов
        ctk.CTkLabel(control_frame, text="📊 ЛОГ ВЫПОЛНЕНИЯ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.log_text = scrolledtext.ScrolledText(control_frame, height=20, width=80)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text.config(state="disabled")
        
        # Кнопки управления
        buttons_frame = ctk.CTkFrame(control_frame)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(buttons_frame, text="🧾 Просмотр данных", 
                     command=self.preview_data, width=200).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="🚀 Запуск автоматизации", 
                     command=self.start_automation, width=200, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="🛑 Остановить", 
                     command=self.stop_automation, width=200, fg_color="red").pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="🧹 Очистить поля", 
                     command=self.clear_input_fields, width=200, fg_color="orange").pack(side="left", padx=5)
        
        # Прогресс бар
        self.progress = ctk.CTkProgressBar(control_frame)
        self.progress.pack(fill="x", padx=10, pady=5)
        self.progress.set(0)
        
    def log_message(self, message):
        """Добавление сообщения в лог"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.app.update()
        
    def validate_data(self):
        """Проверка введенных данных"""
        # Проверка матери
        if not self.mother_fio.get().strip():
            messagebox.showerror("Ошибка", "Введите ФИО матери")
            return False
            
        if not self.validate_date(self.mother_birth.get().strip()):
            messagebox.showerror("Ошибка", "Неверный формат даты рождения матери")
            return False
            
        # Проверка детей
        for i, child in enumerate(self.children_entries):
            if not child['fio'].get().strip():
                messagebox.showerror("Ошибка", f"Введите ФИО ребенка {i+1}")
                return False
                
            if not self.validate_date(child['birth'].get().strip()):
                messagebox.showerror("Ошибка", f"Неверный формат даты рождения ребенка {i+1}")
                return False
                
        # Проверка жилья
        if not self.rooms.get().strip() or not self.validate_positive_number(self.rooms.get()):
            messagebox.showerror("Ошибка", "Введите корректное количество комнат")
            return False
            
        if not self.square.get().strip() or not self.validate_positive_number(self.square.get()):
            messagebox.showerror("Ошибка", "Введите корректную площадь")
            return False
            
        return True
        
    def collect_family_data(self):
        """Сбор данных из формы"""
        family_data = {}
        
        # Родители
        family_data['mother'] = {
            'fio': self.mother_fio.get().strip(),
            'birth_date': self.mother_birth.get().strip(),
            'full_name': self.mother_fio.get().strip()
        }
        
        if self.father_fio.get().strip():
            family_data['father'] = {
                'fio': self.father_fio.get().strip(),
                'birth_date': self.father_birth.get().strip(),
                'full_name': self.father_fio.get().strip()
            }
        else:
            family_data['father'] = None
            
        # Дети
        family_data['children'] = []
        for child in self.children_entries:
            if child['fio'].get().strip():
                family_data['children'].append({
                    'fio': child['fio'].get().strip(),
                    'birth_date': child['birth'].get().strip(),
                    'full_name': child['fio'].get().strip(),
                    'education': child['education'].get().strip()
                })
                
        # Работа
        family_data['work_places'] = {
            'mother': self.mother_work.get().strip(),
            'father': self.father_work.get().strip()
        }
        
        # Доходы
        family_data['incomes'] = {}
        income_fields = {
            'mother_salary': self.mother_salary,
            'father_salary': self.father_salary,
            'unified_benefit': self.unified_benefit,
            'large_family_benefit': self.large_family_benefit,
            'survivor_pension': self.survivor_pension,
            'alimony': self.alimony,
            'disability_pension': self.disability_pension
        }
        
        for key, field in income_fields.items():
            value = field.get().strip()
            if value and self.validate_number(value):
                family_data['incomes'][key] = value
                
        # Жилье
        ownership_text = ""
        if self.ownership.get().strip():
            ownership_text = f", в собственности у {self.ownership.get().strip()}"
            
        family_data['housing'] = f"{self.rooms.get().strip()} комнат, {self.square.get().strip()} кв.м., {self.amenities_var.get()}{ownership_text}"
        
        # АДПИ
        family_data['adpi'] = {
            'has_adpi': 'д' if self.adpi_var.get() == 'да' else 'н',
            'install_date': self.install_date.get().strip() if self.install_date.get().strip() else None,
            'check_date': self.check_date.get().strip() if self.check_date.get().strip() else None
        }
        
        return family_data
        
    def preview_data(self):
        """Предпросмотр собранных данных"""
        if not self.validate_data():
            return
            
        family_data = self.collect_family_data()
        
        # Форматируем данные для показа
        preview_text = "📋 ПРЕДПРОСМОТР ДАННЫХ:\n\n"
        
        # Семья
        preview_text += "👨‍👩‍👧‍👦 СЕМЬЯ:\n"
        preview_text += f"Мать: {family_data['mother']['fio']} {family_data['mother']['birth_date']}\n"
        if family_data['work_places']['mother']:
            preview_text += f"Работает: {family_data['work_places']['mother']}\n"
            
        if family_data['father']:
            preview_text += f"Отец: {family_data['father']['fio']} {family_data['father']['birth_date']}\n"
            if family_data['work_places']['father']:
                preview_text += f"Работает: {family_data['work_places']['father']}\n"
                
        preview_text += "Дети:\n"
        for child in family_data['children']:
            edu_text = f" - {child['education']}" if child.get('education') else ""
            preview_text += f"    {child['fio']} {child['birth_date']}{edu_text}\n"
            
        # Доходы
        if family_data['incomes']:
            preview_text += "\n💰 ДОХОДЫ:\n"
            income_labels = {
                'mother_salary': 'Зарплата матери',
                'father_salary': 'Зарплата отца',
                'unified_benefit': 'Единое пособие',
                'large_family_benefit': 'Пособие по многодетности',
                'survivor_pension': 'Пенсия по потере кормильца',
                'alimony': 'Алименты',
                'disability_pension': 'Пенсия по инвалидности'
            }
            for key, value in family_data['incomes'].items():
                preview_text += f"   {income_labels[key]}: {value}\n"
                
        # Жилье
        preview_text += f"\n🏠 ЖИЛЬЕ: {family_data['housing']}\n"
        
        # АДПИ
        adpi_status = "Установлен" if family_data['adpi']['has_adpi'] == 'д' else "Не установен"
        preview_text += f"\n📟 АДПИ: {adpi_status}\n"
        if family_data['adpi']['install_date']:
            preview_text += f"   Дата установки: {family_data['adpi']['install_date']}\n"
        if family_data['adpi']['check_date']:
            preview_text += f"   Дата проверки: {family_data['adpi']['check_date']}\n"
            
        # Показываем в отдельном окне
        preview_window = ctk.CTkToplevel(self.app)
        preview_window.title("Предпросмотр данных")
        preview_window.geometry("600x500")
        
        preview_textbox = scrolledtext.ScrolledText(preview_window, width=70, height=25)
        preview_textbox.pack(fill="both", expand=True, padx=20, pady=20)
        preview_textbox.insert("1.0", preview_text)
        preview_textbox.config(state="disabled")
        
    def start_automation(self):
        """Запуск автоматизации в отдельном потоке"""
        if not self.validate_data():
            return
            
        self.family_data = self.collect_family_data()
        
        # Блокируем кнопки во время выполнения
        self.log_message("🚀 Запуск автоматизации...")
        self.progress.set(0.1)
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.run_automation_thread)
        thread.daemon = True
        thread.start()
        
    def run_automation_thread(self):
        """Поток выполнения автоматизации"""
        try:
            self.auto_filler = AutoFormFillerGUIWrapper(self)
            self.auto_filler.run_automation(self.family_data)
        except Exception as e:
            self.log_message(f"❌ Ошибка: {e}")
            self.progress.set(0)
        finally:
            # Очищаем поля после завершения автоматизации
            self.clear_input_fields()
            
    def stop_automation(self):
        """Остановка автоматизации"""
        if self.auto_filler and self.auto_filler.driver:
            self.auto_filler.driver.quit()
            self.log_message("🛑 Автоматизация остановлена")
            self.progress.set(0)
            
    def validate_date(self, date_string):
        """Проверка даты"""
        try:
            datetime.strptime(date_string, '%d.%m.%Y')
            return True
        except ValueError:
            return False
            
    def validate_number(self, value):
        """Проверка числа"""
        try:
            float(value)
            return True
        except ValueError:
            return False
            
    def validate_positive_number(self, value):
        """Проверка положительного числа"""
        try:
            num = float(value)
            return num > 0
        except ValueError:
            return False
            
    def run(self):
        """Запуск приложения"""
        self.app.mainloop()


class AutoFormFillerGUIWrapper:
    """Обертка для AutoFormFiller с поддержкой GUI"""
    
    def __init__(self, gui_app):
        self.gui = gui_app
        self.driver = None
        self.wait = None
        
    def log(self, message):
        """Логирование в GUI"""
        self.gui.log_message(message)
        
    def update_progress(self, value):
        """Обновление прогресса"""
        self.gui.progress.set(value)
        self.gui.app.update()
        
    def run_automation(self, family_data):
        """Запуск автоматизации с данными из GUI"""
        try:
            self.log("🔍 Настройка драйвера...")
            self._setup_driver()
            self.update_progress(0.2)
            
            if not self._initialize_connection():
                self.log("❌ Не удалось подключиться к базе данных")
                return
                
            self.update_progress(0.3)
            
            self._login()
            self.update_progress(0.4)

            # 1. Ввод ФИО матери в быстрый поиск
            mother_fio = family_data['mother']['fio']
            self.log(f"🔍 Выполняем поиск по ФИО матери: {mother_fio}")
            if not self._fast_search_mother(mother_fio):
                self.log("❌ Не удалось выполнить поиск матери")
                return

            # 2. Ждем подтверждения от пользователя
            self.log("⏳ Ожидаем подтверждения перехода на верную страницу...")
            if not self._wait_for_user_confirmation():
                self.log("❌ Пользователь не подтвердил переход на верную страницу")
                return

            self.update_progress(0.5)
            
            if not self._check_additional_info_empty():
                if not self._warn_existing_data():
                    self.log("❌ Автоматизация отменена пользователем")
                    return
                    
            self.update_progress(0.6)
            
            # Навигация и получение данных со страницы
            phone, address = self._navigate_to_form()
            self.update_progress(0.7)
            
            # Проверка и редактирование адреса
            address = self._verify_and_edit_address(address)
            self.update_progress(0.8)
            
            # Заполнение формы
            formatted_data = self._format_family_data(family_data)
            self._fill_form(phone, address, *formatted_data)
            self.update_progress(0.9)
            
            # Финальная проверка и сохранение
            if self._final_verification():
                if self._save_and_exit():
                    self._take_screenshot(formatted_data)
                    self.log("\n✅ Автоматизация завершена успешно!")
                    self.update_progress(1.0)
                else:
                    self.log("\n⚠️ Автоматизация завершена с ошибками")
                    
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
            self.update_progress(0)
        finally:
            # 3. Закрываем браузер после завершения автоматизации
            if self.driver:
                self.driver.quit()
                self.log("🔒 Браузер закрыт")

    def _fast_search_mother(self, mother_fio):
        """Ввод ФИО матери в поле быстрого поиска"""
        try:
            # Ждем появления поля поиска
            search_field = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "ctl00$cph$ctrlFastFind$tbFind"))
            )
            
            # Очищаем поле и вводим ФИО матери
            search_field.clear()
            search_field.send_keys(mother_fio)
            self.log(f"✅ Введено ФИО в поиск: {mother_fio}")
            
            # Нажимаем Enter для поиска
            search_field.send_keys(Keys.ENTER)
            self.log("🔍 Выполняем поиск...")
            
            # Ждем завершения поиска
            time.sleep(3)
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка при поиске: {e}")
            return False

    def _wait_for_user_confirmation(self):
        """Ожидание подтверждения от пользователя"""
        try:
            # Показываем сообщение и ждем подтверждения
            self.log("📋 ПОЖАЛУЙСТА, ПРОВЕРЬТЕ:")
            self.log("1. Убедитесь, что поиск выполнен корректно")
            self.log("2. Перейдите на страницу нужной матери/отца")
            self.log("3. Нажмите OK для продолжения автоматизации")
            
            # Используем GUI для подтверждения
            result = messagebox.askyesno(
                "Подтверждение перехода", 
                "Поиск выполнен.\n\n"
                "1. Проверьте результаты поиска\n"
                "2. Перейдите на страницу матери/отца семейства\n"
                "3. Убедитесь, что это правильная страница\n\n"
                "Продолжить автоматизацию?"
            )
            
            if result:
                self.log("✅ Пользователь подтвердил переход на верную страницу")
                return True
            else:
                self.log("❌ Пользователь отменил автоматизацию")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка при подтверждении: {e}")
            return False

    def _detect_browser(self):
        """Определение доступного браузера"""
        system = platform.system().lower()
        
        if system == "windows":
            import winreg
            browsers = [
                (r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe', 'Chrome', ChromeType.GOOGLE),
                (r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\browser.exe', 'Yandex', ChromeType.YANDEX),
            ]
            
            for path, name, btype in browsers:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                        if os.path.exists(winreg.QueryValue(key, None)):
                            return {'name': name, 'type': btype}
                except: pass
                
        elif system in ["linux", "redos"]:
            for path in ['/usr/bin/chromium-browser', '/usr/bin/chromium']:
                if os.path.exists(path):
                    return {'name': 'Chromium', 'type': ChromeType.CHROMIUM}
        
        return None
                
    def _setup_driver(self):
        """Настройка драйвера с автоопределением браузера"""
        self.log("🔍 Определение браузера...")
        browser = self._detect_browser()
        
        if not browser:
            self.log("❌ Не найден Chrome, Yandex или Chromium")
            raise Exception("Браузер не найден")
            
        self.log(f"🚀 Используется: {browser['name']}")
        
        try:
            driver_path = ChromeDriverManager(chrome_type=browser['type']).install()
            service = webdriver.chrome.service.Service(driver_path)
            
            options = webdriver.ChromeOptions()
            if platform.system().lower() in ["linux", "redos"]:
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
            
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--start-maximized')
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            self.driver.maximize_window()
            self.log("✅ Драйвер настроен")
            
        except Exception as e:
            self.log(f"❌ Ошибка настройки драйвера: {e}")
            raise
            
    def _initialize_connection(self):
        """Инициализация подключения к базе данных"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.log(f"🔗 Попытка подключения к базе данных ({attempt + 1}/{max_attempts})...")
                self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
                self.log("✅ Подключение успешно!")
                return True
                
            except Exception as e:
                if "ERR_CONNECTION_REFUSED" in str(e):
                    self.log("❌ Не удалось подключиться к базе данных")
                    self.log("🔌 Убедитесь, что база данных запущена и доступна по адресу http://localhost:8080")
                    
                    if attempt < max_attempts - 1:
                        result = messagebox.askyesno("Ошибка подключения", 
                                                   "Не удалось подключиться к базе данных.\n"
                                                   "Убедитесь, что база данных запущена.\n\n"
                                                   "Повторить попытку?")
                        if result:
                            if self.driver:
                                self.driver.quit()
                            self._setup_driver()
                        else:
                            return False
                    else:
                        self.log("❌ Не удалось подключиться после нескольких попыток")
                        return False
                else:
                    self.log(f"❌ Неизвестная ошибка: {e}")
                    return False
        return False
        
    def _login(self):
        """Вход в систему"""
        self.log("🔐 Выполняем вход в систему...")
        self._fill_field(By.NAME, "tbUserName", "СРЦ_Вол")
        self._fill_field(By.NAME, "tbPassword", "СРЦ_Вол1", press_enter=True)
        self.log("✅ Вход выполнен")
        
    def _check_additional_info_empty(self):
        """Проверка пустого поля дополнительной информации"""
        try:
            # Переходим на вкладку доп. информации
            self._click_element(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL")
            time.sleep(2)
            
            # Проверяем текст в поле
            info_text = self._get_element_text("ctl00_cph_lblAddInfo2", "").strip()
            
            if info_text == "Информация отсутствует" or not info_text:
                return True
            else:
                self.log(f"❌ Найдены существующие данные: {info_text}")
                return False
                
        except Exception as e:
            self.log(f"⚠️ Ошибка проверки поля: {e}")
            return True
        
    def _warn_existing_data(self):
        """Предупреждение о существующих данных"""
        return messagebox.askyesno("Предупреждение", 
                                 "В разделе уже есть данные! Они будут УДАЛЕНЫ.\nПродолжить?")
        
    def _check_correct_page(self):
        """Проверка правильной страницы"""
        try:
            if self._is_element_present(By.ID, "ctl00_cph_lblMobilPhone"):
                return True
            else:
                return False
        except Exception as e:
            self.log(f"❌ Ошибка проверки страницы: {e}")
            return False

    def _is_element_present(self, by, selector):
        """Проверка наличия элемента на странице"""
        try:
            self.driver.find_element(by, selector)
            return True
        except:
            return False
        
    def _navigate_to_form(self):
        """Навигация к форме"""
        self.log("🔍 Извлекаем данные со страницы...")
        phone = self._get_element_text("ctl00_cph_lblMobilPhone")
        address = self._get_element_text("ctl00_cph_lblRegAddress", "Адрес не найден")
        
        self.log("📍 Переходим к форме дополнительной информации...")
        self._click_element(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL")
        self._click_element(By.ID, "ctl00_cph_lbtnEditAddInfo")
        self._click_element(By.ID, "ctl00_cph_ctrlDopFields_lbtnAdd")
        
        return phone, address
        
    def _verify_and_edit_address(self, extracted_address):
        """Проверка и редактирование адреса"""
        self.log(f"🏠 Извлеченный адрес: {extracted_address}")
        # Используем GUI для редактирования адреса
        result = ctk.CTkInputDialog(text="Адрес верен? Если нет - введите правильный:", 
                                title="Проверка адреса").get_input()
        return result or extracted_address
        
    def _format_family_data(self, family_data):
        """Форматирование данных семьи"""
        # Адаптация оригинального метода _format_family_data
        lines = []
        
        if family_data.get('mother'):
            mother_work = family_data['work_places'].get('mother', '')
            mother_line = f"Мать: {family_data['mother']['fio']} {family_data['mother']['birth_date']}"
            lines.extend([mother_line, f"Работает: {mother_work}"])
        else:
            lines.extend(["Мать: ", "Работает: "])
        
        if family_data.get('father'):
            father_work = family_data['work_places'].get('father', '')
            lines.extend([f"Отец: {family_data['father']['fio']} {family_data['father']['birth_date']}", f"Работает: {father_work}"])
        
        lines.append("Дети:")
        for child in family_data['children']:
            edu = f" - {child['education']}" if child.get('education') else ""
            lines.append(f"    {child['fio']} {child['birth_date']}{edu}")
        
        if family_data['incomes']:
            lines.append("Доход:")
            income_labels = {
                'mother_salary': 'з/п матери',
                'father_salary': 'з/п отца', 
                'unified_benefit': 'единое пособие',
                'large_family_benefit': 'пособие по многодетности',
                'survivor_pension': 'пенсия по потере кормильца',
                'alimony': 'алименты',
                'disability_pension': 'пенсия по инвалидности'
            }
            
            for key, value in family_data['incomes'].items():
                lines.append(f"{income_labels[key]} - {value}")
        
        category = "полная, многодетная" if family_data.get('father') else "неполная, многодетная"
        
        add_info_text = "\n".join(lines)
        housing_info = family_data['housing']
        adpi_data = family_data['adpi']
        incomes = family_data['incomes']
        work_places = family_data['work_places']
        
        return add_info_text, category, housing_info, adpi_data, incomes, work_places
        
    def _fill_form(self, phone, address, add_info_text, category, housing_info, adpi_data, incomes, work_places):
        """Заполнение формы"""
        # Реализация аналогична оригинальному методу с массовым заполнением
        self.log("📝 Заполнение формы...")
        time.sleep(2)

        # Массовое нажатие чекбоксов
        checkbox_ids = [8, 12, 13, 14, 17, 18]
        if adpi_data['has_adpi'] == 'д':
            checkbox_ids.extend([15, 16])
        
        self._bulk_click_checkboxes(checkbox_ids)
        self._click_element_with_retry(By.ID, "ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_ctl06_AJOk")
        time.sleep(2)

        # Заполнение текстовой области
        self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True)
        
        # Массовое заполнение полей
        field_data = [
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl02$tb', 'value': phone or ''},
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl04$tb', 'value': category},
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl05$tb', 'value': address},
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl08$tb', 'value': housing_info},
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl09$tb', 
             'value': "Санитарные условия удовлетворительные, для детей имеется отдельное спальное место, место для занятий и отдыха. Продукты питания в достаточном количестве."}
        ]
        
        self._bulk_fill_fields(field_data)
        
        # Заполнение АДПИ
        self._fill_adpi_radio_button(adpi_data)
        
        if adpi_data['has_adpi'] == 'д':
            self._fill_adpi_dates(adpi_data)
            
    def _bulk_click_checkboxes(self, checkbox_ids):
        """Массовое нажатие чекбоксов"""
        script = """
        var ids = arguments[0];
        for (var i = 0; i < ids.length; i++) {
            var checkbox = document.getElementById('ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_' + ids[i]);
            if (checkbox && !checkbox.checked) {
                checkbox.click();
            }
        }
        return ids.length;
        """
        
        try:
            clicked = self.driver.execute_script(script, checkbox_ids)
            self.log(f"✅ Отмечено {clicked} чекбоксов")
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка массового отметки: {e}")
            return False
            
    def _bulk_fill_fields(self, field_data):
        """Массовое заполнение полей"""
        script = """
        var fields = arguments[0];
        var results = [];
        
        for (var i = 0; i < fields.length; i++) {
            var fieldInfo = fields[i];
            var element;
            
            if (fieldInfo.by === 'name') {
                element = document.querySelector('[name="' + fieldInfo.selector + '"]');
            } else if (fieldInfo.by === 'id') {
                element = document.getElementById(fieldInfo.selector);
            }
            
            if (element) {
                try {
                    var oldValue = element.value;
                    element.value = fieldInfo.value;
                    
                    // Триггерим события
                    var events = ['change', 'input', 'blur'];
                    for (var j = 0; j < events.length; j++) {
                        element.dispatchEvent(new Event(events[j], { bubbles: true }));
                    }
                    
                    results.push({
                        selector: fieldInfo.selector,
                        success: true,
                        oldValue: oldValue,
                        newValue: fieldInfo.value
                    });
                    
                } catch (e) {
                    results.push({
                        selector: fieldInfo.selector,
                        success: false,
                        error: e.toString()
                    });
                }
            } else {
                results.push({
                    selector: fieldInfo.selector,
                    success: false,
                    error: 'Element not found'
                });
            }
        }
        return results;
        """
        
        try:
            results = self.driver.execute_script(script, field_data)
            
            success_count = 0
            for result in results:
                if result['success']:
                    success_count += 1
                else:
                    self.log(f"⚠️ Не удалось заполнить {result['selector']}: {result['error']}")
            
            self.log(f"✅ Заполнено {success_count}/{len(field_data)} полей")
            return success_count == len(field_data)
            
        except Exception as e:
            self.log(f"❌ Ошибка массового заполнения: {e}")
            return False
            
    def _fill_adpi_radio_button(self, adpi_data):
        """Заполнение радио-кнопки АДПИ"""
        if adpi_data['has_adpi'] == 'д':
            self._click_element_with_retry(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0")
        else:
            self._click_element_with_retry(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_1")
    
    def _fill_adpi_dates(self, adpi_data):
        """Заполнение дат АДПИ"""
        if adpi_data.get('install_date'):
            self._fill_date_field("igtxtctl00_cph_ctrlDopFields_gv_ctl06_wdte", adpi_data['install_date'])
            time.sleep(1)
        
        if adpi_data.get('check_date'):
            self._fill_date_field("igtxtctl00_cph_ctrlDopFields_gv_ctl07_wdte", adpi_data['check_date'])
            
    def _final_verification(self):
        """Финальная проверка"""
        return messagebox.askyesno("Финальная проверка", 
                                 "Проверьте все введенные данные на странице.\nЕсли нужно что-то исправить - сделайте это сейчас.\n\nПродолжить сохранение?")
        
    def _save_and_exit(self):
        """Сохранение данных"""
        self.log("💾 Сохраняем данные...")
        
        if self._click_element_with_retry(By.ID, "ctl00_cph_lbtnExitSave"):
            time.sleep(2)
            self.log("✅ Данные сохранены!")
            return True
        return False
        
    def _take_screenshot(self, formatted_data):
        """Создание скриншота"""
        try:
            add_info_text, _, _, _, _, _ = formatted_data
            lines = add_info_text.split('\n')
            
            for line in lines:
                if line.startswith('Мать: '):
                    mother_info = line[6:]
                    if len(mother_info) > 10:
                        mother_name = mother_info[:-10].strip()
                        safe_name = re.sub(r'[\\/*?:"<>|]', '_', mother_name)
                        break
            else:
                safe_name = "неизвестно"
            
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            screenshots_dir = os.path.join(desktop, "database_screens")
            
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
            
            file_path = os.path.join(screenshots_dir, f"{safe_name}.png")
            self.driver.save_screenshot(file_path)
            self.log(f"📸 Скриншот сохранен: {file_path}")
            
        except Exception as e:
            self.log(f"⚠️ Ошибка скриншота: {e}")
            
    # Базовые методы Selenium (аналогичные оригинальным)
    def _click_element_with_retry(self, by, selector, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, selector)))
                element.click()
                self.log(f"✓ Элемент {selector} кликнут")
                return True
            except Exception as e:
                self.log(f"⚠️ Ошибка клика {selector} (попытка {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
        return False
        
    def _fill_textarea(self, field_name, text, resize=False):
        try:
            field = self.wait.until(EC.element_to_be_clickable((By.NAME, field_name)))
            field.clear()
            field.send_keys(text)
            if resize:
                self.driver.execute_script("arguments[0].style.height = '352px'; arguments[0].style.width = '1151px';", field)
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка текстовой области {field_name}: {e}")
            return False
            
    def _fill_date_field(self, field_id, date_text):
        try:
            field = self.wait.until(EC.element_to_be_clickable((By.ID, field_id)))
            field.click()
            field.send_keys(Keys.CONTROL + "a")
            field.send_keys(Keys.DELETE)
            
            actions = ActionChains(self.driver)
            for char in date_text:
                actions.send_keys(char)
                actions.pause(0.1)
            actions.perform()
            
            field.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка даты {field_id}: {e}")
            return False
            
    def _click_element(self, by, selector):
        try:
            element = self.wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка клика {selector}: {e}")
            return False
            
    def _get_element_text(self, element_id, default=""):
        try:
            return self.driver.find_element(By.ID, element_id).text
        except:
            return default

    def _fill_field(self, by, selector, text, press_enter=False):
        """Заполнение поля"""
        try:
            field = self.wait.until(EC.element_to_be_clickable((by, selector)))
            field.clear()
            field.send_keys(text + (Keys.ENTER if press_enter else ""))
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка поля {selector}: {e}")
            return False


if __name__ == "__main__":
    app = AutoFormFillerGUI()
    app.run()