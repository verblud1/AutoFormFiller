"""Основной модуль для массового обработчика семей"""

import asyncio
import customtkinter as ctk
from tkinter import messagebox, scrolledtext, filedialog
import threading
import json
from datetime import datetime, timedelta
import os
import re
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import platform
import sys
from utils.file_utils import setup_config_directory, load_config, save_config
from utils.data_processing import clean_string, clean_fio, clean_date, clean_phone
from utils.validation import validate_family_data
from common.gui_components import BaseGUI


class MassFamilyProcessorGUI(BaseGUI):
    def __init__(self):
        super().__init__()
        self.app.title("📦 Массовый обработчик семей")
        self.app.geometry("1200x900")
        self.app.resizable(True, True)
        
        self.families_list = []
        self.current_family_index = 0
        self.is_processing = False
        self.auto_filler = None
        self.processing_thread = None
        self.driver = None
        self.manual_intervention_required = False
        
        # Асинхронные примитивы для синхронизации
        self._pause_event = None
        self._stop_event = None
        self._async_loop = None
        self._processing_task = None
        
        # Организация конфигурационных файлов в отдельную папку
        self.setup_config_directory()
        
        # Файлы конфигурации
        self.config_file = os.path.join(self.config_dir, "mass_processor_config.json")
        self.stats_file = os.path.join(self.config_dir, "processing_statistics.json")
        
        self.config = self.load_config()
        self.stats = self.load_statistics()
        
        # Последний загруженный JSON файл
        self.last_json_path = self.config.get("last_json_path", "")
        
        # Переменные для статистики
        self.success_count = 0
        self.daily_stat = 0
        self.weekly_stat = 0
        
        self.setup_ui()
        self.setup_error_handling()
        
    def setup_config_directory(self):
        """Создание папки для конфигурационных файлов"""
        try:
            # Определяем путь к директории приложения
            app_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir, self.screenshots_dir, self.logs_dir = setup_config_directory(app_dir)
                
        except Exception as e:
            print(f"❌ Ошибка создания папки конфигурации: {e}")
            # Если не удалось создать папку config, используем текущую директорию
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
            self.logs_dir = self.config_dir
            self.screenshots_dir = self.config_dir
    
    def load_statistics(self):
        """Загрузка статистики обработки"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    
                    # Проверяем структуру файла
                    if not isinstance(stats, dict):
                        stats = {}
                    
                    # Проверяем наличие необходимых полей
                    if 'daily' not in stats:
                        stats['daily'] = {}
                    if 'weekly' not in stats:
                        stats['weekly'] = {}
                    
                    return stats
            return {'daily': {}, 'weekly': {}}
        except Exception as e:
            self.log_message(f"⚠️ Ошибка загрузки статистики: {e}")
            return {'daily': {}, 'weekly': {}}
    
    def save_statistics(self):
        """Сохранение статистики обработки"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.log_message(f"⚠️ Ошибка сохранения статистики: {e}")
            return False
    
    def update_statistics(self, success_count):
        """Обновление статистики обработки"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Обновляем дневную статистику
            if today in self.stats['daily']:
                self.stats['daily'][today] += success_count
            else:
                self.stats['daily'][today] = success_count
            
            # Обновляем недельную статистику
            # Получаем номер недели
            week_num = datetime.now().strftime("%Y-W%W")
            if week_num in self.stats['weekly']:
                self.stats['weekly'][week_num] += success_count
            else:
                self.stats['weekly'][week_num] = success_count
            
            # Сохраняем статистику
            self.save_statistics()
            
            # Обновляем отображение статистики
            self.update_statistics_display()
            
            self.log_message(f"📊 Статистика обновлена: +{success_count} семей")
            return True
        except Exception as e:
            self.log_message(f"⚠️ Ошибка обновления статистики: {e}")
            return False
    
    def get_statistics_for_period(self):
        """Получение статистики за день и неделю"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            today_stat = self.stats['daily'].get(today, 0)
            
            # Получаем статистику за текущую неделю (понедельник-пятница)
            week_stat = 0
            current_date = datetime.now()
            
            # Находим понедельник текущей недели
            start_of_week = current_date - timedelta(days=current_date.weekday())
            
            # Для каждого дня недели с понедельника по пятницу (0-4)
            for i in range(5):
                day_date = start_of_week + timedelta(days=i)
                day_str = day_date.strftime("%Y-%m-%d")
                week_stat += self.stats['daily'].get(day_str, 0)
            
            return today_stat, week_stat
        except Exception as e:
            self.log_message(f"⚠️ Ошибка получения статистики: {e}")
            return 0, 0
    
    def update_statistics_display(self):
        """Обновление отображения статистики в интерфейсе"""
        try:
            today_stat, week_stat = self.get_statistics_for_period()
            # Проверяем, существует ли виджет перед обновлением
            try:
                if self.stat_label.winfo_exists():
                    self.stat_label.configure(
                        text=f"📊 Статистика: Сегодня - {today_stat} | Неделя - {week_stat}"
                    )
            except:
                # Виджет может быть уничтожен, игнорируем ошибку
                pass
        except Exception as e:
            self.log_message(f"⚠️ Ошибка обновления отображения статистики: {e}")
    
    def setup_error_handling(self):
        """Настройка обработки необработанных исключений"""
        def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            self.log_message(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {exc_value}")
            self.log_message(f"📋 Подробности:\n{error_msg}")
            
            try:
                # Сохранить лог в файл в папке logs
                log_file = os.path.join(self.logs_dir, f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(f"Crash at {datetime.now()}\n")
                    f.write(error_msg)
                self.log_message(f"📁 Лог сохранен в: {log_file}")
            except:
                pass
            
            messagebox.showerror(
                "Критическая ошибка",
                f"Произошла критическая ошибка:\n\n{exc_value}\n\n"
                f"Программа будет остановлена. Подробности в логах."
            )
            
            self.stop_processing()
            
        sys.excepthook = handle_unhandled_exception
        
    def load_config(self):
        """Загрузка конфигурации из файла"""
        default_config = {
            "pause": "0.5",
            "screenshot": True,
            "stop_on_error": True,
            "screenshot_dir": self.screenshots_dir,  # Используем папку из конфигурации
            "start_index": "1",
            "last_json_path": ""
        }
        
        return load_config(self.config_file, default_config)
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            if self.last_json_path:
                self.config["last_json_path"] = self.last_json_path
            
            if hasattr(self, 'pause_var'):
                self.config["pause"] = self.pause_var.get()
            if hasattr(self, 'screenshot_var'):
                self.config["screenshot"] = self.screenshot_var.get()
            if hasattr(self, 'stop_on_error_var'):
                self.config["stop_on_error"] = self.stop_on_error_var.get()
            if hasattr(self, 'screenshot_dir'):
                self.config["screenshot_dir"] = self.screenshot_dir.get()
            if hasattr(self, 'start_index_var'):
                self.config["start_index"] = self.start_index_var.get()
            
            return save_config(self.config_file, self.config)
        except Exception as e:
            self.log_message(f"❌ Ошибка сохранения конфигурации: {e}")
            return False
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.families_tab = self.tabview.add("👨‍👩‍👧‍👦 Семьи")
        self.settings_tab = self.tabview.add("⚙️ Настройки")
        self.log_tab = self.tabview.add("📊 Логи")
        
        self.setup_families_tab()
        self.setup_settings_tab()
        self.setup_log_tab()
        
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.app.after(100, self.check_last_json)
        
    def on_closing(self):
        """Обработчик закрытия приложения"""
        try:
            # Останавливаем обработку перед закрытием
            if self.is_processing:
                self.stop_processing()
            
            # Уничтожаем окно
            self.app.destroy()
        except Exception as e:
            print(f"Ошибка при закрытии приложения: {e}")
            # Просто завершаем работу, если возникла ошибка
            self.app.quit()
        
        # Завершаем работу программы
        sys.exit(0)
        
        # Добавляем поддержку прокрутки колесиком мыши для всех вкладок
        self.setup_mouse_wheel_binding()
        
        # Улучшаем видимость полос прокрутки
        self.setup_scrollbar_visibility()
    
    def check_last_json(self):
        """Проверка и предложение загрузить последний JSON файл"""
        if self.last_json_path and os.path.exists(self.last_json_path):
            try:
                with open(self.last_json_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                    
                response = messagebox.askyesno(
                    "Автозагрузка", 
                    f"Обнаружен последний загруженный файл:\n{os.path.basename(self.last_json_path)}\n\nЗагрузить его сейчас?"
                )
                if response:
                    self.load_json(self.last_json_path)
            except Exception as e:
                self.log_message(f"⚠️ Ошибка проверки файла {self.last_json_path}: {e}")
                self.last_json_path = ""
                self.config["last_json_path"] = ""
                self.save_config()
    
    def setup_families_tab(self):
        """Вкладка загрузки семей"""
        main_frame = ctk.CTkFrame(self.families_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        load_frame = ctk.CTkFrame(main_frame)
        load_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(load_frame, text="📥 ЗАГРУЗКА ДАННЫХ О СЕМЬЯХ", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        
        if self.last_json_path and os.path.exists(self.last_json_path):
            file_info_frame = ctk.CTkFrame(load_frame)
            file_info_frame.pack(fill="x", padx=10, pady=5)
            
            filename = os.path.basename(self.last_json_path)
            ctk.CTkLabel(file_info_frame, 
                        text=f"📁 Последний файл: {filename}",
                        font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
            
            ctk.CTkButton(file_info_frame, text="📂 Открыть", 
                         command=lambda: self.load_json(self.last_json_path),
                         width=80, height=25).pack(side="right", padx=5)
        
        buttons_frame = ctk.CTkFrame(load_frame)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(buttons_frame, text="📝 Загрузить из JSON", 
                     command=lambda: self.load_json(), width=150).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="📋 Вставить из буфера", 
                     command=self.paste_from_clipboard, width=150).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="🧹 Очистить список", 
                     command=self.clear_families, width=150, fg_color="orange").pack(side="left", padx=5)
        
        self.families_info = ctk.CTkLabel(main_frame, text="Семей загружено: 0")
        self.families_info.pack(anchor="w", padx=10, pady=5)
        
        # Отображение статистики
        self.stat_label = ctk.CTkLabel(main_frame, text="📊 Статистика: Сегодня - 0 | Неделя - 0",
                                      font=ctk.CTkFont(size=12, weight="bold"))
        self.stat_label.pack(anchor="w", padx=10, pady=5)
        self.update_statistics_display()
        
        ctk.CTkLabel(main_frame, text="📋 ЗАГРУЖЕННЫЕ СЕМЬИ:", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=5)
        
        table_frame = ctk.CTkFrame(main_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        headers_frame = ctk.CTkFrame(table_frame)
        headers_frame.pack(fill="x", padx=5, pady=2)
        
        headers = ["№", "ФИО матери", "Дата рождения", "Детей", "Статус", "Действия"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(headers_frame, text=header, font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=i, padx=5, pady=2, sticky="ew")
            headers_frame.grid_columnconfigure(i, weight=1)
        
        self.families_scrollframe = ctk.CTkScrollableFrame(table_frame, height=300)
        self.families_scrollframe.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Привязываем прокрутку колесиком мыши к этому фрейму
        try:
            self.families_scrollframe.bind("<MouseWheel>", self._on_mousewheel)
            self.families_scrollframe.bind("<Button-4>", self._on_mousewheel)
            self.families_scrollframe.bind("<Button-5>", self._on_mousewheel)
        except:
            # Если bind не поддерживается, пропускаем
            pass
        
        self.families_widgets = []
    
    def setup_settings_tab(self):
        """Вкладка настроек автоматизации"""
        settings_frame = ctk.CTkFrame(self.settings_tab)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(settings_frame, text="⚙️ НАСТРОЙКИ АВТОМАТИЗАЦИИ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        pause_frame = ctk.CTkFrame(settings_frame)
        pause_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(pause_frame, text="Пауза между семьями (сек):").pack(side="left", padx=5)
        self.pause_var = ctk.StringVar(value=self.config.get("pause", "0.5"))
        self.pause_entry = ctk.CTkEntry(pause_frame, textvariable=self.pause_var, width=80)
        self.pause_entry.pack(side="left", padx=5)
        
        def validate_pause_input(new_value):
            if new_value == "":
                return True
            try:
                value = float(new_value)
                return 0 <= value <= 60
            except:
                return False
        
        validate_cmd = (self.app.register(validate_pause_input), '%P')
        self.pause_entry.configure(validate="key", validatecommand=validate_cmd)
        
        self.screenshot_var = ctk.BooleanVar(value=self.config.get("screenshot", True))
        ctk.CTkCheckBox(settings_frame, text="Сохранять скриншоты",
                       variable=self.screenshot_var).pack(anchor="w", padx=10, pady=5)

        self.stop_on_error_var = ctk.BooleanVar(value=self.config.get("stop_on_error", True))
        ctk.CTkCheckBox(settings_frame, text="Останавливать при ошибке",
                       variable=self.stop_on_error_var).pack(anchor="w", padx=10, pady=5)
        
        dir_frame = ctk.CTkFrame(settings_frame)
        dir_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(dir_frame, text="Папка для скриншотов:").pack(anchor="w", padx=5)
        screenshot_dir_value = self.config.get("screenshot_dir", "")
        if not screenshot_dir_value:
            screenshot_dir_value = self.screenshots_dir
        
        self.screenshot_dir = ctk.CTkEntry(dir_frame)
        self.screenshot_dir.insert(0, screenshot_dir_value)
        self.screenshot_dir.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkButton(dir_frame, text="Выбрать папку",
                     command=self.select_screenshot_dir, width=120).pack(pady=5)
        
        start_frame = ctk.CTkFrame(settings_frame)
        start_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(start_frame, text="Начать с семьи №:").pack(side="left", padx=5)
        self.start_index_var = ctk.StringVar(value=self.config.get("start_index", "1"))
        self.start_entry = ctk.CTkEntry(start_frame, textvariable=self.start_index_var, width=80)
        self.start_entry.pack(side="left", padx=5)
        
        def validate_index_input(new_value):
            if new_value == "":
                return True
            try:
                value = int(new_value)
                return 1 <= value <= 9999
            except:
                return False
        
        validate_cmd_index = (self.app.register(validate_index_input), '%P')
        self.start_entry.configure(validate="key", validatecommand=validate_cmd_index)
        
        ctk.CTkButton(settings_frame, text="💾 Сохранить настройки",
                     command=self.save_settings_ui, width=200, fg_color="green").pack(pady=20)
    
    def save_settings_ui(self):
        """Сохранение настроек из UI"""
        try:
            try:
                pause_value = float(self.pause_var.get())
                if pause_value < 0 or pause_value > 60:
                    raise ValueError("Пауза должна быть от 0 до 60 секунд")
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректное значение паузы: {e}")
                return
            
            try:
                start_index = int(self.start_index_var.get())
                if start_index < 1:
                    raise ValueError("Индекс должен быть положительным числом")
            except ValueError as e:
                messagebox.showerror("Ошибка", f"Некорректный индекс: {e}")
                return
            
            if self.save_config():
                messagebox.showinfo("Настройки", "Настройки успешно сохранены!")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить настройки")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении настроек: {e}")
        
    def setup_log_tab(self):
        """Вкладка логов"""
        log_frame = ctk.CTkFrame(self.log_tab)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(log_frame, text="📊 ЖУРНАЛ ВЫПОЛНЕНИЯ", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text.config(state="disabled")
        
        # Привязываем прокрутку колесиком мыши к этому виджету
        try:
            self.log_text.bind("<MouseWheel>", self._on_mousewheel)
            self.log_text.bind("<Button-4>", self._on_mousewheel)
            self.log_text.bind("<Button-5>", self._on_mousewheel)
        except:
            # Если bind не поддерживается, пропускаем
            pass
        
        buttons_frame = ctk.CTkFrame(log_frame)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_button = ctk.CTkButton(buttons_frame, text="🚀 Начать обработку", 
                     command=self.start_processing, width=200, fg_color="green")
        self.start_button.pack(side="left", padx=5)
        
        self.pause_button = ctk.CTkButton(buttons_frame, text="⏸️ Пауза", 
                     command=self.pause_processing, width=150, fg_color="blue")
        self.pause_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(buttons_frame, text="🛑 Остановить", 
                     command=self.stop_processing, width=150, fg_color="red")
        self.stop_button.pack(side="left", padx=5)
        
        self.continue_button = ctk.CTkButton(buttons_frame, text="▶️ Продолжить",
                     command=self.continue_processing, width=150, fg_color="green")
        self.continue_button.pack(side="left", padx=5)
        self.continue_button.configure(state="disabled")
        
        # Привязываем обработчик закрытия окна для корректной остановки
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        ctk.CTkButton(buttons_frame, text="📋 Очистить логи", 
                     command=self.clear_logs, width=150).pack(side="left", padx=5)
        
        self.progress = ctk.CTkProgressBar(log_frame)
        self.progress.pack(fill="x", padx=10, pady=5)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(log_frame, text="Готов к работе")
        self.status_label.pack(pady=5)
    
    def pause_processing(self):
        """Пауза обработки"""
        if self.is_processing:
            self.is_processing = False
            if self._pause_event:
                self._pause_event.set()
            self.log_message("⏸️ Обработка приостановлена")
            self.update_status("Приостановлено")
            
            # Обновляем состояние кнопок
            self.pause_button.configure(state="disabled")
            self.continue_button.configure(state="normal")
    
    def stop_processing(self):
        """Остановка обработки"""
        try:
            self.is_processing = False
            self.manual_intervention_required = False
            
            # Устанавливаем события остановки и паузы
            if self._stop_event:
                self._stop_event.set()
            if self._pause_event:
                self._pause_event.set()
            
            # Отменяем асинхронная задача если она есть
            if self._processing_task and self._processing_task.done():
                try:
                    self._processing_task.cancel()
                except:
                    pass
            
            # Останавливаем автоматизацию
            if self.auto_filler:
                self.auto_filler.stop_processing()
                
            # Закрываем драйвер
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                    self.log_message("🔒 Драйвер закрыт")
                except Exception as e:
                    self.log_message(f"⚠️ Ошибка при закрытии драйвера: {e}")
            
            # Ждем завершения потока
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
                
            # Разблокируем кнопки
            self.start_button.configure(state="normal")
            self.pause_button.configure(state="disabled")
            self.continue_button.configure(state="disabled")
            
            self.log_message("🛑 Обработка остановлена")
            self.update_status("Остановлено")
            
        except Exception as e:
            self.log_message(f"⚠️ Ошибка при остановке: {e}")
    
    def continue_processing(self):
        """Продолжение обработки после ручного вмешательства"""
        self.manual_intervention_required = False
        if self._pause_event:
            self._pause_event.clear()
        self.continue_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.log_message("▶️ Продолжаем обработку после ручного вмешательства")
        
        # Если обработка была приостановлена, возобновляем её
        if not self.is_processing:
            self.is_processing = True
        
        # Также сбрасываем флаг ожидания ручного вмешательства в GUI
        if hasattr(self, 'manual_intervention_required'):
            self.manual_intervention_required = False
        
        # Обновляем состояние кнопок в интерфейсе
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.stop_button.configure(state="normal")
    
    def load_json(self, file_path=None):
        """Загрузка семей из JSON файла"""
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Выберите JSON файл",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        
        if not file_path:
            return
            
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError("Файл пуст")
            if file_size > 50 * 1024 * 1024:
                raise ValueError("Файл слишком большой (больше 50 MB)")
                
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if not isinstance(data, list):
                    raise ValueError("JSON должен содержать массив семей")
                    
                families_loaded = 0
                for i, family in enumerate(data, 1):
                    try:
                        normalized_family = self.normalize_family_data(family)
                        normalized_family['status'] = 'ожидает'
                        normalized_family['error_message'] = ''
                        self.families_list.append(normalized_family)
                        families_loaded += 1
                    except Exception as e:
                        self.log_message(f"⚠️ Ошибка загрузки семьи {i}: {e}")
                        continue
                    
                self.last_json_path = file_path
                self.config["last_json_path"] = file_path
                self.save_config()
                
                self.update_families_table()
                self.update_families_info()
                self.log_message(f"✅ Загружено {families_loaded} семей из JSON файла: {os.path.basename(file_path)}")
                self.log_message(f"📊 Всего семей в списке: {len(self.families_list)}")
                
        except FileNotFoundError as e:
            messagebox.showerror("Ошибка", str(e))
        except json.JSONDecodeError as e:
            messagebox.showerror("Ошибка JSON", f"Ошибка парсинга JSON файла: {e}")
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить JSON: {str(e)}")
            self.log_message(f"❌ Ошибка загрузки JSON: {e}")
    
    def normalize_family_data(self, family):
        """Нормализация данных семьи с разделением доходов"""
        normalized = {}
        
        # Основные поля
        normalized['mother_fio'] = str(family.get('mother_fio', '')).strip()
        normalized['mother_birth'] = str(family.get('mother_birth', '')).strip()
        normalized['mother_work'] = str(family.get('mother_work', '')).strip()
        
        # Отец
        normalized['father_fio'] = str(family.get('father_fio', '')).strip()
        normalized['father_birth'] = str(family.get('father_birth', '')).strip()
        normalized['father_work'] = str(family.get('father_work', '')).strip()
        
        # Дети
        children = family.get('children', [])
        if isinstance(children, list):
            normalized['children'] = []
            for child in children:
                if isinstance(child, dict):
                    normalized_child = {
                        'fio': str(child.get('fio', '')).strip(),
                        'birth': str(child.get('birth', '')).strip(),
                        'education': str(child.get('education', '')).strip()
                    }
                    normalized['children'].append(normalized_child)
        else:
            normalized['children'] = []
        
        # Жилье
        normalized['rooms'] = str(family.get('rooms', '')).strip()
        normalized['square'] = str(family.get('square', '')).strip()
        normalized['amenities'] = str(family.get('amenities', 'со всеми удобствами')).strip()
        normalized['ownership'] = str(family.get('ownership', '')).strip()
        normalized['address'] = str(family.get('address', '')).strip()
        
        # Доходы - СБОР И РАЗДЕЛЕНИЕ ДОХОДОВ
        normalized['incomes'] = {}
        
        # Собираем доходы из отдельных полей JSON
        income_fields = {
            'mother_salary': 'mother_salary',
            'father_salary': 'father_salary',
            'unified_benefit': 'unified_benefit',
            'large_family_benefit': 'large_family_benefit',
            'survivor_pension': 'survivor_pension',
            'alimony': 'alimony',
            'disability_pension': 'disability_pension'
        }
        
        for json_key, our_key in income_fields.items():
            if json_key in family and family[json_key]:
                try:
                    value = str(family[json_key]).strip()
                    if value and value != '0':
                        normalized['incomes'][our_key] = value
                except:
                    pass
        
        # Также проверяем вложенный словарь incomes (для обратной совместимости)
        incomes_dict = family.get('incomes', {})
        if isinstance(incomes_dict, dict):
            for key, value in incomes_dict.items():
                if value and str(value).strip() and str(value).strip() != '0':
                    normalized['incomes'][key] = str(value).strip()
        
        # АДПИ
        normalized['adpi'] = str(family.get('adpi', 'нет')).strip().lower()
        normalized['install_date'] = str(family.get('install_date', '')).strip()
        normalized['check_date'] = str(family.get('check_date', '')).strip()
        
        # Телефон - ИСПРАВЛЕННАЯ ЧАСТЬ
        # Проверяем разные варианты названия поля
        phone_number = family.get('phone_number', family.get('phone', ''))
        normalized['phone'] = str(phone_number).strip()
        
        return normalized
    
    def paste_from_clipboard(self):
        """Вставка данных из буфера обмена"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            
            if not text or not text.strip():
                messagebox.showwarning("Предупреждение", "Буфер обмена пуст")
                return
                
            preview_dialog = ctk.CTkInputDialog(
                text="Вставленные данные:\n\n" + text[:500] + ("..." if len(text) > 500 else ""),
                title="Проверка данных из буфера"
            )
            
            lines = text.strip().split('\n')
            families = []
            current_family = {}
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line.startswith('=== Семья ==='):
                    if current_family:
                        families.append(current_family)
                    current_family = {'status': 'ожидает', 'error_message': ''}
                elif ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'фио матери':
                        current_family['mother_fio'] = value
                    elif key == 'дата рождения матери':
                        current_family['mother_birth'] = value
                    elif key == 'место работы матери':
                        current_family['mother_work'] = value
                    elif key == 'комнаты':
                        current_family['rooms'] = value
                    elif key == 'площадь':
                        current_family['square'] = value
                    elif key == 'телефон':
                        current_family['phone'] = value
                    elif key == 'адрес':
                        current_family['address'] = value
            
            if current_family:
                families.append(current_family)
                
            if families:
                self.families_list.extend(families)
                self.update_families_table()
                self.update_families_info()
                self.log_message(f"✅ Загружено {len(families)} семей из буфера обмена")
            else:
                self.log_message("⚠️ Не удалось распознать данные в буфере обмена")
                
        except tk.TclError:
            messagebox.showerror("Ошибка", "Не удалось получить данные из буфера обмена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при вставке: {str(e)}")
            self.log_message(f"❌ Ошибка вставки: {e}")
    
    def update_families_table(self):
        """Обновление таблицы семей"""
        try:
            # Проверяем, существует ли родительский фрейм перед обновлением
            if not self.families_scrollframe.winfo_exists():
                return
                
            # Сохраняем ссылки на старые виджеты перед их уничтожением
            old_widgets = list(self.families_widgets)
            self.families_widgets = []
            
            for i, family in enumerate(self.families_list):
                # Проверяем, существует ли родительский фрейм перед созданием новых виджетов
                if not self.families_scrollframe.winfo_exists():
                    break
                    
                row_frame = ctk.CTkFrame(self.families_scrollframe)
                row_frame.pack(fill="x", padx=5, pady=2)
                
                ctk.CTkLabel(row_frame, text=str(i+1)).grid(row=0, column=0, padx=5, pady=2)
                
                mother_fio = family.get('mother_fio', '')[:30] + ('...' if len(family.get('mother_fio', '')) > 30 else '')
                ctk.CTkLabel(row_frame, text=mother_fio).grid(row=0, column=1, padx=5, pady=2)
                
                ctk.CTkLabel(row_frame, text=family.get('mother_birth', '')).grid(row=0, column=2, padx=5, pady=2)
                
                children_count = len(family.get('children', []))
                ctk.CTkLabel(row_frame, text=str(children_count)).grid(row=0, column=3, padx=5, pady=2)
                
                status = family.get('status', 'ожидает')
                status_label = ctk.CTkLabel(row_frame, text=status)
                status_label.grid(row=0, column=4, padx=5, pady=2)
                
                if status == 'успешно':
                    status_label.configure(text_color="green")
                elif status == 'ошибка':
                    status_label.configure(text_color="red")
                elif status == 'в процессе':
                    status_label.configure(text_color="blue")
                elif status == 'пропущено':
                    status_label.configure(text_color="orange")
                elif status == 'ручное вмешательство':
                    status_label.configure(text_color="purple")
                
                actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                actions_frame.grid(row=0, column=5, padx=5, pady=2)
                
                ctk.CTkButton(actions_frame, text="✏️", width=30,
                             command=lambda idx=i: self.edit_family(idx)).pack(side="left", padx=2)
                ctk.CTkButton(actions_frame, text="👁️", width=30,
                             command=lambda idx=i: self.view_family(idx)).pack(side="left", padx=2)
                ctk.CTkButton(actions_frame, text="❌", width=30,
                             command=lambda idx=i: self.remove_family(idx)).pack(side="left", padx=2)
                
                self.families_widgets.append(row_frame)
                
                for j in range(6):
                    row_frame.grid_columnconfigure(j, weight=1)
            
            # Уничтожаем старые виджеты только после создания новых
            for widget in old_widgets:
                try:
                    # Проверяем, существует ли виджет перед уничтожением
                    if widget.winfo_exists():
                        widget.destroy()
                except:
                    # Игнорируем ошибки при уничтожении, если виджет уже уничтожен
                    pass
                    
        except Exception as e:
            self.log_message(f"❌ Ошибка обновления таблицы: {e}")
    
    def update_families_info(self):
        """Обновление информации о загруженных семьях"""
        try:
            total = len(self.families_list)
            if total == 0:
                # Проверяем, существует ли виджет перед обновлением
                try:
                    if self.families_info.winfo_exists():
                        self.families_info.configure(text="Семей загружено: 0")
                except:
                    # Виджет может быть уничтожен, игнорируем ошибку
                    pass
                return
                
            stats = {
                'ожидает': 0,
                'в процессе': 0,
                'успешно': 0,
                'ошибка': 0,
                'пропущено': 0,
                'ручное вмешательство': 0
            }
            
            for family in self.families_list:
                status = family.get('status', 'ожидает')
                if status in stats:
                    stats[status] += 1
                    
            info_text = f"Семей загружено: {total}"
            if stats['успешно'] > 0:
                info_text += f" | ✅: {stats['успешно']}"
            if stats['ошибка'] > 0:
                info_text += f" | ❌: {stats['ошибка']}"
            if stats['ожидает'] > 0:
                info_text += f" | ⏳: {stats['ожидает']}"
            if stats['ручное вмешательство'] > 0:
                info_text += f" | 🛠️: {stats['ручное вмешательство']}"
                
            # Проверяем, существует ли виджет перед обновлением
            try:
                if self.families_info.winfo_exists():
                    self.families_info.configure(text=info_text)
            except:
                # Виджет может быть уничтожен, игнорируем ошибку
                pass
            
        except Exception as e:
            self.log_message(f"⚠️ Ошибка обновления информации: {e}")
    
    def edit_family(self, index):
        """Редактирование семьи"""
        try:
            if 0 <= index < len(self.families_list):
                family = self.families_list[index]
                
                dialog = ctk.CTkToplevel(self.app)
                dialog.title(f"Редактирование семьи {index + 1}")
                dialog.geometry("600x700")
                dialog.resizable(False, False)
                
                dialog.transient(self.app)
                dialog.grab_set()
                
                scroll_frame = ctk.CTkScrollableFrame(dialog)
                scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Привязываем прокрутку колесиком мыши к этому фрейму
                try:
                    scroll_frame.bind("<MouseWheel>", self._on_mousewheel)
                    scroll_frame.bind("<Button-4>", self._on_mousewheel)
                    scroll_frame.bind("<Button-5>", self._on_mousewheel)
                except:
                    # Если bind не поддерживается, пропускаем
                    pass
                
                fields = [
                    ("ФИО матери:", "mother_fio", 300),
                    ("Дата рождения матери:", "mother_birth", 100),
                    ("Место работы матери:", "mother_work", 300),
                    ("ФИО отца:", "father_fio", 300),
                    ("Дата рождения отца:", "father_birth", 100),
                    ("Место работы отца:", "father_work", 300),
                    ("Телефон:", "phone", 150),
                    ("Адрес:", "address", 300),
                    ("Количество комнат:", "rooms", 50),
                    ("Площадь (кв.м.):", "square", 50),
                    ("Удобства:", "amenities", 200),
                    ("Собственность:", "ownership", 200),
                    ("АДПИ:", "adpi", 100),
                    ("Дата установки АДПИ:", "install_date", 100),
                    ("Дата проверки АДПИ:", "check_date", 100),
                    ("Зарплата матери:", "mother_salary", 100),
                    ("Зарплата отца:", "father_salary", 100),
                    ("Единое пособие:", "unified_benefit", 100),
                    ("Пособие многодетным:", "large_family_benefit", 100),
                ]
                
                entries = {}
                for i, (label, key, width) in enumerate(fields):
                    ctk.CTkLabel(scroll_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="w")
                    
                    if key in ['mother_salary', 'father_salary', 'unified_benefit', 'large_family_benefit']:
                        value = family.get('incomes', {}).get(key, '')
                    else:
                        value = family.get(key, '')
                    
                    entry = ctk.CTkEntry(scroll_frame, width=width)
                    entry.insert(0, str(value))
                    entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                    entries[key] = entry
                
                button_frame = ctk.CTkFrame(dialog)
                button_frame.pack(fill="x", padx=10, pady=10)
                
                def save_changes():
                    try:
                        for key, entry in entries.items():
                            new_value = entry.get().strip()
                            
                            if key == 'adpi':
                                new_value = new_value.lower()
                            
                            if key in ['mother_salary', 'father_salary', 'unified_benefit', 'large_family_benefit']:
                                if 'incomes' not in self.families_list[index]:
                                    self.families_list[index]['incomes'] = {}
                                if new_value:
                                    self.families_list[index]['incomes'][key] = new_value
                                elif key in self.families_list[index].get('incomes', {}):
                                    del self.families_list[index]['incomes'][key]
                            else:
                                self.families_list[index][key] = new_value
                        
                        self.update_families_table()
                        self.log_message(f"✏️ Семья {index + 1} отредактирована")
                        dialog.destroy()
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Ошибка сохранения: {e}")
                
                ctk.CTkButton(button_frame, text="💾 Сохранить", command=save_changes, fg_color="green").pack(side="left", padx=5)
                ctk.CTkButton(button_frame, text="❌ Отмена", command=dialog.destroy).pack(side="left", padx=5)
                
                dialog.wait_window()
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка редактирования: {e}")
    
    def view_family(self, index):
        """Просмотр подробной информации о семье"""
        try:
            if 0 <= index < len(self.families_list):
                family = self.families_list[index]
                
                dialog = ctk.CTkToplevel(self.app)
                dialog.title(f"Просмотр семьи {index + 1}")
                dialog.geometry("500x600")
                
                text_widget = scrolledtext.ScrolledText(dialog, width=60, height=30)
                text_widget.pack(fill="both", expand=True, padx=10, pady=10)
                
                # Привязываем прокрутку колесиком мыши к этому виджету
                try:
                    text_widget.bind("<MouseWheel>", self._on_mousewheel)
                    text_widget.bind("<Button-4>", self._on_mousewheel)
                    text_widget.bind("<Button-5>", self._on_mousewheel)
                except:
                    # Если bind не поддерживается, пропускаем
                    pass
                
                info_text = f"=== Семья {index + 1} ===\n\n"
                info_text += f"Статус: {family.get('status', 'неизвестно')}\n"
                
                if family.get('error_message'):
                    info_text += f"Ошибка: {family['error_message']}\n\n"
                
                info_text += "\n=== Основная информация ===\n"
                info_text += f"Мать: {family.get('mother_fio', '')} ({family.get('mother_birth', '')})\n"
                info_text += f"Работа: {family.get('mother_work', '')}\n"
                info_text += f"Телефон: {family.get('phone', '')}\n"
                info_text += f"Адрес: {family.get('address', '')}\n"
                
                if family.get('father_fio'):
                    info_text += f"\nОтец: {family['father_fio']} ({family.get('father_birth', '')})\n"
                    info_text += f"Работа: {family.get('father_work', '')}\n"
                
                info_text += "\n=== Дети ===\n"
                children = family.get('children', [])
                if children:
                    for i, child in enumerate(children, 1):
                        info_text += f"{i}. {child.get('fio', '')} ({child.get('birth', '')}) - {child.get('education', '')}\n"
                else:
                    info_text += "Детей нет\n"
                
                info_text += "\n=== Жилье ===\n"
                info_text += f"Комнат: {family.get('rooms', '')}\n"
                info_text += f"Площадь: {family.get('square', '')} кв.м.\n"
                info_text += f"Удобства: {family.get('amenities', '')}\n"
                info_text += f"Собственность: {family.get('ownership', '')}\n"
                
                info_text += "\n=== Доходы ===\n"
                incomes = family.get('incomes', {})
                if incomes:
                    income_labels = {
                        'mother_salary': 'Зарплата матери',
                        'father_salary': 'Зарплата отца',
                        'unified_benefit': 'Единое пособие',
                        'large_family_benefit': 'Пособие по многодетности',
                        'survivor_pension': 'Пенсия по потере кормильца',
                        'alimony': 'Алименты',
                        'disability_pension': 'Пенсия по инвалидности'
                    }
                    
                    for key, value in incomes.items():
                        label = income_labels.get(key, key)
                        info_text += f"{label}: {value}\n"
                else:
                    info_text += "Доходы не указаны\n"
                
                info_text += f"\n=== АДПИ ===\n"
                info_text += f"Наличие: {family.get('adpi', 'нет')}\n"
                info_text += f"Дата установки: {family.get('install_date', '')}\n"
                info_text += f"Дата проверки: {family.get('check_date', '')}\n"
                
                text_widget.insert("1.0", info_text)
                text_widget.config(state="disabled")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка просмотра: {e}")
    
    def remove_family(self, index):
        """Удаление семьи из списка"""
        try:
            if 0 <= index < len(self.families_list):
                family_info = self.families_list[index].get('mother_fio', f'семья {index + 1}')
                if messagebox.askyesno("Подтверждение", f"Удалить семью:\n\n{family_info}?"):
                    del self.families_list[index]
                    self.update_families_table()
                    self.update_families_info()
                    self.log_message(f"🗑️ Удалена семья {index + 1}")
                    
        except Exception as e:
            self.log_message(f"❌ Ошибка удаления семьи: {e}")
    
    def clear_families(self):
        """Очистка списка семей"""
        try:
            if not self.families_list:
                return
                
            if messagebox.askyesno("Подтверждение", "Очистить весь список семей?"):
                self.families_list = []
                self.update_families_table()
                self.update_families_info()
                self.log_message("🧹 Список семей очищен")
                
        except Exception as e:
            self.log_message(f"❌ Ошибка очистки списка: {e}")
    
    def select_screenshot_dir(self):
        """Выбор директории для скриншотов"""
        try:
            initial_dir = self.screenshot_dir.get() if hasattr(self, 'screenshot_dir') else None
            dir_path = filedialog.askdirectory(
                title="Выберите папку для скриншотов",
                initialdir=initial_dir
            )
            if dir_path:
                self.screenshot_dir.delete(0, 'end')
                self.screenshot_dir.insert(0, dir_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка выбора директории: {e}")
    
    def clear_logs(self):
        """Очистка логов"""
        try:
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка очистки логов: {e}")
    
    def update_progress(self, value):
        """Обновление прогресса"""
        try:
            # Проверяем, существует ли виджет перед обновлением
            try:
                # Проверяем, что виджет существует и не был уничтожен
                if self.progress.winfo_exists():
                    self.progress.set(value)
                    self.app.update_idletasks()
            except:
                # Виджет может быть уничтожен, игнорируем ошибку
                pass
        except:
            pass
    
    def update_status(self, message):
        """Обновление статуса"""
        try:
            # Проверяем, существует ли виджет перед обновлением
            try:
                # Проверяем, что виджет существует и не был уничтожен
                if self.status_label.winfo_exists():
                    self.status_label.configure(text=message)
                    self.app.update_idletasks()
            except:
                # Виджет может быть уничтожен, игнорируем ошибку
                pass
        except:
            pass
    
    def start_processing(self):
        """Начало обработки семей с выбором стартовой семьи"""
        try:
            if not self.families_list:
                messagebox.showwarning("Предупреждение", "Нет семей для обработки")
                return
                
            if self.is_processing:
                messagebox.showwarning("Предупреждение", "Обработка уже запущена")
                return
            
            if not self.check_database_connection():
                self.log_message("❌ Не удалось подключиться к базе данных")
                return
            
            # Создаем диалог выбора стартовой семьи
            dialog = ctk.CTkToplevel(self.app)
            dialog.title("Выбор начальной семьи")
            dialog.geometry("600x500")  # Увеличили размер окна
            dialog.resizable(False, False)
            dialog.transient(self.app)
            dialog.grab_set()
            
            ctk.CTkLabel(dialog, text="Выберите с какой семьи начать обработку:", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
            
            # Получаем список семей с их статусами
            families_data = []
            for i, family in enumerate(self.families_list):
                status = family.get('status', 'ожидает')
                status_icon = ""
                if status == 'успешно':
                    status_icon = "✅"
                elif status == 'ошибка':
                    status_icon = "❌"
                elif status == 'ожидает':
                    status_icon = "⏳"
                elif status == 'ручное вмешательство':
                    status_icon = "🛠️"
                
                families_data.append(f"{i+1}. {family.get('mother_fio', '')[:30]}... {status_icon}")
            
            # Прокручиваемый список семей с увеличенной высотой
            families_listbox = scrolledtext.ScrolledText(dialog, height=10, width=70)  # Увеличили ширину и уменьшили высоту
            families_listbox.pack(pady=10, padx=20, fill="both", expand=True)
            
            # Привязываем прокрутку колесиком мыши к этому виджету
            try:
                families_listbox.bind("<MouseWheel>", self._on_mousewheel)
                families_listbox.bind("<Button-4>", self._on_mousewheel)
                families_listbox.bind("<Button-5>", self._on_mousewheel)
            except:
                # Если bind не поддерживается, пропускаем
                pass
            
            for family_info in families_data:
                families_listbox.insert("end", family_info + "\n")
            families_listbox.config(state="disabled")
            
            # Поле для ввода номера семьи
            input_frame = ctk.CTkFrame(dialog)
            input_frame.pack(pady=10, padx=20, fill="x")
            
            ctk.CTkLabel(input_frame, text="Или введите номер семьи:").pack(side="left", padx=5)
            family_number_var = ctk.StringVar(value="1")
            family_number_entry = ctk.CTkEntry(input_frame, textvariable=family_number_var, width=100)
            family_number_entry.pack(side="left", padx=5)
            
            def validate_family_number():
                try:
                    num_str = family_number_var.get().strip()
                    if not num_str:
                        messagebox.showerror("Ошибка", "Введите номер семьи")
                        return False
                    num = int(num_str)
                    if 1 <= num <= len(self.families_list):
                        return True
                    else:
                        messagebox.showerror("Ошибка", f"Номер должен быть от 1 до {len(self.families_list)}")
                        return False
                except ValueError:
                    messagebox.showerror("Ошибка", "Введите корректный номер")
                    return False
            
            # Кнопки - делаем вертикальный layout
            button_frame = ctk.CTkFrame(dialog)
            button_frame.pack(pady=10, padx=20, fill="x")
            
            # Первая строка кнопок
            button_row1 = ctk.CTkFrame(button_frame, fg_color="transparent")
            button_row1.pack(fill="x", pady=5)
            
            ctk.CTkButton(button_row1, text="Начать с выбранной", 
                         command=lambda: start_from_beginning(), width=200).pack(side="left", padx=5)
            ctk.CTkButton(button_row1, text="Начать с ошибки", 
                         command=lambda: start_from_error(), width=200).pack(side="right", padx=5)
            
            # Вторая строка кнопок
            button_row2 = ctk.CTkFrame(button_frame, fg_color="transparent")
            button_row2.pack(fill="x", pady=5)
            
            ctk.CTkButton(button_row2, text="Начать с ожидающей", 
                         command=lambda: start_from_pending(), width=200).pack(side="left", padx=5)
            ctk.CTkButton(button_row2, text="Начать с необработанной", 
                         command=lambda: start_from_last_unprocessed(), width=200).pack(side="right", padx=5)
            
            # Кнопка отмены
            button_row3 = ctk.CTkFrame(button_frame, fg_color="transparent")
            button_row3.pack(fill="x", pady=10)
            
            ctk.CTkButton(button_row3, text="❌ Отмена", 
                         command=dialog.destroy, width=200, fg_color="gray").pack()
            
            def start_from_beginning():
                if validate_family_number():
                    start_index = int(family_number_var.get()) - 1
                    if 0 <= start_index < len(self.families_list):
                        self._start_processing_from_index(start_index)
                        dialog.destroy()
                    else:
                        messagebox.showerror("Ошибка", f"Индекс вне диапазона. Должен быть от 1 до {len(self.families_list)}")
            
            def start_from_error():
                # Ищем первую семью со статусом "ошибка"
                error_index = -1
                for i, family in enumerate(self.families_list):
                    if family.get('status') == 'ошибка':
                        error_index = i
                        break
                
                if error_index != -1:
                    self._start_processing_from_index(error_index)
                    dialog.destroy()
                else:
                    messagebox.showinfo("Информация", "Нет семей со статусом 'ошибка'")
            
            def start_from_pending():
                # Ищем первую семью со статусом "ожидает"
                pending_index = -1
                for i, family in enumerate(self.families_list):
                    if family.get('status') == 'ожидает':
                        pending_index = i
                        break
                
                if pending_index != -1:
                    self._start_processing_from_index(pending_index)
                    dialog.destroy()
                else:
                    messagebox.showinfo("Информация", "Нет семей со статусом 'ожидает'")
            
            def start_from_last_unprocessed():
                # Ищем первую необработанную семью (не "успешно")
                unprocessed_index = -1
                for i, family in enumerate(self.families_list):
                    if family.get('status') not in ['успешно', 'пропущено']:
                        unprocessed_index = i
                        break
                
                if unprocessed_index != -1:
                    self._start_processing_from_index(unprocessed_index)
                    dialog.destroy()
                else:
                    messagebox.showinfo("Информация", "Все семьи уже обработаны")
            
            dialog.wait_window()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска обработки: {e}")
            messagebox.showerror("Ошибка", f"Не удалось запустить обработку: {e}")
    
    def _start_processing_from_index(self, start_index):
        """Внутренний метод для начала обработки с указанного индекса"""
        try:
            self.current_family_index = start_index
            self.is_processing = True
            
            # Инициализируем asyncio примитивы
            self._pause_event = asyncio.Event()
            self._stop_event = asyncio.Event()
            
            self.start_button.configure(state="disabled")
            self.save_config()
            
            # Запускаем асинхронную обработку в отдельном потоке
            self.processing_thread = threading.Thread(
                target=self._run_async_processing,
                daemon=False
            )
            self.processing_thread.start()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска обработки: {e}")
            self.is_processing = False
            self.start_button.configure(state="normal")
    
    def _run_async_processing(self):
        """Запуск асинхронной обработки в отдельном потоке"""
        try:
            # Создаем новый event loop для потока
            self._async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._async_loop)
            
            # Запускаем асинхронную обработку
            self._processing_task = self._async_loop.create_task(
                self.process_families_async()
            )
            
            # Запускаем event loop
            self._async_loop.run_until_complete(self._processing_task)
            
        except asyncio.CancelledError:
            self.log_message("🛑 Задача обработки отменена")
        except Exception as e:
            self.log_message(f"❌ Ошибка в асинхронной обработке: {e}")
        finally:
            # Закрываем loop
            if self._async_loop and not self._async_loop.is_closed():
                self._async_loop.close()
            self._async_loop = None
            
            # Обновляем UI в основном потоке через after
            self.app.after(0, self._on_processing_finished)
    
    def _on_processing_finished(self):
        """Обработка завершения асинхронной обработки"""
        self.is_processing = False
        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled")
        self.continue_button.configure(state="disabled")
    
    def check_database_connection(self):
        """Проверка подключения к базе данных"""
        try:
            self.log_message("🔗 Проверка подключения к базе данных...")
            
            try:
                driver = webdriver.Chrome()
                driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
                time.sleep(1)
                
                if "Поиск информации" in driver.title or "FindInfo.aspx" in driver.current_url:
                    self.log_message("✅ Подключение к базе данных установлено")
                    driver.quit()
                    return True
                else:
                    self.log_message("❌ Не удалось загрузить страницу поиска")
                    driver.quit()
                    return False
                    
            except Exception as e:
                self.log_message(f"❌ Ошибка подключения: {e}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Ошибка проверки подключения: {e}")
            return False
    
    async def process_families_async(self):
        """Асинхронный цикл обработки семей с повторной обработкой ошибок"""
        try:
            total = len(self.families_list)
            processed_count = 0
            success_count = 0
            error_count = 0
            skipped_count = 0
            retry_families = []
            
            self.success_count = 0
            
            self.log_message(f"🚀 Начало асинхронной обработки {total - self.current_family_index} семей")
            self.update_status("Идет асинхронная обработка...")
            
            for i in range(self.current_family_index, total):
                if self._stop_event.is_set():
                    self.log_message("⏹️ Обработка остановлена")
                    break
                
                if self._pause_event.is_set():
                    self.log_message("⏸️ Обработка приостановлена (ожидание продолжения)")
                    try:
                        await asyncio.wait_for(self._pause_event.wait(), timeout=0.5)
                    except asyncio.TimeoutError:
                        pass
                    continue
                
                if not self.is_processing:
                    self.log_message("⏸️ Обработка приостановлена пользователем")
                    break
                    
                family = self.families_list[i]
                processed_count += 1
                
                try:
                    if family.get('status') == 'успешно':
                        self.log_message(f"⏭️ Пропускаем семью {i+1} - уже обработана")
                        skipped_count += 1
                        continue
                    
                    family['status'] = 'в процессе'
                    self.app.after(0, self.update_families_table)
                    
                    self.log_message(f"\n📋 Обработка семьи {i+1}/{total}")
                    self.log_message(f"👩 Мать: {family.get('mother_fio', '')}")
                    
                    if not family.get('mother_fio') and not family.get('father_fio'):
                        self.log_message("⚠️ Пропуск: не указано ФИО матери или отца")
                        family['status'] = 'пропущено'
                        family['error_message'] = 'Не указано ФИО матери или отца'
                        skipped_count += 1
                        continue
                    
                    if self.manual_intervention_required:
                        family['status'] = 'ручное вмешательство'
                        self.log_message("🛠️ Требуется ручное вмешательство")
                        self.app.after(0, lambda: self.continue_button.configure(state="normal"))
                        self.app.after(0, lambda: self.pause_button.configure(state="disabled"))
                        self.log_message("⏳ Ожидаю ручного вмешательства...")
                        
                        while self.manual_intervention_required and self.is_processing and not self._stop_event.is_set():
                            await asyncio.sleep(0.5)
                        
                        if self._stop_event.is_set():
                            break
                        
                        self.log_message("▶️ Продолжаем после ручного вмешательства")
                        self.app.after(0, lambda: self.continue_button.configure(state="disabled"))
                        self.app.after(0, lambda: self.pause_button.configure(state="normal"))
                    
                    success = await self.process_single_family_async(family, i+1)
                    
                    if success:
                        family['status'] = 'успешно'
                        family['error_message'] = ''
                        success_count += 1
                        self.log_message(f"✅ Семья {i+1} обработана успешно")
                    else:
                        family['status'] = 'ошибка'
                        family['error_message'] = 'Ошибка при обработке'
                        error_count += 1
                        retry_families.append(i)
                        self.log_message(f"❌ Ошибка при обработке семьи {i+1}")
                        
                        if self.stop_on_error_var.get():
                            self.log_message("⏸️ Остановка из-за ошибки")
                            break
                        
                except Exception as e:
                    error_msg = str(e)
                    self.log_message(f"❌ Критическая ошибка обработки семьи: {error_msg}")
                    family['status'] = 'ошибка'
                    family['error_message'] = error_msg
                    error_count += 1
                    retry_families.append(i)
                    
                    if self.stop_on_error_var.get():
                        self.log_message("⏸️ Остановка из-за критической ошибки")
                        break
                        
                finally:
                    progress_value = (i + 1) / total
                    self.app.after(0, lambda v=progress_value: self.progress.set(v))
                    status_text = f"Обработано: {i+1}/{total} | ✅: {success_count} | ❌: {error_count} | ⏭️: {skipped_count}"
                    self.app.after(0, lambda t=status_text: self.status_label.configure(text=t))
                    self.app.after(0, self.update_families_table)
                    
                    if i < total - 1 and self.is_processing and not self._stop_event.is_set():
                        try:
                            pause_time = float(self.pause_var.get())
                            if pause_time > 0:
                                await asyncio.sleep(pause_time)
                        except:
                            await asyncio.sleep(0.5)
            
            if retry_families and self.is_processing and not self._stop_event.is_set():
                self.log_message(f"\n🔄 Повторная обработка {len(retry_families)} семей с ошибками...")
                
                for idx, family_idx in enumerate(retry_families):
                    if self._stop_event.is_set() or not self.is_processing:
                        break
                        
                    family = self.families_list[family_idx]
                    self.log_message(f"\n🔄 Повторная обработка семьи {family_idx+1}/{total} (попытка 2)")
                    
                    family['status'] = 'в процессе'
                    self.app.after(0, self.update_families_table)
                    
                    success = await self.process_single_family_async(family, family_idx+1)
                    
                    if success:
                        family['status'] = 'успешно'
                        family['error_message'] = ''
                        success_count += 1
                        error_count -= 1
                        self.log_message(f"✅ Семья {family_idx+1} обработана успешно при повторной попытке")
                    else:
                        family['status'] = 'ошибка'
                        family['error_message'] = 'Не удалось обработать после 2 попыток'
                        self.log_message(f"❌ Семья {family_idx+1} не обработана после 2 попыток")
                    
                    self.app.after(0, self.update_families_table)
                    
                    if idx < len(retry_families) - 1 and self.is_processing:
                        try:
                            pause_time = float(self.pause_var.get())
                            if pause_time > 0:
                                await asyncio.sleep(pause_time)
                        except:
                            await asyncio.sleep(0.5)
            
            self.is_processing = False
            self.app.after(0, lambda: self.start_button.configure(state="normal"))
            self.app.after(0, lambda: self.pause_button.configure(state="disabled"))
            self.app.after(0, lambda: self.continue_button.configure(state="disabled"))
            
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                    self.log_message("🔒 Драйвер закрыт")
                except:
                    pass
            
            if success_count > 0:
                self.update_statistics(success_count)
            
            self.log_message(f"\n🏁 Асинхронная обработка завершена!")
            self.log_message(f"📊 Итоги: Всего {processed_count} | Успешно {success_count} | Ошибки {error_count} | Пропущено {skipped_count}")
            
            today_stat, week_stat = self.get_statistics_for_period()
            self.log_message(f"📈 Статистика: Сегодня - {today_stat} | Неделя - {week_stat}")
            
            if error_count == 0 and skipped_count == 0:
                self.app.after(0, lambda: self.update_status("✅ Все семьи обработаны успешно!"))
            else:
                self.app.after(0, lambda: self.update_status(f"Обработка завершена с {error_count} ошибками"))
            
            self.app.after(0, self.handle_completed_families)
            
        except Exception as e:
            self.log_message(f"❌ Критическая ошибка в асинхронном цикле: {e}")
            self.app.after(0, lambda: self.update_status("Ошибка обработки"))
            self.is_processing = False
            self.app.after(0, lambda: self.start_button.configure(state="normal"))
            self.app.after(0, lambda: self.pause_button.configure(state="disabled"))
            self.app.after(0, lambda: self.continue_button.configure(state="disabled"))
    
    async def process_single_family_async(self, family_data, family_number):
        """Асинхронная обработка одной семьи с повторными попытками"""
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                self.log_message(f"🔄 Попытка {attempt + 1} обработки семьи {family_number}")
                
                if self._stop_event.is_set():
                    return False
                
                if attempt > 0:
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None
                    
                    self.auto_filler = AutoFormFillerMass(self)
                    if not self.auto_filler._setup_driver():
                        self.log_message("❌ Не удалось настроить драйвер")
                        continue
                    self.driver = self.auto_filler.driver
                elif not self.driver:
                    self.auto_filler = AutoFormFillerMass(self)
                    if not self.auto_filler._setup_driver():
                        self.log_message("❌ Не удалось настроить драйвер")
                        continue
                    self.driver = self.auto_filler.driver
                else:
                    self.auto_filler = AutoFormFillerMass(self)
                    try:
                        _ = self.driver.current_url
                        self.auto_filler.driver = self.driver
                        self.auto_filler.wait = WebDriverWait(self.driver, 10)
                    except:
                        self.log_message("⚠️ Драйвер неактивен, создаем новый")
                        if self.driver:
                            try:
                                self.driver.quit()
                            except:
                                pass
                        self.driver = None
                        self.auto_filler = AutoFormFillerMass(self)
                        if not self.auto_filler._setup_driver():
                            self.log_message("❌ Не удалось настроить драйвер")
                            continue
                        self.driver = self.auto_filler.driver
                
                if self.screenshot_var.get():
                    screenshot_dir = self.screenshot_dir.get().strip()
                    if not screenshot_dir:
                        screenshot_dir = self.screenshots_dir
                    self.auto_filler.screenshot_dir = screenshot_dir
                
                success = self.auto_filler.process_family(family_data, family_number)
                
                if success:
                    return True
                else:
                    self.log_message(f"❌ Попытка {attempt + 1} не удалась")
                    if attempt < max_attempts - 1:
                        self.log_message("🔄 Возвращаемся на страницу поиска...")
                        try:
                            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
                            await asyncio.sleep(0.2)
                        except:
                            pass
                
            except Exception as e:
                self.log_message(f"❌ Ошибка в process_single_family_async (попытка {attempt + 1}): {str(e)}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)
        
        self.log_message(f"❌ Обработка семьи {family_number} не удалась после {max_attempts} попыток")
        return False
    
    def process_families(self):
        """Основной цикл обработки семей (синхронный, вызывает асинхронный метод)"""
        # Этот метод оставлен для совместимости, но теперь использует асинхронную версию
        if self._async_loop and not self._async_loop.is_closed():
            # Если loop существует, запускаем асинхронную обработку
            try:
                self._async_loop.run_until_complete(self.process_families_async())
            except:
                pass
        else:
            # Fallback на синхронную обработку если async не работает
            self._sync_process_families()
    
    def _sync_process_families(self):
        """Синхронный цикл обработки семей (резервный метод)"""
        # Это резервный синхронный метод, если асинхронная обработка не работает
        pass  # Синхронная логика перенесена в process_families_async
            
    def process_single_family_with_retry(self, family_data, family_number):
        """Обработка одной семьи с повторными попытками"""
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                self.log_message(f"🔄 Попытка {attempt + 1} обработки семьи {family_number}")
                
                # При повторной попытке перезапускаем драйвер
                if attempt > 0:
                    if self.driver:
                        try:
                            self.driver.quit()
                        except Exception as e:
                            self.log_message(f"⚠️ Ошибка при закрытии драйвера: {e}")
                        self.driver = None
                    
                    self.auto_filler = AutoFormFillerMass(self)
                    if not self.auto_filler._setup_driver():
                        self.log_message("❌ Не удалось настроить драйвер")
                        continue
                    self.driver = self.auto_filler.driver
                elif not self.driver:
                    # Первая попытка, но драйвера нет
                    self.auto_filler = AutoFormFillerMass(self)
                    if not self.auto_filler._setup_driver():
                        self.log_message("❌ Не удалось настроить драйвер")
                        continue
                    self.driver = self.auto_filler.driver
                else:
                    # Используем существующий драйвер
                    self.auto_filler = AutoFormFillerMass(self)
                    # Проверяем, что драйвер все еще активен
                    try:
                        # Проверяем, можно ли получить URL страницы
                        _ = self.driver.current_url
                        self.auto_filler.driver = self.driver
                        self.auto_filler.wait = WebDriverWait(self.driver, 10)
                    except:
                        # Драйвер больше не активен, нужно создать новый
                        self.log_message("⚠️ Драйвер больше не активен, создаем новый")
                        if self.driver:
                            try:
                                self.driver.quit()
                            except Exception as e:
                                self.log_message(f"⚠️ Ошибка при закрытии старого драйвера: {e}")
                        self.driver = None
                        
                        self.auto_filler = AutoFormFillerMass(self)
                        if not self.auto_filler._setup_driver():
                            self.log_message("❌ Не удалось настроить драйвер")
                            continue
                        self.driver = self.auto_filler.driver
                
                # Устанавливаем путь для скриншотов
                if self.screenshot_var.get():
                    screenshot_dir = self.screenshot_dir.get().strip()
                    if not screenshot_dir:
                        screenshot_dir = self.screenshots_dir
                        
                    if not os.path.exists(screenshot_dir):
                        try:
                            os.makedirs(screenshot_dir)
                            self.log_message(f"📁 Создана папка для скриншотов: {screenshot_dir}")
                        except Exception as e:
                            self.log_message(f"⚠️ Не удалось создать папку для скриншотов: {e}")
                            screenshot_dir = None
                            
                    self.auto_filler.screenshot_dir = screenshot_dir
                    
                # Запускаем автоматизацию
                success = self.auto_filler.process_family(family_data, family_number)
                
                if success:
                    return True
                else:
                    self.log_message(f"❌ Попытка {attempt + 1} не удалась")
                    if attempt < max_attempts - 1:
                        self.log_message("🔄 Возвращаемся на страницу поиска для повторной попытки...")
                        # Возвращаемся на страницу поиска
                        try:
                            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
                            time.sleep(0.2)
                        except:
                            pass
                
            except Exception as e:
                self.log_message(f"❌ Ошибка в process_single_family (попытка {attempt + 1}): {str(e)}")
                import traceback
                self.log_message(f"📋 Трассировка:\n{traceback.format_exc()}")
                if attempt < max_attempts - 1:
                    self.log_message("🔄 Пробуем еще раз...")
                    time.sleep(1)
        
        self.log_message(f"❌ Обработка семьи {family_number} не удалась после {max_attempts} попыток")
        return False
    
    def _update_progress_and_status(self, current_index, total_count, success_count, error_count, skipped_count):
        """Обновление прогресса и статуса с детальной информацией"""
        # Обновляем прогресс
        progress_value = current_index / total_count
        self.update_progress(progress_value)
        
        # Обновляем статус с детальной информацией
        status_text = f"Обработано: {current_index}/{total_count} | ✅: {success_count} | ❌: {error_count} | ⏭️: {skipped_count}"
        self.update_status(status_text)
        
        # Проверяем, не остановлена ли обработка, чтобы избежать лишних обновлений UI
        if self.is_processing:
            self.update_families_table()

    def handle_completed_families(self):
        """Обработка завершенных семей - выбор, перемещение в completed и удаление из исходного файла"""
        try:
            # Проверяем, есть ли исходный JSON файл
            if not self.last_json_path or not os.path.exists(self.last_json_path):
                self.log_message("⚠️ Не найден исходный JSON файл для обработки завершенных семей")
                return

            # Получаем успешно обработанные семьи
            completed_families = []
            for family in self.families_list:
                if family.get('status') == 'успешно':
                    completed_families.append(family)

            if not completed_families:
                self.log_message("ℹ️ Нет успешно обработанных семей для перемещения")
                return

            # Создаем диалог для выбора семей для перемещения в completed
            self.show_completed_families_dialog(completed_families)

        except Exception as e:
            self.log_message(f"❌ Ошибка при обработке завершенных семей: {e}")
            import traceback
            self.log_message(f"📋 Трассировка:\n{traceback.format_exc()}")

    def show_completed_families_dialog(self, completed_families):
        """Показать диалог для выбора семей для добавления в completed"""
        try:
            dialog = ctk.CTkToplevel(self.app)
            dialog.title("Выбор семей для завершения")
            dialog.geometry("800x600")
            dialog.transient(self.app)
            dialog.grab_set()

            # Заголовок
            ctk.CTkLabel(dialog, text="Выберите семьи для добавления в завершенные:",
                        font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

            # Прокручиваемый фрейм для чекбоксов
            scroll_frame = ctk.CTkScrollableFrame(dialog, height=400)
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

            # Создаем переменные для чекбоксов
            family_vars = []
            for i, family in enumerate(completed_families):
                var = ctk.BooleanVar(value=True)  # По умолчанию все отмечены
                family_vars.append(var)
                
                mother_fio = family.get('mother_fio', 'Неизвестно')
                father_fio = family.get('father_fio', '')
                children_count = len(family.get('children', []))
                
                text = f"{i+1}. {mother_fio}"
                if father_fio:
                    text += f" + {father_fio}"
                text += f" ({children_count} детей)"
                
                checkbox = ctk.CTkCheckBox(scroll_frame, text=text, variable=var)
                checkbox.pack(anchor="w", pady=2)

            # Кнопки управления
            button_frame = ctk.CTkFrame(dialog)
            button_frame.pack(fill="x", padx=20, pady=10)

            def select_all():
                for var in family_vars:
                    var.set(True)

            def deselect_all():
                for var in family_vars:
                    var.set(False)

            def process_selection():
                try:
                    # Получаем выбранные семьи
                    selected_families = []
                    for i, var in enumerate(family_vars):
                        if var.get():
                            selected_families.append(completed_families[i])

                    if not selected_families:
                        messagebox.showwarning("Предупреждение", "Не выбрано ни одной семьи")
                        return

                    # Обрабатываем выбранные семьи
                    self.process_selected_completed_families(selected_families)
                    
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Ошибка при обработке выбора: {e}")

            ctk.CTkButton(button_frame, text="Выбрать все", command=select_all, width=100).pack(side="left", padx=5)
            ctk.CTkButton(button_frame, text="Снять все", command=deselect_all, width=100).pack(side="left", padx=5)
            ctk.CTkButton(button_frame, text="Добавить в завершенные", command=process_selection,
                         width=200, fg_color="green").pack(side="right", padx=5)
            ctk.CTkButton(button_frame, text="Отмена", command=dialog.destroy,
                         width=100, fg_color="gray").pack(side="right", padx=5)

        except Exception as e:
            self.log_message(f"❌ Ошибка при показе диалога завершенных семей: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при показе диалога: {e}")

    def process_selected_completed_families(self, selected_families):
        """Обработка выбранных семей - добавление в completed JSON и удаление из исходного"""
        try:
            # Создаем папку completed, если не существует
            completed_dir = os.path.join(os.path.dirname(self.last_json_path), "completed")
            if not os.path.exists(completed_dir):
                os.makedirs(completed_dir)

            # Получаем текущую неделю в формате YYYY-Www (год-номер недели)
            current_date = datetime.now()
            year, week_num = current_date.isocalendar()[:2]  # Получаем год и номер недели
            week_folder_name = f"{year}-W{week_num:02d}"  # Формат: 2026-W03
            week_dir = os.path.join(completed_dir, week_folder_name)
            
            # Создаем подпапку для текущей недели, если не существует
            if not os.path.exists(week_dir):
                os.makedirs(week_dir)
                self.log_message(f"📁 Создана недельная папка: {week_folder_name}")

            # Формируем имя файла с сегодняшней датой
            today_date = current_date.strftime("%d.%m.%Y")
            completed_filename = f"{today_date}_completed_families.json"
            completed_filepath = os.path.join(week_dir, completed_filename)

            # Загружаем существующие завершенные семьи, если файл существует
            existing_completed = []
            if os.path.exists(completed_filepath):
                with open(completed_filepath, 'r', encoding='utf-8') as f:
                    try:
                        existing_completed = json.load(f)
                        if not isinstance(existing_completed, list):
                            existing_completed = []
                    except json.JSONDecodeError:
                        existing_completed = []

            # Добавляем новые завершенные семьи
            existing_completed.extend(selected_families)

            # Сохраняем обновленный список завершенных семей
            with open(completed_filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_completed, f, ensure_ascii=False, indent=2)

            self.log_message(f"✅ {len(selected_families)} семей добавлено в {completed_filename}")

            # Удаляем выбранные семьи из исходного JSON файла
            self.remove_families_from_source(selected_families)
            
            # Добавляем поле isPainted = true для всех перемещенных семей
            for family in selected_families:
                family['isPainted'] = True

        except Exception as e:
            self.log_message(f"❌ Ошибка при обработке выбранных завершенных семей: {e}")
            import traceback
            self.log_message(f"📋 Трассировка:\n{traceback.format_exc()}")

    def remove_families_from_source(self, families_to_remove):
        """Удаление семей из исходного JSON файла"""
        try:
            # Загружаем исходный JSON
            with open(self.last_json_path, 'r', encoding='utf-8') as f:
                all_families = json.load(f)

            # Создаем множество ФИО для быстрого поиска
            families_to_remove_set = set()
            for family in families_to_remove:
                mother_fio = family.get('mother_fio', '').strip().lower()
                father_fio = family.get('father_fio', '').strip().lower()
                families_to_remove_set.add(mother_fio)
                if father_fio:
                    families_to_remove_set.add(father_fio)

            # Фильтруем семьи, исключая те, что нужно удалить
            remaining_families = []
            removed_count = 0
            
            for family in all_families:
                mother_fio = family.get('mother_fio', '').strip().lower()
                father_fio = family.get('father_fio', '').strip().lower()
                
                # Проверяем, нужно ли удалять эту семью
                should_remove = mother_fio in families_to_remove_set or father_fio in families_to_remove_set
                
                # Также проверяем, что семья не была помечена как закрашенная (isPainted), чтобы избежать случайного удаления
                is_painted = family.get('isPainted', family.get('isColored', False))
                
                if not should_remove or is_painted:
                    remaining_families.append(family)
                else:
                    removed_count += 1

            # Сохраняем обновленный JSON обратно
            with open(self.last_json_path, 'w', encoding='utf-8') as f:
                json.dump(remaining_families, f, ensure_ascii=False, indent=2)

            self.log_message(f"🗑️ Удалено {removed_count} семей из исходного файла")
            
            # Обновляем внутренний список семей
            self.families_list = remaining_families
            self.update_families_table()
            self.update_families_info()

        except Exception as e:
            self.log_message(f"❌ Ошибка при удалении семей из исходного файла: {e}")
            import traceback
            self.log_message(f"📋 Трассировка:\n{traceback.format_exc()}")

    def log_message(self, message):
        """Логирование сообщений в текстовое поле"""
        try:
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            log_entry = f"{timestamp} {message}\n"
            
            # Проверяем, существует ли виджет перед обновлением
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                # Временно разрешаем редактирование
                self.log_text.config(state="normal")
                # Добавляем сообщение
                self.log_text.insert("end", log_entry)
                # Прокручиваем к последней строке
                self.log_text.see("end")
                # Возвращаем в состояние "только для чтения"
                self.log_text.config(state="disabled")
        except:
            # Если не удается обновить GUI, выводим в консоль
            print(f"[LOG] {message}")
    
    def run(self):
        """Запуск приложения"""
        self.app.mainloop()


class AutoFormFillerMass:

    def process_single_family_with_retry(self, family_data, family_number):
        """Обработка одной семьи с повторными попытками"""
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                self.gui.log_message(f"🔄 Попытка {attempt + 1} обработки семьи {family_number}")
                
                # При повторной попытке перезапускаем драйвер
                if attempt > 0:
                    if self.driver:
                        try:
                            self.driver.quit()
                        except Exception as e:
                            self.gui.log_message(f"⚠️ Ошибка при закрытии драйвера: {e}")
                        self.driver = None
                    
                    self.auto_filler = AutoFormFillerMass(self)
                    if not self.auto_filler._setup_driver():
                        self.gui.log_message("❌ Не удалось настроить драйвер")
                        continue
                    self.driver = self.auto_filler.driver
                elif not self.driver:
                    # Первая попытка, но драйвера нет
                    self.auto_filler = AutoFormFillerMass(self)
                    if not self.auto_filler._setup_driver():
                        self.gui.log_message("❌ Не удалось настроить драйвер")
                        continue
                    self.driver = self.auto_filler.driver
                else:
                    # Используем существующий драйвер
                    self.auto_filler = AutoFormFillerMass(self)
                    # Проверяем, что драйвер все еще активен
                    try:
                        # Проверяем, можно ли получить URL страницы
                        _ = self.driver.current_url
                        self.auto_filler.driver = self.driver
                        self.auto_filler.wait = WebDriverWait(self.driver, 10)
                    except:
                        # Драйвер больше не активен, нужно создать новый
                        self.gui.log_message("⚠️ Драйвер больше не активен, создаем новый")
                        if self.driver:
                            try:
                                self.driver.quit()
                            except Exception as e:
                                self.gui.log_message(f"⚠️ Ошибка при закрытии старого драйвера: {e}")
                        self.driver = None
                        
                        self.auto_filler = AutoFormFillerMass(self)
                        if not self.auto_filler._setup_driver():
                            self.gui.log_message("❌ Не удалось настроить драйвер")
                            continue
                        self.driver = self.auto_filler.driver
                
                # Устанавливаем путь для скриншотов
                if self.screenshot_var.get():
                    screenshot_dir = self.screenshot_dir.get().strip()
                    if not screenshot_dir:
                        screenshot_dir = self.screenshots_dir
                        
                    if not os.path.exists(screenshot_dir):
                        try:
                            os.makedirs(screenshot_dir)
                            self.gui.log_message(f"📁 Создана папка для скриншотов: {screenshot_dir}")
                        except Exception as e:
                            self.gui.log_message(f"⚠️ Не удалось создать папку для скриншотов: {e}")
                            screenshot_dir = None
                            
                    self.auto_filler.screenshot_dir = screenshot_dir
                    
                # Запускаем автоматизацию
                success = self.auto_filler.process_family(family_data, family_number)
                
                if success:
                    return True
                else:
                    self.gui.log_message(f"❌ Попытка {attempt + 1} не удалась")
                    if attempt < max_attempts - 1:
                        self.gui.log_message("🔄 Возвращаемся на страницу поиска для повторной попытки...")
                        # Возвращаемся на страницу поиска
                        try:
                            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
                            time.sleep(0.2)
                        except:
                            pass
                
            except Exception as e:
                self.gui.log_message(f"❌ Ошибка в process_single_family (попытка {attempt + 1}): {str(e)}")
                import traceback
                self.gui.log_message(f"📋 Трассировка:\n{traceback.format_exc()}")
                if attempt < max_attempts - 1:
                    self.gui.log_message("🔄 Пробуем еще раз...")
                    time.sleep(1)
        
        self.gui.log_message(f"❌ Обработка семьи {family_number} не удалась после {max_attempts} попыток")
        return False
    
    def pause_processing(self):
        """Пауза обработки"""
        if self.is_processing:
            self.is_processing = False
            self.log_message("⏸️ Обработка приостановлена")
            self.update_status("Приостановлено")
    
    def stop_processing(self):
        """Остановка обработки"""
        try:
            self.is_processing = False
            self.manual_intervention_required = False
            
            # Останавливаем автоматизацию
            if self.auto_filler:
                self.auto_filler.stop_processing()
                
            # Закрываем драйвер
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                    self.log_message("🔒 Драйвер закрыт")
                except Exception as e:
                    self.log_message(f"⚠️ Ошибка при закрытии драйвера: {e}")
                
            # Ждем завершения потока
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
                
            # Разблокируем кнопки
            self.start_button.configure(state="normal")
            self.continue_button.configure(state="disabled")
            
            self.log_message("🛑 Обработка остановлена")
            self.update_status("Остановлено")
            
        except Exception as e:
            self.log_message(f"⚠️ Ошибка при остановке: {e}")
    
    def _update_progress_and_status(self, current_index, total_count, success_count, error_count, skipped_count):
        """Обновление прогресса и статуса с детальной информацией"""
        # Обновляем прогресс
        progress_value = current_index / total_count
        self.gui.update_progress(progress_value)
        
        # Обновляем статус с детальной информацией
        status_text = f"Обработано: {current_index}/{total_count} | ✅: {success_count} | ❌: {error_count} | ⏭️: {skipped_count}"
        self.gui.update_status(status_text)
        
        # Проверяем, не остановлена ли обработка, чтобы избежать лишних обновлений UI
        if self.gui.is_processing:
            self.gui.update_families_table()

    def run(self):
        """Запуск приложения"""
        self.app.mainloop()


class AutoFormFillerMass:
    """Класс для массовой обработки семей с улучшенной обработкой ошибок"""
    
    def __init__(self, gui_app):
        self.gui = gui_app
        self.driver = None
        self.wait = None
        self.screenshot_dir = None
        self.should_stop = False
        self.phone = ""
        self.address = ""
        
    def log(self, message):
        """Логирование в GUI"""
        self.gui.log_message(message)
        
    def stop_processing(self):
        """Остановка обработки"""
        self.should_stop = True
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def wait_for_manual_intervention(self, message):
        """Ожидание ручного вмешательства пользователя"""
        self.log(f"🛠️ {message}")
        
        self.gui.manual_intervention_required = True

        # Показываем сообщение пользователю
        messagebox.showinfo("Требуется ручное вмешательство",
                           f"{message}\n\n"
                           "Пожалуйста, перейдите на нужную страницу в браузере и нажмете 'Продолжить' в программе.")
        
        # Ждем, пока пользователь не нажмет "Продолжить"
        while self.gui.manual_intervention_required and not self.should_stop:
            time.sleep(0.5)
        
        return not self.should_stop
        
    # Удаляем дублирующий метод, так как он уже существует в другом виде
    
    def process_family(self, family_data, family_number):
        """Обработка одной семьи"""
        try:
            # 1. Возвращаемся на страницу поиска
            self.log("🔙 Возвращаемся на страницу поиска...")
            try:
                self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
                time.sleep(0.2)  # Уменьшено с 0.5 до 0.2 секунды
            except Exception as e:
                self.log(f"❌ Не удалось загрузить страницу поиска: {e}")
                
                # Запрашиваем ручное вмешательство
                if self.wait_for_manual_intervention("Не удалось загрузить страницу поиска"):
                    self.log("▶️ Продолжаем после ручного вмешательства")
                    # Проверяем, что страница доступна после ручного вмешательства
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "ctl00_cph_ctrlFastFind_tbFind"))
                        )
                        self.log("✅ Страница поиска доступна после ручного вмешательства")
                    except:
                        self.log("❌ Страница поиска все еще недоступна после ручного вмешательства")
                        return False
                else:
                    return False
            
            # 2. Поиск семьи по ФИО матери
            mother_fio = family_data.get('mother_fio', '')
            father_fio = family_data.get('father_fio', '')
            
            # Если нет ФИО матери, используем ФИО отца для поиска
            search_fio = mother_fio if mother_fio else father_fio
            
            if not search_fio:
                self.log("❌ Не указано ФИО матери или отца")
                return False
                
            self.log(f"🔍 Поиск семьи: {search_fio}")
            
            # Выполняем поиск
            if not self._fast_search_mother(search_fio):
                self.log("❌ Не удалось найти семью")
                
                # Запрашиваем ручное вмешательство
                if self.wait_for_manual_intervention(f"Не удалось найти семью: {mother_fio}"):
                    self.log("▶️ Продолжаем после ручного вмешательства")
                    # Предполагаем, что пользователь уже на нужной странице
                else:
                    return False
            
            # 3. Анализ результатов поиска и автоматический выбор карточки
            self.log("🤖 Анализируем результаты поиска...")
            result = self._analyze_search_results(family_number, search_fio)
            
            if not result:
                self.log("❌ Не удалось автоматически выбрать карточку")
                
                # Запрашиваем ручное вмешательство
                if self.wait_for_manual_intervention("Не удалось автоматически выбрать карточку"):
                    self.log("▶️ Продолжаем после ручного вмешательства")
                    # Предполагаем, что пользователь уже на нужной карточке
                else:
                    return False
            
            # 4. ПЕРЕД ПЕРЕХОДОМ НА ДОПОЛНИТЕЛЬНУЮ ИНФОРМАЦИЮ - ПОЛУЧАЕМ ТЕЛЕФОН И АДРЕС
            # Ждем, пока страница карточки полностью загрузится
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: "CardInfo.aspx" in driver.current_url or "ПКУ" in driver.title or
                    driver.execute_script("return document.readyState") == "complete"
                )
                self.log("📱 Получаем телефон и адрес СРАЗУ ПОСЛЕ ПЕРЕХОДА НА КАРТОЧКУ...")
                
                # Получаем данные из family_data (из JSON)
                self._get_phone_and_address_from_family_data(family_data)
                
                # Также пытаемся получить со страницы (если не удалось из JSON)
                self._get_phone_and_address_from_page()
            except Exception as e:
                self.log(f"⚠️ Не удалось дождаться полной загрузки карточки или получить данные: {e}")
                # Возвращаемся на страницу поиска
                self._return_to_search_page()
                return False
            
            # 5. Проверка и заполнение данных
            if not self._check_additional_info_empty():
                if not self._warn_existing_data():
                    self.log("⚠️ Пропускаем - данные уже существуют")
                    # Возвращаемся на страницу поиска
                    self._return_to_search_page()
                    return True  # Возвращаем True, так как это не ошибка
                    
            # 6. Навигация к форме дополнительной информации
            self.log("🔄 Переходим на вкладку доп. информации...")
            if not self._navigate_to_additional_info():
                # Запрашиваем ручное вмешательство при ошибке навигации
                if self.wait_for_manual_intervention("Не удалось перейти на вкладку доп. информации"):
                    self.log("▶️ Продолжаем после ручного вмешательства")
                    # Предполагаем, что пользователь уже на нужной форме
                else:
                    return False
                
            # 7. Форматирование данных семьи (с доходами)
            formatted_data = self._format_family_data(family_data)
            
            # 8. Заполнение формы
            if not self._fill_form(*formatted_data):
                self.log("❌ Ошибка заполнения формы")
                return False
            
            # 9. Сохранение
            if self._final_verification(family_data):
                if self._save_and_exit():
                    # 10. Скриншот (делаем скриншот сразу после сохранения)
                    if self.screenshot_dir:
                        self._take_screenshot(formatted_data, family_number, family_data)

                    # 11. Возвращаемся на страницу поиска без закрытия браузера
                    time.sleep(0.2)
                    self._return_to_search_page()

                    self.log("✅ Семья обработана успешно")
                    return True
            return False
            
        except Exception as e:
            self.log(f"❌ Ошибка при обработке семьи: {str(e)}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _get_phone_and_address_from_family_data(self, family_data):
        """Получение телефона и адреса из данных семьи (JSON)"""
        try:
            # Телефон из данных
            phone_from_data = family_data.get('phone', '')
            if phone_from_data:
                self.phone = phone_from_data
                self.log(f"📱 Используем телефон из JSON данных: {self.phone}")
            else:
                self.log("⚠️ Телефон не найден в JSON данных")
                self.phone = ""
            
            # Адрес из данных
            address_from_data = family_data.get('address', '')
            if address_from_data:
                self.address = address_from_data
                self.log(f"🏠 Используем адрес из JSON данных: {self.address}")
            else:
                self.log("⚠️ Адрес не найден в JSON данных")
                self.address = ""
                
        except Exception as e:
            self.log(f"⚠️ Ошибка получения данных из JSON: {e}")
            self.phone = ""
            self.address = ""
    
    def _get_phone_and_address_from_page(self):
        """Дополнительная попытка получить телефон и адрес со страницы"""
        try:
            # Если телефон из JSON не получен, пытаемся со страницы
            if not self.phone:
                try:
                    # Ждем появления элемента телефона
                    phone_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "ctl00_cph_lblMobilPhone"))
                    )
                    phone_text = phone_element.text.strip() if phone_element else ""
                    if phone_text:
                        self.phone = phone_text
                        self.log(f"📱 Телефон со страницы: {self.phone}")
                except Exception as e:
                    self.log("⚠️ Телефон не найден на странице")
            
            # Если адрес из JSON не получен, пытаемся со страницы
            if not self.address or self.address == "Адрес не найден":
                try:
                    # Ждем появления элемента адреса
                    address_element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.ID, "ctl00_cph_lblRegAddress"))
                    )
                    address_text = address_element.text.strip() if address_element else ""
                    if address_text:
                        self.address = address_text
                        self.log(f"🏠 Адрес со страницы: {self.address}")
                        
                        # Спрашиваем пользователя, верен ли адрес
                        result = messagebox.askyesno(
                            "Проверка адреса", 
                            f"Адрес верен?\n{self.address}\n\nЕсли нет - отредактируйте в следующих шагах."
                        )
                        
                        if not result:
                            address_dialog = ctk.CTkInputDialog(
                                text=f"Введите правильный адрес:",
                                title="Исправление адреса"
                            )
                            new_address = address_dialog.get_input()
                            if new_address:
                                self.address = new_address
                except Exception as e:
                    self.log("⚠️ Адрес не найден на странице")
                    if not self.address:
                        self.address = "Адрес не найден"
                        
        except Exception as e:
            self.log(f"⚠️ Ошибка получения данных со страницы: {e}")
    
    def _return_to_search_page(self):
        """Возврат на страницу поиска без закрытия браузера"""
        try:
            self.log("🔄 Возвращаемся на страницу поиска...")
            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
            
            # Ждем полной загрузки страницы
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Дополнительно ждем появление элемента поиска и проверяем, что он доступен для ввода
            search_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "ctl00$cph$ctrlFastFind$tbFind"))
            )
            
            # Убедимся, что поле поиска пустое перед следующим использованием
            search_element.clear()
            
            # Дополнительно проверяем, что страница полностью загружена и готова к поиску
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_cph_dTabsContainer"))  # Убедимся, что контейнер результатов поиска присутствует
            )
            
            self.log("✅ Вернулись на страницу поиска")
        except Exception as e:
            self.log(f"⚠️ Не удалось вернуться на страницу поиска: {e}")
    
    def _analyze_search_results(self, family_number, mother_fio):
        """Анализ результатов поиска и автоматический выбор карточки"""
        try:
            # Добавляем дополнительное ожидание полной загрузки страницы результатов поиска
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Ждем появления контейнера с результатами поиска
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer"))
            )
            
            # Повторяем попытку нахождения карточек с несколькими попытками
            cards = None
            for attempt in range(3):
                try:
                    cards = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers"))
                    )
                    break
                except:
                    self.log(f"⚠️ Попытка {attempt + 1} нахождения карточек не удалась, ожидание и повтор...")
                    time.sleep(1)
                    continue
            
            if not cards:
                self.log("❌ Карточки не найдены")
                return False
                
            self.log(f"📊 Найдено карточек: {len(cards)}")
            
            # Убираем автоматический выбор первой карточки, если найдена только одна
            # Теперь будем искать карточки по приоритетам: "Вышневолоцкий городской округ" -> "Вышневолоцкий" -> "Вышний Волочек" -> выбор пользователем
            
            # Получаем свежий список карточек для анализа
            fresh_cards = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers")
            
            # Поиск по приоритетам
            vyishnevolotsk_ao_cards = []  # "Вышневолоцкий городской округ"
            vyishnevolotsk_cards = []     # "Вышневолоцкий"
            vyshniy_volochek_cards = []   # "Вышний Волочек"
            
            for i, card in enumerate(fresh_cards):
                try:
                    # Используем более надежный способ получения текста
                    fio = ""
                    try:
                        fio_element = card.find_element(By.CSS_SELECTOR, ".fio")
                        fio = fio_element.text if fio_element else ""
                    except:
                        # Альтернативный способ получения ФИО
                        try:
                            fio = card.text.split('\n')[0] if card.text else ""
                        except:
                            fio = f"Карточка {i+1}"
                    
                    address = ""
                    try:
                        details_table = card.find_element(By.CSS_SELECTOR, "table.tbl-details")
                        rows = details_table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2 and "Проживает:" in cells[0].text:
                                address = cells[1].text
                                break
                    except:
                        # Альтернативный способ получения адреса
                        address = card.text
                    
                    self.log(f"  Карточка {i+1}: {fio}")
                    self.log(f"    Адрес: {address[:50]}..." if len(address) > 50 else f"    Адрес: {address}")
                    
                    # Проверяем по приоритетам
                    address_lower = address.lower()
                    if "вышневолоцкий городской округ" in address_lower:
                        vyishnevolotsk_ao_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышневолоцкий городской округ")
                    elif "вышневолоцкий" in address_lower:
                        vyishnevolotsk_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышневолоцкий район")
                    elif "вышний волочек" in address_lower:
                        vyshniy_volochek_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышний Волочек")
                    elif "вышневолоцкий" in address_lower:
                        vyishnevolotsk_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышневолоцкий район (альтернативное написание)")
                    elif "вышнего волочка" in address_lower:
                        vyshniy_volochek_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышний Волочек (альтернативное написание)")
                        
                except Exception as e:
                    self.log(f"⚠️ Ошибка анализа карточки {i+1}: {e}")
                    continue
            
            # Проверяем карточки по приоритетам
            selected_cards = []
            priority_name = ""
            
            if vyishnevolotsk_ao_cards:
                selected_cards = vyishnevolotsk_ao_cards
                priority_name = "Вышневолоцкий городской округ"
                self.log(f"✅ Найдено {len(vyishnevolotsk_ao_cards)} карточек в {priority_name}")
            elif vyishnevolotsk_cards:
                selected_cards = vyishnevolotsk_cards
                priority_name = "Вышневолоцкий район"
                self.log(f"✅ Найдено {len(vyishnevolotsk_cards)} карточек в {priority_name}")
            elif vyshniy_volochek_cards:
                selected_cards = vyshniy_volochek_cards
                priority_name = "Вышний Волочек"
                self.log(f"✅ Найдено {len(vyshniy_volochek_cards)} карточек в {priority_name}")
            else:
                self.log("❌ Не найдено карточек в указанных районах (Вышневолоцкий городской округ, Вышневолоцкий район, Вышний Волочек)")
                # Получаем свежий список карточек для передачи в выбор
                fresh_cards_for_selection = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers")
                return self._show_cards_for_selection(fresh_cards_for_selection, family_number, mother_fio)
                
            # Обработка выбранного приоритета
            if len(selected_cards) == 1:
                self.log(f"✅ Найдена 1 карточка в {priority_name}")
                try:
                    # Используем свежую карточку из selected_cards
                    card = selected_cards[0]['card']
                    # Ищем ссылку с атрибутом title='Переход в просмотр ПКУ' с обработкой stale элементов
                    try:
                        links = card.find_elements(By.CSS_SELECTOR, "a[title='Переход в просмотр ПКУ']")
                    except Exception as e:
                        if "stale element reference" in str(e).lower():
                            # Получаем свежий список карточек и пробуем снова
                            fresh_cards = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers")
                            if len(fresh_cards) > selected_cards[0]['index']:
                                card = fresh_cards[selected_cards[0]['index']]
                                links = card.find_elements(By.CSS_SELECTOR, "a[title='Переход в просмотр ПКУ']")
                            else:
                                self.log("❌ Не удалось получить свежий список карточек")
                                return False
                        else:
                            raise e
                    
                    if len(links) > 0:
                        link = links[0]
                        # Получаем ID ссылки для использования в случае stale element reference
                        link_id = link.get_attribute("id")
                        
                        if link_id:
                            # Используем ID для получения свежего элемента перед кликом
                            try:
                                fresh_link = WebDriverWait(self.driver, 10).until(
                                    EC.element_to_be_clickable((By.ID, link_id))
                                )
                                # Прокручиваем к элементу перед кликом
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", fresh_link)
                                time.sleep(0.5)  # Небольшая задержка для завершения прокрутки
                                
                                # Используем JavaScript для клика, чтобы избежать stale element reference
                                try:
                                    self.driver.execute_script("arguments[0].click();", fresh_link)
                                except:
                                    # Если JavaScript клик не работает, используем обычный клик
                                    fresh_link.click()
                            except:
                                # Если не удается найти элемент по ID, используем JavaScript напрямую
                                link_script = f"document.querySelector('a[title=\"Переход в просмотр ПКУ\"][id=\"{link_id}\"]')"
                                try:
                                    self.driver.execute_script(f"({link_script}).click();")
                                except Exception as js_error:
                                    self.log(f"❌ Не удалось кликнуть через JavaScript по ID: {js_error}")
                                    # Попробуем универсальный селектор
                                    try:
                                        self.driver.execute_script("document.querySelector('a[title=\"Переход в просмотр ПКУ\"]').click();")
                                    except Exception as universal_error:
                                        self.log(f"❌ Не удалось кликнуть через универсальный селектор: {universal_error}")
                                        return False
                        else:
                            # Если у ссылки нет ID, используем общий селектор
                            try:
                                # Прокручиваем к элементу перед кликом
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", link)
                                time.sleep(0.5)  # Небольшая задержка для завершения прокрутки
                                
                                # Используем JavaScript для клика, чтобы избежать stale element reference
                                try:
                                    self.driver.execute_script("arguments[0].click();", link)
                                except:
                                    # Если JavaScript клик не работает, используем обычный клик
                                    link.click()
                            except Exception as click_error:
                                self.log(f"❌ Не удалось кликнуть на ссылку: {click_error}")
                                return False
                        
                        return True
                    else:
                        self.log("❌ Не удалось найти ссылку для перехода к карточке")
                        return False
                except Exception as e:
                    self.log(f"❌ Не удалось кликнуть на ссылку: {e}")
                    import traceback
                    self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
                    return False
                    
            else:
                self.log(f"⚠️ Найдено {len(selected_cards)} карточек в {priority_name}")
                # Передаем свежие карточки в метод выбора
                fresh_cards_for_selection = [info['card'] for info in selected_cards]
                return self._show_cards_for_selection(
                    fresh_cards_for_selection,
                    family_number,
                    mother_fio,
                    filtered=True
                )
                
        except Exception as e:
            self.log(f"❌ Ошибка анализа результатов поиска: {e}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _show_cards_for_selection(self, cards, family_number, mother_fio, filtered=False):
        """Показ карточек пользователю для выбора"""
        try:
            card_info_list = []
            
            # Получаем свежие карточки для отображения информации
            for i, card in enumerate(cards):
                try:
                    fio_element = card.find_element(By.CSS_SELECTOR, ".fio")
                    fio = fio_element.text if fio_element else f"Карточка {i+1}"
                    
                    address = ""
                    try:
                        details_table = card.find_element(By.CSS_SELECTOR, "table.tbl-details")
                        rows = details_table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2 and "Проживает:" in cells[0].text:
                                address = cells[1].text
                                break
                    except:
                        pass
                    
                    # Определяем приоритет района для отображения
                    address_lower = address.lower()
                    priority = ""
                    if "вышневолоцкий городской округ" in address_lower:
                        priority = " (Вышневолоцкий ГО)"
                    elif "вышневолоцкий" in address_lower:
                        priority = " (Вышневолоцкий)"
                    elif "вышний волочек" in address_lower:
                        priority = " (Вышний Волочек)"
                    
                    card_info_list.append({
                        'index': i,
                        'fio': fio,
                        'address': address[:100] + "..." if len(address) > 100 else address,
                        'priority': priority
                    })
                except:
                    card_info_list.append({
                        'index': i,
                        'fio': f"Карточка {i+1}",
                        'address': "Информация недоступна",
                        'priority': ""
                    })
            
            dialog_text = f"Семья {family_number}: {mother_fio}\n\n"
            
            if filtered:
                dialog_text += "Найдено несколько карточек в приоритетных районах (Вышневолоцкий городской округ -> Вышневолоцкий -> Вышний Волочек):\n\n"
            else:
                dialog_text += "Найдено несколько карточек. Выберите нужную:\n\n"
            
            for i, info in enumerate(card_info_list):
                dialog_text += f"{i+1}. {info['fio']}{info.get('priority', '')}\n"
                dialog_text += f"   Адрес: {info['address']}\n\n"
            
            dialog_text += "Введите номер карточки (1, 2, 3...):"
            
            choice_dialog = ctk.CTkInputDialog(
                text=dialog_text,
                title="Выбор карточки"
            )
            
            choice = choice_dialog.get_input()
            
            if not choice:
                self.log("❌ Пользователь не сделал выбор")
                return False
                
            try:
                choice_num = int(choice) - 1
                if 0 <= choice_num < len(cards):
                    # Вместо использования старой карточки, находим свежую по индексу
                    fresh_cards = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers")
                    if choice_num < len(fresh_cards):
                        selected_card = fresh_cards[choice_num]
                        # Ищем ссылку с атрибутом title='Переход в просмотр ПКУ'
                        links = selected_card.find_elements(By.CSS_SELECTOR, "a[title='Переход в просмотр ПКУ']")
                        if len(links) > 0:
                            link = links[0]
                            # Получаем ID ссылки для использования в случае stale element reference
                            link_id = link.get_attribute("id")
                            
                            if link_id:
                                # Используем ID для получения свежего элемента перед кликом
                                try:
                                    fresh_link = WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable((By.ID, link_id))
                                    )
                                    # Прокручиваем к элементу перед кликом
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", fresh_link)
                                    time.sleep(0.5)  # Небольшая задержка для завершения прокрутки
                                    
                                    # Используем JavaScript для клика, чтобы избежать stale element reference
                                    try:
                                        self.driver.execute_script("arguments[0].click();", fresh_link)
                                    except:
                                        # Если JavaScript клик не работает, используем обычный клик
                                        fresh_link.click()
                                except:
                                    # Если не удается найти элемент по ID, используем JavaScript напрямую
                                    link_script = f"document.querySelector('a[title=\"Переход в просмотр ПКУ\"][id=\"{link_id}\"]')"
                                    try:
                                        self.driver.execute_script(f"({link_script}).click();")
                                    except Exception as js_error:
                                        self.log(f"❌ Не удалось кликнуть через JavaScript по ID: {js_error}")
                                        # Попробуем универсальный селектор
                                        try:
                                            self.driver.execute_script("document.querySelector('a[title=\"Переход в просмотр ПКУ\"]').click();")
                                        except Exception as universal_error:
                                            self.log(f"❌ Не удалось кликнуть через универсальный селектор: {universal_error}")
                                            return False
                            else:
                                # Если у ссылки нет ID, используем общий селектор
                                try:
                                    # Прокручиваем к элементу перед кликом
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", link)
                                    time.sleep(0.5)  # Небольшая задержка для завершения прокрутки
                                    
                                    # Используем JavaScript для клика, чтобы избежать stale element reference
                                    try:
                                        self.driver.execute_script("arguments[0].click();", link)
                                    except:
                                        # Если JavaScript клик не работает, используем обычный клик
                                        link.click()
                                except Exception as click_error:
                                    self.log(f"❌ Не удалось кликнуть на ссылку: {click_error}")
                                    return False
                            
                            time.sleep(0.8)  # Уменьшено с 2 до 0.8 секунды
                            self.log(f"✅ Выбрана карточка {choice_num + 1}")
                            return True
                        else:
                            self.log(f"❌ Не удалось найти ссылку для карточки {choice_num + 1}")
                            return False
                    else:
                        self.log(f"❌ Карточка с индексом {choice_num} не найдена в свежем списке")
                        return False
                else:
                    self.log(f"❌ Некорректный номер карточки: {choice}")
                    return False
            except ValueError:
                self.log(f"❌ Некорректный ввод: {choice}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка при выборе карточки: {e}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _setup_driver(self):
        """Настройка драйвера"""
        try:
            self.log("🔧 Настройка драйвера...")
            
            # Импортируем chrome_driver_helper
            from chrome_driver_helper import setup_chrome_driver
            
            # Используем улучшенный метод настройки ChromeDriver
            self.driver = setup_chrome_driver()
            if self.driver is None:
                self.log("❌ Не удалось настроить ChromeDriver")
                messagebox.showerror("Ошибка", "Не удалось настроить ChromeDriver")
                return False
            
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.maximize_window()
            
            if not self._login():
                return False
                
            self.log("✅ Драйвер настроен и выполнен вход")
            return True
            
        except ImportError:
            # Если не удается импортировать chrome_driver_helper, используем старую логику
            self.log("⚠️ chrome_driver_helper не найден, используем старую логику...")
            return self._setup_driver_legacy()
        except Exception as e:
            self.log(f"❌ Ошибка настройки драйвера: {e}")
            return False
    
    def _setup_driver_legacy(self):
        """Старая логика настройки драйвера (резервный вариант)"""
        try:
            self.log("🔧 Настройка драйвера (старый метод)...")
            
            browser = self._detect_browser()
            if not browser:
                self.log("❌ Не найден Chrome, Yandex или Chromium")
                messagebox.showerror("Ошибка", "Не найден браузер Chrome, Yandex или Chromium")
                return False
                
            try:
                driver_path = ChromeDriverManager(chrome_type=browser['type']).install()
            except Exception as e:
                self.log(f"❌ Не удалось установить драйвер: {e}")
                messagebox.showerror("Ошибка", f"Не удалось установить драйвер браузера: {e}")
                return False
                
            service = webdriver.chrome.service.Service(driver_path)
            
            options = webdriver.ChromeOptions()
            if platform.system().lower() in ["linux", "redos"]:
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
            
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--start-maximized')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            try:
                self.driver = webdriver.Chrome(service=service, options=options)
                self.wait = WebDriverWait(self.driver, 10)
                
                self.driver.maximize_window()
                
                if not self._login():
                    return False
                    
                self.log("✅ Драйвер настроен и выполнен вход")
                return True
                
            except Exception as e:
                self.log(f"❌ Не удалось запустить драйвер: {e}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка настройки драйвера: {e}")
            return False
    
    def _detect_browser(self):
        """Определение доступного браузера"""
        system = platform.system().lower()
        
        if system == "windows":
            try:
                import winreg
                browsers = [
                    (r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe', 'Chrome', ChromeType.GOOGLE),
                    #(r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\browser.exe', 'Yandex', ChromeType.YANDEX),
                ]
                
                for path, name, btype in browsers:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                            browser_path = winreg.QueryValue(key, None)
                            if os.path.exists(browser_path):
                                self.log(f"✅ Найден браузер: {name}")
                                return {'name': name, 'type': btype}
                    except Exception:
                        continue
                        
            except ImportError:
                self.log("⚠️ Модуль winreg недоступен, пробуем стандартный Chrome")
                return {'name': 'Chrome', 'type': ChromeType.GOOGLE}
                
        elif system in ["linux", "redos"]:
            for path in ['/usr/bin/chromium-browser', '/usr/bin/chromium', '/usr/bin/google-chrome']:
                if os.path.exists(path):
                    self.log(f"✅ Найден браузер: {os.path.basename(path)}")
                    return {'name': 'Chromium', 'type': ChromeType.CHROMIUM}
        
        self.log("⚠️ Браузер не найден, пробуем Chrome")
        return {'name': 'Chrome', 'type': ChromeType.GOOGLE}
    
    def _login(self):
        """Вход в систему"""
        try:
            self.log("🔐 Выполняем вход...")
            
            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
            time.sleep(1)
            
            username_field = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "tbUserName"))
            )
            username_field.clear()
            username_field.send_keys("СРЦ_Вол")
            
            password_field = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "tbPassword"))
            )
            password_field.clear()
            password_field.send_keys("СРЦ_Вол1", Keys.ENTER)
            
            time.sleep(1)
            self.log("✅ Вход выполнен")
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка входа: {e}")
            messagebox.showerror("Ошибка входа", f"Не удалось выполнить вход: {e}")
            return False
    
    def _fast_search_mother(self, mother_fio):
        """Быстрый поиск по ФИО матери"""
        max_attempts = 3  # Увеличиваем число попыток
        for attempt in range(max_attempts):
            try:
                # Ждем, что поле поиска будет доступно и пустое
                search_field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "ctl00$cph$ctrlFastFind$tbFind"))
                )
                
                # Получаем атрибуты элемента перед возможной устаревшей ссылкой
                search_field_id = search_field.get_attribute("id")
                search_field_name = search_field.get_attribute("name")
                
                # Очищаем поле и вводим новое значение
                search_field.clear()
                time.sleep(0.2)  # Небольшая задержка для завершения очистки
                search_field.send_keys(mother_fio)
                search_field.send_keys(Keys.ENTER)
                
                # Ждем появления результатов поиска
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers"))
                )
                
                self.log(f"✅ Поиск выполнен успешно (попытка {attempt + 1})")
                return True
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"⚠️ Попытка {attempt + 1} поиска не удалась: {e}")
                    # Если возникла ошибка stale element reference, пробуем использовать JavaScript
                    if "stale element reference" in str(e).lower():
                        try:
                            # Используем JavaScript для ввода данных в поле поиска
                            js_script = f"""
                            var searchField = document.querySelector('[name="ctl00$cph$ctrlFastFind$tbFind"]');
                            if (searchField) {{
                                searchField.value = '{mother_fio}';
                                searchField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                searchField.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                                return true;
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                # Ждем появления результатов поиска
                                WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers"))
                                )
                                self.log(f"✅ Поиск выполнен успешно через JavaScript (попытка {attempt + 1})")
                                return True
                        except Exception as js_error:
                            self.log(f"⚠️ Не удалось выполнить поиск через JavaScript: {js_error}")
                    
                    # Дополнительно убедимся, что мы на странице поиска
                    try:
                        self.driver.refresh()
                        time.sleep(1)
                        # Повторно дожидаемся загрузки страницы
                        WebDriverWait(self.driver, 10).until(
                            lambda driver: driver.execute_script("return document.readyState") == "complete"
                        )
                    except:
                        pass
                    time.sleep(0.5)
                else:
                    self.log(f"❌ Ошибка поиска после {max_attempts} попыток: {e}")
                    return False
        return False
    
    def _check_additional_info_empty(self):
        """Проверка пустого поля дополнительной информации"""
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                if not self._click_element_with_retry(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL", max_attempts=2):
                    self.log(f"⚠️ Не удалось кликнуть вкладку дополнительной информации, попытка {attempt + 1}")
                    if attempt < max_attempts - 1:
                        # Возвращаемся на страницу поиска и снова ищем семью
                        self._return_to_search_page()
                        # Здесь потребуется повторный поиск семьи, что может быть сложно
                        # Поэтому просто продолжаем попытки клика
                        time.sleep(1)
                        continue
                    else:
                        return False
                        
                # Ждем появления элемента с информацией
                try:
                    info_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, "ctl00_cph_lblAddInfo2"))
                    )
                    info_text = info_element.text.strip()
                except:
                    # Если элемент не найден, проверяем наличие других элементов
                    info_text = ""
                
                result = info_text == "Информация отсутствует" or not info_text
                self.log(f"📊 Проверка дополнительной информации: {'пусто' if result else 'есть данные'}")
                return result
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"⚠️ Попытка {attempt + 1} проверки поля не удалась: {e}")
                    time.sleep(0.5)
                else:
                    self.log(f"⚠️ Ошибка проверки поля: {e}")
                    return True
        return True
    
    def _warn_existing_data(self):
        """Предупреждение о существующих данных"""
        return messagebox.askyesno("Предупреждение", 
                                 "В разделе уже есть данные! Они будут УДАЛЕНЫ.\nПродолжить?")
                                 
    def _navigate_to_additional_info(self):
        """Навигация к форме дополнительной информации"""
        try:
            # Клик по вкладке "Доп. информация"
            self.log("🔄 Переход на вкладку дополнительной информации...")
            
            # Проверяем, что мы действительно на странице карточки перед переходом к доп. информации
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: "CardInfo.aspx" in driver.current_url or "ПКУ" in driver.title
                )
            except:
                self.log("⚠️ Мы не на странице карточки семьи")
                return False
            
            if not self._click_element_with_retry(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL"):
                self.log("❌ Не удалось кликнуть вкладку дополнительной информации")
                return False
            
            # Небольшая задержка для загрузки вкладки
            time.sleep(0.5)
            
            # Ожидаем появление кнопки редактирования с дополнительной проверкой
            try:
                edit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_cph_lbtnEditAddInfo"))
                )
                self.log("✅ Кнопка редактирования найдена")
            except:
                self.log("❌ Кнопка редактирования не найдена")
                return False
                
            if not self._click_element_with_retry(By.ID, "ctl00_cph_lbtnEditAddInfo"):
                self.log("❌ Не удалось кликнуть кнопку редактирования")
                return False
            
            # Небольшая задержка после клика по кнопке редактирования
            time.sleep(0.5)
            
            # Ожидаем появление кнопки добавления с дополнительной проверкой
            try:
                add_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_cph_ctrlDopFields_lbtnAdd"))
                )
                self.log("✅ Кнопка добавления найдена")
            except:
                self.log("❌ Кнопка добавления не найдена")
                return False
                
            if not self._click_element_with_retry(By.ID, "ctl00_cph_ctrlDopFields_lbtnAdd"):
                self.log("❌ Не удалось кликнуть кнопку добавления")
                return False
            
            # Небольшая задержка после клика по кнопке добавления
            time.sleep(1)
            
            # Ждем загрузки формы с дополнительной проверкой
            try:
                form_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "ctl00$cph$tbAddInfo"))
                )
                self.log("✅ Форма дополнительной информации загружена")
            except:
                self.log("❌ Форма дополнительной информации не загружена")
                return False
                
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка навигации: {e}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _format_family_data(self, family_data):
        """Форматирование данных семьи с доходами"""
        try:
            lines = []
            
            # Мать
            mother_line = f"Мать: {family_data.get('mother_fio', '')} {family_data.get('mother_birth', '')}"
            lines.extend([mother_line, f"Работает: {family_data.get('mother_work', '')}"])
            
            # Отец
            if family_data.get('father_fio'):
                lines.extend([
                    f"Отец: {family_data['father_fio']} {family_data.get('father_birth', '')}",
                    f"Работает: {family_data.get('father_work', '')}"
                ])
            
            # Дети
            if family_data.get('children'):
                lines.append("Дети:")
                for child in family_data['children']:
                    edu = f" - {child.get('education', '')}" if child.get('education') else ""
                    lines.append(f"    {child.get('fio', '')} {child.get('birth', '')}{edu}")
            
            # Доходы - ВКЛЮЧАЕМ ДОХОДЫ ИЗ JSON
            incomes = family_data.get('incomes', {})
            if incomes:
                lines.append("\nДоходы семьи:")
                income_labels = {
                    'mother_salary': 'Зарплата матери',
                    'father_salary': 'Зарплата отца', 
                    'unified_benefit': 'Единое пособие',
                    'large_family_benefit': 'Пособие по многодетности',
                    'survivor_pension': 'Пенсия по потере кормильца',
                    'alimony': 'Алименты',
                    'disability_pension': 'Пенсия по инвалидности'
                }
                
                for key, value in incomes.items():
                    if key in income_labels and value:
                        try:
                            clean_value = ''.join(filter(str.isdigit, str(value)))
                            if clean_value:
                                float_value = float(clean_value)
                                formatted_value = f"{float_value:,.0f} руб.".replace(",", " ")
                            else:
                                formatted_value = value
                        except:
                            formatted_value = value
                        lines.append(f"{income_labels[key]}: {formatted_value}")
                
                try:
                    total_income = 0
                    for value in incomes.values():
                        clean_value = ''.join(filter(str.isdigit, str(value)))
                        if clean_value:
                            total_income += float(clean_value)
                    if total_income > 0:
                        lines.append(f"\nОбщий доход: {total_income:,.0f} руб.".replace(",", " "))
                except:
                    pass
            
            # Категория семьи
            category = "полная, многодетная" if family_data.get('father_fio') else "неполная, многодетная"
            
            add_info_text = "\n".join(lines)
            
            # Жилищные условия - ВКЛЮЧАЕМ СОБСТВЕННОСТЬ
            rooms = family_data.get('rooms', '')
            square = family_data.get('square', '')
            amenities = family_data.get('amenities', 'со всеми удобствами')
            ownership = family_data.get('ownership', '')
            
            housing_parts = []
            if rooms:
                housing_parts.append(f"{rooms} комнат")
            if square:
                housing_parts.append(f"{square} кв.м.")
            if amenities:
                housing_parts.append(f"{amenities}")
            if ownership:
                housing_parts.append(f"{ownership}")
            
            housing_info = ", ".join(housing_parts)
            
            adpi_data = {
                'has_adpi': 'д' if family_data.get('adpi') == 'да' else 'н',
                'install_date': family_data.get('install_date'),
                'check_date': family_data.get('check_date')
            }
            
            return add_info_text, category, housing_info, adpi_data
            
        except Exception as e:
            self.log(f"❌ Ошибка форматирования данных: {e}")
            return "", "", "", {'has_adpi': 'н', 'install_date': '', 'check_date': ''}
    
    def _fill_form(self, add_info_text, category, housing_info, adpi_data):
        """Заполнение формы с динамическим определением индексов"""
        try:
            # Определяем, есть ли АДПИ
            has_adpi = adpi_data['has_adpi'] == 'д'
            
            # Отмечаем чекбоксы
            checkbox_ids = [8, 12, 13, 14, 17, 18]
            if has_adpi:
                checkbox_ids.extend([15, 16])
            
            self.log(f"🔄 Отмечаем чекбоксы: {checkbox_ids}")
            
            # Проверяем каждый чекбокс перед установкой
            for checkbox_id in checkbox_ids:
                try:
                    checkbox_element_id = f"ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_{checkbox_id}"
                    checkbox = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, checkbox_element_id))
                    )
                    
                    # Прокручиваем к чекбоксу
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", checkbox)
                    time.sleep(0.2)
                    
                    # Проверяем, установлен ли чекбокс уже
                    is_selected = checkbox.is_selected()
                    if not is_selected:
                        # Попробуем кликнуть напрямую
                        try:
                            checkbox.click()
                            time.sleep(0.1)  # Небольшая задержка для обновления состояния
                        except:
                            # Если клик не удался, используем JavaScript
                            try:
                                self.driver.execute_script("arguments[0].click();", checkbox)
                            except:
                                self.log(f"⚠️ Не удалось отметить чекбокс {checkbox_id} через клик")
                                continue
                        
                        # Проверяем, что чекбокс действительно установлен
                        is_selected_after = checkbox.is_selected()
                        if is_selected_after:
                            self.log(f"✅ Чекбокс {checkbox_id} отмечен")
                        else:
                            self.log(f"⚠️ Не удалось отметить чекбокс {checkbox_id}")
                    else:
                        self.log(f"ℹ️ Чекбокс {checkbox_id} уже отмечен")
                except Exception as e:
                    self.log(f"⚠️ Не удалось отметить чекбокс {checkbox_id}: {e}")
                    
            # Альтернативный метод через JavaScript для уверенности
            js_script = """
            var ids = arguments[0];
            for (var i = 0; i < ids.length; i++) {
                var checkboxId = 'ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_' + ids[i];
                var checkbox = document.getElementById(checkboxId);
                if (checkbox && !checkbox.checked) {
                    checkbox.checked = true;
                    checkbox.dispatchEvent(new Event('click', { bubbles: true }));
                }
            }
            """
            
            try:
                self.driver.execute_script(js_script, checkbox_ids)
                self.log("✅ Чекбоксы дополнительно обработаны через JavaScript")
            except Exception as e:
                self.log(f"⚠️ Не удалось обработать чекбоксы через JavaScript: {e}")
            
            # Клик по кнопке подтверждения чекбоксов с улучшенной обработкой
            ok_button_id = "ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_ctl06_AJOk"
            if not self._click_element_with_retry(By.ID, ok_button_id):
                self.log("⚠️ Не удалось кликнуть кнопку подтверждения чекбоксов")
                # Попробуем альтернативный способ
                try:
                    ok_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, ok_button_id))
                    )
                    self.driver.execute_script("arguments[0].click();", ok_button)
                    self.log("✅ Кнопка подтверждения чекбоксов нажата через JavaScript")
                except:
                    self.log("❌ Не удалось нажать кнопку подтверждения чекбоксов")
                    return False
                
            # Заполняем основное текстовое поле
            if not self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True):
                self.log("⚠️ Не удалось заполнить текстовую область")
                self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True)
            
            # Заполняем АДПИ радио-кнопку
            self.log("🔄 Заполняем данные АДПИ...")
            if not self._fill_adpi_radio_button(adpi_data):
                self.log("⚠️ Не удалось заполнить АДПИ")
            
            # Динамически определяем индексы полей
            field_indices = self._get_field_indices()
            
            if not field_indices:
                self.log("❌ Не удалось определить индексы полей")
                return False
            
            # Заполняем поля по найденным индексам
            if 'phone' in field_indices:
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["phone"]}$tb',
                    self.phone or ''
                ):
                    self.log("⚠️ Не удалось заполнить телефон")
            else:
                self.log("⚠️ Поле телефона не найдено в таблице")
            
            if 'category' in field_indices:
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["category"]}$tb',
                    category
                ):
                    self.log("⚠️ Не удалось заполнить категорию семьи")
            else:
                self.log("⚠️ Поле категории семьи не найдено в таблице")
            
            if 'address' in field_indices:
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["address"]}$tb',
                    self.address
                ):
                    self.log("⚠️ Не удалось заполнить адрес")
            else:
                self.log("⚠️ Поле адреса не найдено в таблице")
            
            if 'housing' in field_indices:
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["housing"]}$tb',
                    housing_info
                ):
                    self.log("⚠️ Не удалось заполнить жилищные условия")
            else:
                self.log("⚠️ Поле жилищных условий не найдено в таблице")
            
            if 'living' in field_indices:
                living_conditions_text = "Санитарные условия удовлетворительные, для детей имеется отдельное спальное место, место для занятий и отдыха. Продукты питания в достаточном количестве."
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["living"]}$tb',
                    living_conditions_text
                ):
                    self.log("⚠️ Не удалось заполнить бытовые условия")
            else:
                self.log("⚠️ Поле бытовых условий не найдено в таблице")
            
            # Заполняем даты АДПИ если есть
            if has_adpi:
                self._fill_adpi_dates_with_indices(adpi_data, field_indices)
                
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка заполнения формы: {e}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _get_field_indices(self):
        """Динамическое определение индексов полей по их названиям"""
        field_indices = {}
        
        try:
            # Ждем загрузки таблицы
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_cph_ctrlDopFields_gv"))
            )
            
            # Прокручиваем немного вниз, чтобы таблица была видна
            self.driver.execute_script("window.scrollBy(0, 300);")
            # Убрали задержку, так как используем ожидание элементов
            
            # Пробуем найти все строки с полями
            rows = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_ctrlDopFields_gv tr:not(:first-child)")
            
            if not rows:
                self.log("⚠️ Не найдены строки в таблице, использую стандартные индексы")
                return self._get_fallback_indices()
            
            self.log(f"📊 Найдено строк в таблице: {len(rows)}")
            
            # Проходим по всем строкам и ищем нужные поля
            for i, row in enumerate(rows, start=2):  # начинаем с 2
                try:
                    # Формируем индекс для поиска элемента
                    index_str = f"{i:02d}"
                    
                    # Пробуем найти элемент с названием поля
                    try:
                        field_name_elem = row.find_element(By.ID, f"ctl00_cph_ctrlDopFields_gv_ctl{index_str}_lbName")
                        field_name = field_name_elem.text.strip()
                        
                        self.log(f"  Строка {index_str}: {field_name}")
                        
                        # Сопоставляем название поля с нашими ключами
                        if "Номер телефона" in field_name:
                            field_indices['phone'] = index_str
                        elif "Категория семьи" in field_name:
                            field_indices['category'] = index_str
                        elif "Фактический адрес проживания семьи" in field_name or "адрес" in field_name.lower():
                            field_indices['address'] = index_str
                        elif "Жилищные условия" in field_name or "жилищ" in field_name.lower():
                            field_indices['housing'] = index_str
                        elif "Бытовые условия" in field_name or "бытов" in field_name.lower():
                            field_indices['living'] = index_str
                        elif "Дата установки АДПИ" in field_name or "установки" in field_name.lower():
                            field_indices['install_date'] = index_str
                        elif "Дата последней проверки АДПИ" in field_name or "проверки" in field_name.lower():
                            field_indices['check_date'] = index_str
                        
                    except:
                        # Пробуем альтернативный способ поиска
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                field_name = cells[1].text.strip()
                                if field_name:
                                    self.log(f"  Строка {index_str}: {field_name}")
                                    
                                    if "Номер телефона" in field_name:
                                        field_indices['phone'] = index_str
                                    elif "Категория семьи" in field_name:
                                        field_indices['category'] = index_str
                                    elif "Фактический адрес проживания семьи" in field_name or "адрес" in field_name.lower():
                                        field_indices['address'] = index_str
                                    elif "Жилищные условия" in field_name or "жилищ" in field_name.lower():
                                        field_indices['housing'] = index_str
                                    elif "Бытовые условия" in field_name or "бытов" in field_name.lower():
                                        field_indices['living'] = index_str
                                    elif "Дата установки АДПИ" in field_name or "установки" in field_name.lower():
                                        field_indices['install_date'] = index_str
                                    elif "Дата последней проверки АДПИ" in field_name or "проверки" in field_name.lower():
                                        field_indices['check_date'] = index_str
                        except:
                            continue
                            
                except Exception as e:
                    self.log(f"    ⚠️ Ошибка анализа строки {i}: {e}")
                    continue
            
            self.log(f"✅ Определены индексы полей: {field_indices}")
            
            # Если не нашли все нужные поля, используем запасной вариант
            required_fields = ['phone', 'category', 'address', 'housing', 'living']
            missing_fields = [field for field in required_fields if field not in field_indices]
            
            if missing_fields:
                self.log(f"⚠️ Не найдены поля: {missing_fields}, использую стандартные индексы")
                fallback_indices = self._get_fallback_indices()
                # Объединяем найденные индексы со стандартными
                for field in missing_fields:
                    if field in fallback_indices:
                        field_indices[field] = fallback_indices[field]
            
            return field_indices
            
        except Exception as e:
            self.log(f"❌ Ошибка определения индексов полей: {e}")
            return self._get_fallback_indices()
    
    def _get_fallback_indices(self):
        """Запасной вариант определения индексов"""
        # Проверяем, есть ли АДПИ (ищем радио-кнопку "Да" для АДПИ)
        try:
            adpi_yes = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0"))
            )
            has_adpi = True
        except:
            has_adpi = False
        
        if has_adpi:
            return {
                'phone': '02',
                'category': '06',
                'address': '07',
                'housing': '08',
                'living': '09',
                'install_date': '04',
                'check_date': '05'
            }
        else:
            return {
                'phone': '02',
                'category': '04',
                'address': '05',
                'housing': '06',
                'living': '07'
            }
    
    def _fill_field_with_retry(self, by, selector, text, max_attempts=3):
        """Улучшенный метод заполнения поля с повторными попытками"""
        for attempt in range(max_attempts):
            try:
                self.log(f"🔄 Попытка {attempt + 1} заполнения поля {selector}")
                
                # Ждем и получаем элемент заново каждый раз
                field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((by, selector))
                )
                
                # Прокручиваем к элементу
                self.driver.execute_script("arguments[0].scrollIntoView(true);", field)
                # Убрали задержку, т.к. используем ожидания
                
                # Получаем атрибуты элемента перед возможной устаревшей ссылкой
                field_id = field.get_attribute("id")
                field_name = field.get_attribute("name")
                
                # Очищаем поле
                field.clear()
                # Убрали задержку
                
                # Вводим текст
                if text:
                    field.send_keys(text)
                    # Убрали задержку
                    
                    # Проверяем, что текст введен
                    try:
                        value = field.get_attribute('value')
                        if value and value.strip():
                            self.log(f"✅ Заполнено поле: {selector}")
                            return True
                    except:
                        # Для textarea проверяем свойство value
                        try:
                            value = field.get_property('value')
                            if value and value.strip():
                                self.log(f"✅ Заполнено поле: {selector}")
                                return True
                        except:
                            # Если не удалось проверить, считаем успешным
                            self.log(f"✅ Заполнено поле: {selector} (не удалось проверить)")
                            return True
            
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"⚠️ Попытка {attempt + 1} заполнения поля {selector} не удалась: {e}")
                    # Если возникла ошибка stale element reference, пробуем использовать JavaScript
                    if "stale element reference" in str(e).lower():
                        try:
                            # Используем JavaScript для заполнения поля
                            if by == By.ID:
                                js_script = f"""
                                var element = document.getElementById('{selector}');
                                if (element) {{
                                    element.value = '{text}';
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    return true;
                                }}
                                return false;
                                """
                                result = self.driver.execute_script(js_script)
                                if result:
                                    self.log(f"✅ Заполнено поле через JavaScript: {selector}")
                                    return True
                            elif by == By.NAME:
                                js_script = f"""
                                var elements = document.getElementsByName('{selector}');
                                if (elements.length > 0) {{
                                    var element = elements[0];
                                    element.value = '{text}';
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    return true;
                                }}
                                return false;
                                """
                                result = self.driver.execute_script(js_script)
                                if result:
                                    self.log(f"✅ Заполнено поле через JavaScript: {selector}")
                                    return True
                            elif by == By.CSS_SELECTOR:
                                js_script = f"""
                                var element = document.querySelector('{selector}');
                                if (element) {{
                                    element.value = '{text}';
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    return true;
                                }}
                                return false;
                                """
                                result = self.driver.execute_script(js_script)
                                if result:
                                    self.log(f"✅ Заполнено поле через JavaScript: {selector}")
                                    return True
                        except Exception as js_error:
                            self.log(f"⚠️ Не удалось заполнить поле через JavaScript: {js_error}")
                    time.sleep(0.2)  # Уменьшили задержку с 0.5 до 0.2 секунды
                else:
                    self.log(f"❌ Не удалось заполнить поле {selector}: {e}")
                    # Если все попытки не удались, используем JavaScript как финальную попытку
                    try:
                        # Используем JavaScript для заполнения поля как последнюю меру
                        if by == By.ID:
                            js_script = f"""
                            var element = document.getElementById('{selector}');
                            if (element) {{
                                element.value = '{text}';
                                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return true;
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                self.log(f"✅ Заполнено поле через JavaScript как последняя мера: {selector}")
                                return True
                        elif by == By.NAME:
                            js_script = f"""
                            var elements = document.getElementsByName('{selector}');
                            if (elements.length > 0) {{
                                var element = elements[0];
                                element.value = '{text}';
                                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return true;
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                self.log(f"✅ Заполнено поле через JavaScript как последняя мера: {selector}")
                                return True
                        elif by == By.CSS_SELECTOR:
                            js_script = f"""
                            var element = document.querySelector('{selector}');
                            if (element) {{
                                element.value = '{text}';
                                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return true;
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                self.log(f"✅ Заполнено поле через JavaScript как последняя мера: {selector}")
                                return True
                    except Exception as final_js_error:
                        self.log(f"⚠️ Не удалось заполнить поле через JavaScript как последнюю меру: {final_js_error}")
        
        return False
    
    def _fill_adpi_dates_with_indices(self, adpi_data, field_indices):
        """Заполнение дат АДПИ с использованием найденных индексов"""
        try:
            if adpi_data.get('install_date') and 'install_date' in field_indices:
                install_idx = field_indices['install_date']
                if not self._fill_date_field(f"igtxtctl00_cph_ctrlDopFields_gv_ctl{install_idx}_wdte", adpi_data['install_date']):
                    self.log("⚠️ Не удалось заполнить дату установки АДПИ")
                    return False
            
            if adpi_data.get('check_date') and 'check_date' in field_indices:
                check_idx = field_indices['check_date']
                if not self._fill_date_field(f"igtxtctl00_cph_ctrlDopFields_gv_ctl{check_idx}_wdte", adpi_data['check_date']):
                    self.log("⚠️ Не удалось заполнить дату проверки АДПИ")
                    return False
            
            self.log("✅ Даты АДПИ заполнены")
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка заполнения дат АДПИ: {e}")
            return False

    def _fill_date_field(self, field_id, date_text):
        """Заполнение поля даты"""
        try:
            # Ищем поле даты
            field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, field_id))
            )
            
            # Получаем атрибуты элемента перед возможной устаревшей ссылкой
            element_id = field.get_attribute("id")
            element_name = field.get_attribute("name")
            
            # Прокручиваем к элементу
            self.driver.execute_script("arguments[0].scrollIntoView(true);", field)
            # Убрали задержку, т.к. используем ожидания
            
            # Кликаем на поле
            field.click()
            # Убрали задержку
            
            # Очищаем поле
            field.send_keys(Keys.CONTROL + "a")
            field.send_keys(Keys.DELETE)
            # Убрали задержку
            
            # Вводим дату
            field.send_keys(date_text)
            # Убрали посимвольный ввод и задержки
            
            # Нажимаем Enter для подтверждения
            field.send_keys(Keys.ENTER)
            # Убрали задержку, т.к. следующее действие будет ждать элемент
            
            self.log(f"✅ Дата заполнена: {date_text}")
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка заполнения даты: {e}")
            # Если возникла ошибка stale element reference, пробуем использовать JavaScript
            if "stale element reference" in str(e).lower():
                try:
                    # Используем JavaScript для заполнения поля даты
                    js_script = f"""
                    var dateField = document.getElementById('{field_id}');
                    if (dateField) {{
                        dateField.value = '{date_text}';
                        dateField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        dateField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                    """
                    result = self.driver.execute_script(js_script)
                    if result:
                        self.log(f"✅ Дата заполнена через JavaScript: {date_text}")
                        return True
                except Exception as js_error:
                    self.log(f"⚠️ Не удалось заполнить дату через JavaScript: {js_error}")
                    # Попробуем альтернативный метод с использованием общего селектора
                    try:
                        js_script_alt = f"""
                        var dateField = document.querySelector('#{field_id}');
                        if (dateField) {{
                            dateField.value = '{date_text}';
                            dateField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            dateField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                        """
                        result_alt = self.driver.execute_script(js_script_alt)
                        if result_alt:
                            self.log(f"✅ Дата заполнена через альтернативный JavaScript: {date_text}")
                            return True
                    except Exception as alt_error:
                        self.log(f"⚠️ Не удалось заполнить дату через альтернативный JavaScript: {alt_error}")
            # Если все методы не сработали, возвращаем False
            return False
            
    def _final_verification(self, family_data):
        """Финальная проверка"""
        try:
            mother_fio = family_data.get('mother_fio', 'неизвестно')
            return messagebox.askyesno("Финальная проверка", 
                                     f"Семья: {mother_fio}\n\n"
                                     "Проверьте все введенные данные на странице.\n\n"
                                     "Продолжить сохранение?")
        except:
            return False
            
    def _save_and_exit(self):
        """Сохранение данных"""
        try:
            self.log("💾 Сохраняем данные...")
            
            save_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_cph_lbtnExitSave"))
            )
            save_button.click()
            
            self.log("✅ Данные сохранены")
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка сохранения: {e}")
            return False
            
    def _take_screenshot(self, formatted_data, family_number, family_data):
        """Создание скриншота"""
        try:
            add_info_text, _, _, _ = formatted_data
            lines = add_info_text.split('\n')
            
            mother_name = ""
            for line in lines:
                if line.startswith('Мать: '):
                    mother_info = line[6:]
                    if '(' in mother_info:
                        mother_name = mother_info[:mother_info.index('(')].strip()
                    else:
                        mother_name = mother_info.strip()
                    break
            
            if not mother_name:
                mother_name = f"семья_{family_number}"
            
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', mother_name)
            safe_name = safe_name[:50]
            
            if not self.screenshot_dir:
                self.screenshot_dir = self.gui.screenshots_dir
                
            if not os.path.exists(self.screenshot_dir):
                try:
                    os.makedirs(self.screenshot_dir)
                except Exception as e:
                    self.log(f"⚠️ Не удалось создать папку для скриншотов: {e}")
                    return
            
            file_path = os.path.join(self.screenshot_dir, f"{family_number:03d}_{safe_name}.png")
            
            for attempt in range(3):
                try:
                    self.driver.save_screenshot(file_path)
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        self.log(f"📸 Скриншот сохранен: {file_path}")
                        return
                except Exception as e:
                    if attempt < 2:
                        time.sleep(0.5)
                    else:
                        self.log(f"⚠️ Ошибка скриншота: {e}")
            
        except Exception as e:
            self.log(f"⚠️ Ошибка создания скриншота: {e}")
            
    def _bulk_click_checkboxes(self, checkbox_ids):
        try:
            for checkbox_id in checkbox_ids:
                try:
                    checkbox = self.wait.until(
                        EC.element_to_be_clickable(
                            (By.ID, f"ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_{checkbox_id}")
                        )
                    )
                    if not checkbox.is_selected():
                        checkbox.click()
                        self.log(f"✅ Чекбокс {checkbox_id} отмечен")
                    else:
                        self.log(f"ℹ️ Чекбокс {checkbox_id} уже отмечен")
                    time.sleep(0.02)  # Уменьшено с 0.07 до 0.02 секунды
                except Exception as e:
                    self.log(f"⚠️ Не удалось найти или кликнуть чекбокс {checkbox_id}: {e}")
                    continue
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка отметки чекбоксов: {e}")
            return False
            
    def _bulk_fill_fields(self, field_data):
        try:
            for field_info in field_data:
                try:
                    if field_info['by'] == 'name':
                        element = self.wait.until(
                            EC.element_to_be_clickable((By.NAME, field_info['selector']))
                        )
                        element.clear()
                        element.send_keys(field_info['value'])
                        time.sleep(0.02)  # Уменьшено с 0.07 до 0.02 секунды
                except:
                    continue
            return True
        except Exception as e:
            self.log(f"❌ Ошибка заполнения полей: {e}")
            return False
            
    def _fill_adpi_radio_button(self, adpi_data):
        try:
            # Determine which radio button to select
            if adpi_data['has_adpi'] == 'д':
                radio_button_id = "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0"
                self.log("🔄 Устанавливаем 'Да' для АДПИ")
            else:
                radio_button_id = "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_1"
                self.log("🔄 Устанавливаем 'Нет' для АДПИ")
            
            # Wait for the radio button to be present
            try:
                radio_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, radio_button_id))
                )
                
                # Get attributes before potential stale reference
                element_id = radio_button.get_attribute("id")
                element_name = radio_button.get_attribute("name")
                
                # Check if it's already selected
                is_selected = radio_button.is_selected()
                if is_selected:
                    self.log("ℹ️ Радио-кнопка АДПИ уже выбрана")
                    return True
                
                # Try clicking the radio button
                success = self._click_element_with_retry(By.ID, radio_button_id)
                if success:
                    self.log("✅ Радио-кнопка АДПИ успешно установлена")
                    return True
                else:
                    self.log("⚠️ Не удалось кликнуть радио-кнопку АДПИ через метод _click_element_with_retry")
                    
                    # Try alternative method using JavaScript with fresh reference
                    try:
                        # Use fresh reference to avoid stale element reference
                        fresh_radio_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, element_id))
                        )
                        self.driver.execute_script("arguments[0].click();", fresh_radio_button)
                        self.log("✅ Радио-кнопка АДПИ установлена через JavaScript")
                        return True
                    except Exception as js_error:
                        self.log(f"⚠️ Не удалось установить радио-кнопку АДПИ через JavaScript: {js_error}")
                        
                        # Final attempt: click via dispatchEvent with fresh reference
                        try:
                            fresh_radio_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.ID, element_id))
                            )
                            self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", fresh_radio_button)
                            self.log("✅ Радио-кнопка АДПИ установлена через MouseEvent")
                            return True
                        except Exception as event_error:
                            self.log(f"❌ Не удалось установить радио-кнопку АДПИ через MouseEvent: {event_error}")
                            # Final fallback using direct JavaScript
                            try:
                                js_script = f"""
                                var radioBtn = document.getElementById('{element_id}');
                                if (radioBtn && !radioBtn.checked) {{
                                    radioBtn.checked = true;
                                    radioBtn.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    radioBtn.dispatchEvent(new Event('click', {{ bubbles: true }}));
                                    return true;
                                }}
                                return false;
                                """
                                result = self.driver.execute_script(js_script)
                                if result:
                                    self.log("✅ Радио-кнопка АДПИ установлена через прямой JavaScript")
                                    return True
                                else:
                                    self.log("❌ Не удалось установить радио-кнопку АДПИ через прямой JavaScript")
                                    return False
                            except Exception as final_error:
                                self.log(f"❌ Окончательная ошибка установки радио-кнопки АДПИ: {final_error}")
                                return False
            except Exception as wait_error:
                self.log(f"❌ Ошибка ожидания радио-кнопки АДПИ: {wait_error}")
                return False
                
        except Exception as e:
            self.log(f"⚠️ Ошибка заполнения АДПИ: {e}")
            return False
            
    def _click_element_with_retry(self, by, selector, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                self.log(f"🔄 Попытка {attempt + 1} клика на элемент {selector}")
                
                # First, wait for element to be present
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                
                # Wait a bit for the element to be fully rendered
                time.sleep(0.2)
                
                # Check if element is clickable now
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                
                # Wait for any animations to complete
                time.sleep(0.3)
                
                # Get element attributes before potential stale reference
                element_id = element.get_attribute("id")
                element_name = element.get_attribute("name")
                
                # Try to click the element
                try:
                    element.click()
                    self.log(f"✅ Успешно кликнут элемент: {selector}")
                    return True
                except Exception as click_error:
                    # If direct click fails, try different approaches
                    try:
                        # Try clicking via JavaScript using fresh element reference
                        if element_id:
                            # Use the ID to get a fresh reference to the element
                            fresh_element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.ID, element_id))
                            )
                            self.driver.execute_script("arguments[0].click();", fresh_element)
                        elif element_name:
                            # Use the name to get a fresh reference to the element
                            fresh_element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.NAME, element_name))
                            )
                            self.driver.execute_script("arguments[0].click();", fresh_element)
                        else:
                            # Use the original selector to get a fresh reference
                            fresh_element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            self.driver.execute_script("arguments[0].click();", fresh_element)
                        self.log(f"✅ Успешно кликнут элемент через JavaScript: {selector}")
                        return True
                    except Exception as js_error:
                        # Try sending a click event with fresh element
                        try:
                            if element_id:
                                fresh_element = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.ID, element_id))
                                )
                                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", fresh_element)
                            elif element_name:
                                fresh_element = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.NAME, element_name))
                                )
                                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", fresh_element)
                            else:
                                fresh_element = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((by, selector))
                                )
                                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", fresh_element)
                            self.log(f"✅ Успешно кликнут элемент через MouseEvent: {selector}")
                            return True
                        except Exception as event_error:
                            self.log(f"⚠️ Все методы клика не удались: {click_error}, {event_error}")
                            # If all methods fail, try a more general approach
                            try:
                                # Execute JavaScript to click the element directly
                                script = f"document.querySelector('{selector.replace(By.ID, '#').replace(By.NAME, '[name]').replace(By.CLASS_NAME, '.')}').click();"
                                if by == By.ID:
                                    script = f"document.getElementById('{selector}').click();"
                                elif by == By.NAME:
                                    script = f"document.querySelector('[name=\"{selector}\"]').click();"
                                elif by == By.CLASS_NAME:
                                    script = f"document.querySelector('.{selector}').click();"
                                elif by == By.CSS_SELECTOR:
                                    script = f"document.querySelector('{selector}').click();"
                                elif by == By.XPATH:
                                    script = f"document.evaluate('{selector}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click();"
                                
                                self.driver.execute_script(script)
                                self.log(f"✅ Успешно кликнут элемент через общий JavaScript: {selector}")
                                return True
                            except Exception as general_error:
                                self.log(f"⚠️ Общий метод клика не сработал: {general_error}")
                                # Last resort: try to find the element again and use a more robust approach
                                try:
                                    # Find the element again using its attributes
                                    if element_id:
                                        self.driver.execute_script(f"document.getElementById('{element_id}').click();")
                                        self.log(f"✅ Успешно кликнут элемент через ID JavaScript: {element_id}")
                                        return True
                                    elif element_name:
                                        self.driver.execute_script(f"document.querySelector('[name=\"{element_name}\"]').click();")
                                        self.log(f"✅ Успешно кликнут элемент через Name JavaScript: {element_name}")
                                        return True
                                    else:
                                        continue
                                except Exception as last_resort_error:
                                    self.log(f"⚠️ Последняя попытка клика не удалась: {last_resort_error}")
                                    continue
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"⚠️ Попытка {attempt + 1} клика на элемент {selector} не удалась: {str(e)}")
                    # If we encounter a stale element reference, wait a bit more before retrying
                    if "stale element reference" in str(e).lower():
                        time.sleep(1)  # Wait longer when dealing with stale element references
                    else:
                        time.sleep(0.5)  # Wait a bit longer between attempts
                else:
                    self.log(f"❌ Не удалось кликнуть элемент {selector} после {max_attempts} попыток: {str(e)}")
                    return False
        return False
        
    def _fill_textarea(self, field_name, text, resize=False):
        try:
            # First, wait for the element to be present
            field = self.wait.until(EC.presence_of_element_located((By.NAME, field_name)))
            
            # Wait a bit more for the element to be fully loaded
            time.sleep(0.3)
            
            # Now wait for it to be clickable
            field = self.wait.until(EC.element_to_be_clickable((By.NAME, field_name)))
            
            # Get field attributes before potential stale reference
            field_id = field.get_attribute("id")
            field_name_attr = field.get_attribute("name")
            
            # Scroll to the element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", field)
            time.sleep(0.3)
            
            # Clear the field using JavaScript to ensure it's completely cleared
            self.driver.execute_script("arguments[0].value = '';", field)
            
            # Click on the field to focus it
            field.click()
            
            # Fill the field using multiple methods to ensure success
            try:
                # Method 1: Direct send_keys
                field.send_keys(Keys.CONTROL + "a")  # Select all
                field.send_keys(Keys.DELETE)  # Delete selected
                field.send_keys(text)  # Send the new text
            except Exception as direct_error:
                # Method 2: Using JavaScript if direct method fails
                try:
                    # Use fresh reference to the element to avoid stale element reference
                    if field_id:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, field_id))
                        )
                        self.driver.execute_script("arguments[0].value = arguments[1];", fresh_field, text)
                    else:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.NAME, field_name_attr))
                        )
                        self.driver.execute_script("arguments[0].value = arguments[1];", fresh_field, text)
                    # Trigger input event so the page recognizes the change
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", fresh_field)
                except:
                    # If stale element reference occurs, use direct JavaScript method
                    result = self._fill_textarea_directly_by_name(field_name, text)
                    if result:
                        self.log(f"✅ Текстовая область заполнена через JavaScript")
                        if resize:
                            script = f"var el = document.getElementsByName('{field_name}')[0]; if(el) {{ el.style.height = '352px'; el.style.width = '1151px'; }}"
                            self.driver.execute_script(script)
                        return True
                    else:
                        raise direct_error  # Re-raise the original error
            
            # Verify the text was set correctly
            actual_value = field.get_attribute("value") or field.get_property("value")
            if actual_value != text:
                # If the value doesn't match, try JavaScript method
                try:
                    # Use fresh reference to the element to avoid stale element reference
                    if field_id:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, field_id))
                        )
                        self.driver.execute_script("arguments[0].value = arguments[1];", fresh_field, text)
                    else:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.NAME, field_name_attr))
                        )
                        self.driver.execute_script("arguments[0].value = arguments[1];", fresh_field, text)
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", fresh_field)
                except:
                    # If stale element reference occurs, use direct JavaScript method
                    result = self._fill_textarea_directly_by_name(field_name, text)
                    if not result:
                        self.log("⚠️ Не удалось заполнить текстовую область")
                        return False
            
            if resize:
                try:
                    # Use fresh reference to the element to avoid stale element reference
                    if field_id:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, field_id))
                        )
                        self.driver.execute_script("arguments[0].style.height = '352px'; arguments[0].style.width = '1151px';", fresh_field)
                    else:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.NAME, field_name_attr))
                        )
                        self.driver.execute_script("arguments[0].style.height = '352px'; arguments[0].style.width = '1151px';", fresh_field)
                except:
                    # If stale element reference occurs, use direct JavaScript method for resize
                    resize_script = f"var el = document.getElementsByName('{field_name}')[0]; if(el) {{ el.style.height = '352px'; el.style.width = '1151px'; }}"
                    self.driver.execute_script(resize_script)
            
            self.log(f"✅ Текстовая область заполнена ({len(text)} символов)")
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка текстовой области: {e}")
            # Try the direct JavaScript method as a fallback
            try:
                result = self._fill_textarea_directly_by_name(field_name, text)
                if result:
                    self.log(f"✅ Текстовая область заполнена через JavaScript")
                    if resize:
                        script = f"var el = document.getElementsByName('{field_name}')[0]; if(el) {{ el.style.height = '352px'; el.style.width = '1151px'; }}"
                        self.driver.execute_script(script)
                    return True
            except Exception as js_error:
                self.log(f"⚠️ Ошибка при заполнении текстовой области через JavaScript: {js_error}")
                # Final fallback: use direct JavaScript with more robust error handling
                try:
                    # Use more robust JavaScript approach to fill the textarea
                    escaped_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
                    js_script = f"""
                    var elements = document.getElementsByName('{field_name}');
                    if (elements.length > 0) {{
                        var textarea = elements[0];
                        textarea.value = '{escaped_text}';
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                    """
                    result = self.driver.execute_script(js_script)
                    if result:
                        self.log(f"✅ Текстовая область заполнена через прямой JavaScript")
                        if resize:
                            resize_script = f"var el = document.getElementsByName('{field_name}')[0]; if(el) {{ el.style.height = '352px'; el.style.width = '1151px'; }}"
                            self.driver.execute_script(resize_script)
                        return True
                except Exception as final_error:
                    self.log(f"❌ Не удалось заполнить текстовую область даже через прямой JavaScript: {final_error}")
            return False
    
    def _fill_textarea_directly_by_name(self, field_name, text):
        """Прямое заполнение textarea по NAME через JavaScript"""
        try:
            # Escape backticks in the text to prevent breaking the JavaScript template literal
            escaped_text = text.replace('`', '\\`')
            script = f"""
            var elements = document.getElementsByName('{field_name}');
            if (elements.length > 0) {{
                var textarea = elements[0];
                textarea.value = `{escaped_text}`;
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                return true;
            }}
            return false;
            """
            result = self.driver.execute_script(script)
            return result
        except Exception as e:
            self.log(f"⚠️ Не удалось заполнить через JavaScript по NAME: {e}")
            return False
            
    def _fill_textarea_directly(self, element_id, text):
        """Прямое заполнение textarea по ID через JavaScript"""
        try:
            # Escape backticks in the text to prevent breaking the JavaScript template literal
            escaped_text = text.replace('`', '\\`')
            script = f"""
            var textarea = document.getElementById('{element_id}');
            if (textarea) {{
                textarea.value = `{escaped_text}`;
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                return true;
            }}
            return false;
            """
            result = self.driver.execute_script(script)
            if result:
                self.log(f"✅ Текстовая область заполнена через JavaScript")
                return True
        except Exception as e:
            self.log(f"⚠️ Не удалось заполнить через JavaScript: {e}")
        return False
            
    def _click_element(self, by, selector):
        try:
            element = self.wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка клика: {e}")
            return False
            
    def _get_element_text(self, element_id, default=""):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, element_id))
            )
            return element.text
        except Exception as e:
            self.log(f"⚠️ Ошибка получения текста элемента {element_id}: {e}")
            return default
    
