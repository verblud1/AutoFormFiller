#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЕДИНАЯ ТОЧКА ВХОДА - СИСТЕМА РАБОТЫ С СЕМЬЯМИ
Запускает все компоненты системы через графический интерфейс
"""

import os
import sys
import subprocess
import platform
import threading
import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import json
import webbrowser
from datetime import datetime, timedelta
import shutil

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FamilySystemLauncher:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("🚀 Система работы с семьями")
        self.app.geometry("800x600")
        self.app.resizable(False, False)
        
        # Центрируем окно
        self.center_window()
        
        # Пути
        self.home_dir = os.path.expanduser("~")
        self.desktop_path = self.get_desktop_path()
        self.system_dir = os.path.join(self.desktop_path, "FamilySystem")
        
        # Файлы системы
        self.files_to_copy = [
            "json_family_creator.py",
            "massform.py",
            "database_client.sh",
            "database_client.bat",
            "config.env",
            "family_system_launcher.py"  # Этот файл
        ]
        
        
        self.github_token = None
        self.github_token_file = os.path.join(self.system_dir, ".github_token") if hasattr(self, 'system_dir') else None
        self.load_github_token()

        # Организация конфигурационных файлов в отдельную папку
        self.setup_config_directory()
        
        # Файлы конфигурации
        self.stats_file = os.path.join(self.config_dir, "processing_statistics.json")
        
        self.stats = self.load_statistics()
        
        # Переменные для статистики
        self.success_count = 0
        self.daily_stat = 0
        self.weekly_stat = 0

        # Проверяем установку
        self.is_installed = os.path.exists(self.system_dir)
        
        # Настройки
        self.config = self.load_config()
        
        self.setup_ui()
        
        # Автоматически проверяем установку при запуске
        self.app.after(100, self.check_installation_status)
        
        # Обновляем отображение статистики при запуске
        self.app.after(200, self.update_statistics_display)
        
        # Периодическое обновление статистики (раз в 30 секунд)
        self.app.after(30000, self.periodic_statistics_update)

    def setup_config_directory(self):
        """Создание папки для конфигурационных файлов"""
        try:
            # Определяем путь к директории приложения
            app_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir = os.path.join(app_dir, "config")
            
            # Создаем папку config, если она не существует
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                print(f"✅ Создана папка конфигурации: {self.config_dir}")
            
            # Создаем подпапку для логов
            self.logs_dir = os.path.join(self.config_dir, "logs")
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
                print(f"✅ Создана папка для логов: {self.logs_dir}")
                
            # Создаем подпапку для скриншотов
            self.screenshots_dir = os.path.join(self.config_dir, "screenshots")
            if not os.path.exists(self.screenshots_dir):
                os.makedirs(self.screenshots_dir)
                print(f"✅ Создана папка для скриншотов: {self.screenshots_dir}")
                
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
            print(f"⚠️ Ошибка загрузки статистики: {e}")
            return {'daily': {}, 'weekly': {}}

    def save_statistics(self):
        """Сохранение статистики обработки"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения статистики: {e}")
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
            
            print(f"📊 Статистика обновлена: +{success_count} семей")
            return True
        except Exception as e:
            print(f"⚠️ Ошибка обновления статистики: {e}")
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
            print(f"⚠️ Ошибка получения статистики: {e}")
            return 0, 0

    def update_statistics_display(self):
        """Обновление отображения статистики в интерфейсе"""
        try:
            today_stat, week_stat = self.get_statistics_for_period()
            self.stat_label.configure(
                text=f"📊 Статистика: Сегодня - {today_stat} | Неделя - {week_stat}"
            )
        except Exception as e:
            print(f"⚠️ Ошибка обновления отображения статистики: {e}")
            
    def periodic_statistics_update(self):
        """Периодическое обновление статистики"""
        try:
            # Обновляем статистику
            self.update_statistics_display()
            
            # Запланировать следующее обновление
            self.app.after(30000, self.periodic_statistics_update)
        except Exception as e:
            print(f"⚠️ Ошибка периодического обновления статистики: {e}")
    
    def center_window(self):
        """Центрирует окно на экране"""
        self.app.update_idletasks()
        width = self.app.winfo_width()
        height = self.app.winfo_height()
        x = (self.app.winfo_screenwidth() // 2) - (width // 2)
        y = (self.app.winfo_screenheight() // 2) - (height // 2)
        self.app.geometry(f'{width}x{height}+{x}+{y}')
    
    def get_desktop_path(self):
        """Определяет путь к рабочему столу для разных ОС"""
        system = platform.system()
        
        if system == "Windows":
            desktop = os.path.join(self.home_dir, "Desktop")
        elif system in ["Linux", "RedOS"]:
            # Пробуем разные варианты для Linux
            possible_paths = [
                os.path.join(self.home_dir, "Рабочий стол"),
                os.path.join(self.home_dir, "Desktop"),
                os.path.join(self.home_dir, "desktop"),
                os.path.join(self.home_dir, "Стол")
            ]
            
            desktop = self.home_dir + "/Desktop"  # По умолчанию
            
            for path in possible_paths:
                if os.path.exists(path):
                    desktop = path
                    break
            else:
                # Если папки нет, создаем
                desktop = os.path.join(self.home_dir, "Desktop")
                os.makedirs(desktop, exist_ok=True)
        else:
            desktop = os.path.join(self.home_dir, "Desktop")
        
        return desktop
    
    def load_config(self):
        """Загружает конфигурацию"""
        config_file = os.path.join(os.path.dirname(__file__), "launcher_config.json")
        default_config = {
            "last_used": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "installation_path": self.system_dir,
            "auto_check_updates": True
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_config
        
        return default_config
    
    def save_config(self):
        """Сохраняет конфигурацию"""
        config_file = os.path.join(os.path.dirname(__file__), "launcher_config.json")
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def setup_ui(self):
        """Настраивает пользовательский интерфейс"""
        # Основной контейнер
        main_frame = ctk.CTkFrame(self.app)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame, 
            text="🚀 СИСТЕМА РАБОТЫ С СЕМЬЯМИ",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack()
        
        ctk.CTkLabel(
            title_frame,
            text="Единая точка входа для всех компонентов системы",
            font=ctk.CTkFont(size=14)
        ).pack()
        
        # Информация о системе
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(
            info_frame,
            text="Статус: проверка...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Отображение статистики
        self.stat_label = ctk.CTkLabel(
            info_frame,
            text="📊 Статистика: Сегодня - 0 | Неделя - 0",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.stat_label.pack(pady=5)
        self.update_statistics_display()
        
        # Блок кнопок
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Кнопка 1: Создатель JSON
        self.btn_json = ctk.CTkButton(
            buttons_frame,
            text="📝 ВНЕСТИ СЕМЬИ В JSON",
            command=self.launch_json_creator,
            height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2B7A78",
            hover_color="#175A58"
        )
        self.btn_json.pack(fill="x", pady=10)
        
        # Кнопка 2: Массовый обработчик
        self.btn_mass = ctk.CTkButton(
            buttons_frame,
            text="⚙️ ЗАПОЛНИТЬ В БАЗУ",
            command=self.launch_mass_processor,
            height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3A506B",
            hover_color="#2A406B"
        )
        self.btn_mass.pack(fill="x", pady=10)
        
        # Кнопка 3: База данных
        self.btn_db = ctk.CTkButton(
            buttons_frame,
            text="🗄️ ЗАПУСТИТЬ БАЗУ ДАННЫХ",
            command=self.launch_database,
            height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#5E4AE3",
            hover_color="#4A3AD3"
        )
        self.btn_db.pack(fill="x", pady=10)
        
        # Нижняя панель управления
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=(20, 0))
        
        # Кнопки управления системой
        manage_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        manage_frame.pack(fill="x", pady=5)
        
        self.btn_install = ctk.CTkButton(
            manage_frame,
            text="📦 УСТАНОВИТЬ СИСТЕМУ",
            command=self.install_system,
            width=180,
            fg_color="#28A745",
            hover_color="#218838"
        )
        self.btn_install.pack(side="left", padx=5)
        
          # В методе setup_ui() добавьте кнопку (после других кнопок):
        self.btn_github = ctk.CTkButton(
            buttons_frame,
            text="🔄 ОБНОВИТЬ ЧЕРЕЗ GITHUB",
            command=self.update_from_github,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6f42c1",
            hover_color="#5a32a3"
        )
        self.btn_github.pack(fill="x", pady=10)
    
        self.btn_update = ctk.CTkButton(
            manage_frame,
            text="🔄 ОБНОВИТЬ",
            command=self.update_system,
            width=120,
            fg_color="#17A2B8",
            hover_color="#138496"
        )
        self.btn_update.pack(side="left", padx=5)
        
        self.btn_uninstall = ctk.CTkButton(
            manage_frame,
            text="🗑️ УДАЛИТЬ",
            command=self.uninstall_system,
            width=120,
            fg_color="#DC3545",
            hover_color="#C82333"
        )
        self.btn_uninstall.pack(side="left", padx=5)
        
        self.btn_open_folder = ctk.CTkButton(
            manage_frame,
            text="📁 ПАПКА СИСТЕМЫ",
            command=self.open_system_folder,
            width=140,
            fg_color="#6C757D",
            hover_color="#5A6268"
        )
        self.btn_open_folder.pack(side="left", padx=5)
        
        # Лог
        log_frame = ctk.CTkFrame(main_frame, height=120)
        log_frame.pack(fill="x", padx=10, pady=(20, 10))
        
        ctk.CTkLabel(
            log_frame,
            text="📋 Лог действий:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=5,
            width=70,
            bg="#2B2B2B",
            fg="white",
            font=("Courier", 10)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text.config(state="disabled")
    
    def log_message(self, message):
        """Добавляет сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state="normal")
        self.log_text.insert("end", log_entry)
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        
        self.app.update_idletasks()
        print(log_entry.strip())
    
    def check_installation_status(self):
        """Проверяет статус установки и обновляет интерфейс"""
        self.is_installed = os.path.exists(self.system_dir)
        
        if self.is_installed:
            self.status_label.configure(
                text=f"✅ Система установлена в: {self.system_dir}",
                text_color="green"
            )
            self.btn_install.configure(state="disabled", text="✅ УСТАНОВЛЕНА")
            self.btn_update.configure(state="normal")
            self.btn_uninstall.configure(state="normal")
            self.btn_open_folder.configure(state="normal")
            
            # Проверяем доступность компонентов
            self.check_components()
            
            # Обновляем статистику
            self.update_statistics_display()
        else:
            self.status_label.configure(
                text="❌ Система не установлена. Нажмите 'Установить систему'",
                text_color="red"
            )
            self.btn_install.configure(state="normal", text="📦 УСТАНОВИТЬ СИСТЕМУ")
            self.btn_update.configure(state="disabled")
            self.btn_uninstall.configure(state="disabled")
            self.btn_open_folder.configure(state="disabled")
            
            # Отключаем основные кнопки
            self.btn_json.configure(state="disabled")
            self.btn_mass.configure(state="disabled")
            self.btn_db.configure(state="disabled")
    
    def check_components(self):
        """Проверяет наличие компонентов системы"""
        missing = []
        
        # Проверяем основные файлы
        base_files = ["json_family_creator.py", "massform.py"]
        for file in base_files:
            file_path = os.path.join(self.system_dir, file)
            if not os.path.exists(file_path):
                missing.append(file)
        
        # Проверяем OS-специфичные файлы
        if platform.system() == "Windows":
            windows_files = ["database_client.bat"]
            for file in windows_files:
                file_path = os.path.join(self.system_dir, file)
                if not os.path.exists(file_path):
                    missing.append(file)
        else:  # Linux/RedOS
            linux_files = ["database_client.sh"]
            for file in linux_files:
                file_path = os.path.join(self.system_dir, file)
                if not os.path.exists(file_path):
                    missing.append(file)
        
        if missing:
            self.log_message(f"⚠️ Отсутствуют файлы: {', '.join(missing)}")
            # Разрешаем использовать компоненты, даже если нет файлов базы данных
            self.btn_json.configure(state="normal")
            self.btn_mass.configure(state="normal")
            # Разрешаем кнопку базы данных только если файл есть
            if platform.system() == "Windows":
                if os.path.exists(os.path.join(self.system_dir, "database_client.bat")):
                    self.btn_db.configure(state="normal")
                else:
                    self.btn_db.configure(state="disabled")
            else:
                if os.path.exists(os.path.join(self.system_dir, "database_client.sh")):
                    self.btn_db.configure(state="normal")
                else:
                    self.btn_db.configure(state="disabled")
        else:
            self.btn_json.configure(state="normal")
            self.btn_mass.configure(state="normal")
            self.btn_db.configure(state="normal")
            self.log_message("✅ Все компоненты системы доступны")
    
    def install_system(self):
        """Устанавливает систему на рабочий стол"""
        try:
            if self.is_installed:
                response = messagebox.askyesno(
                    "Подтверждение",
                    "Система уже установлена. Переустановить?\n\n"
                    "Существующие файлы будут перезаписаны."
                )
                if not response:
                    return
            
            # Создаем папку системы
            os.makedirs(self.system_dir, exist_ok=True)
            self.log_message(f"📁 Создана папка: {self.system_dir}")
            
            # Копируем файлы
            script_dir = os.path.dirname(os.path.abspath(__file__))
            copied_files = 0
            
            for filename in self.files_to_copy:
                src_path = os.path.join(script_dir, filename)
                dst_path = os.path.join(self.system_dir, filename)
                
                if os.path.exists(src_path):
                    try:
                        shutil.copy2(src_path, dst_path)
                        copied_files += 1
                        self.log_message(f"📄 Скопирован: {filename}")
                    except Exception as e:
                        self.log_message(f"❌ Ошибка копирования {filename}: {e}")
                else:
                    self.log_message(f"⚠️ Файл не найден: {filename}")
            
            # Создаем конфигурационный файл если его нет
            config_file = os.path.join(self.system_dir, "config.env")
            if not os.path.exists(config_file):
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write("""# Конфигурация подключения к базе данных
# ЗАПОЛНИТЕ ЭТИ НАСТРОЙКИ ПЕРЕД ЗАПУСКОМ

SSH_HOST="192.168.10.59"
SSH_USER="sshuser"
SSH_PASSWORD="orsd321"
LOCAL_PORT="8080"
REMOTE_HOST="172.30.1.18"
REMOTE_PORT="80"
WEB_PATH="/aspnetkp/common/FindInfo.aspx"
""")
                self.log_message("⚙️ Создан конфигурационный файл config.env")
            
            # Делаем скрипты исполняемыми (для Linux)
            if platform.system() in ["Linux", "RedOS"]:
                for script in ["database_client.sh"]:
                    script_path = os.path.join(self.system_dir, script)
                    if os.path.exists(script_path):
                        os.chmod(script_path, 0o755)
                        self.log_message(f"🔧 Сделал исполняемым: {script}")
            
            # Создаем ярлык (только для Windows)
            if platform.system() == "Windows":
                self.create_windows_shortcut()
            
            # Создаем .desktop файл (для Linux/RedOS)
            elif platform.system() in ["Linux", "RedOS"]:
                self.create_linux_desktop_file()
            
            # Обновляем конфигурацию
            self.config["installation_path"] = self.system_dir
            self.config["last_install"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_config()
            
            # Обновляем статус
            self.log_message(f"✅ Установка завершена! Скопировано файлов: {copied_files}")
            messagebox.showinfo(
                "Установка завершена",
                f"✅ Система успешно установлена в:\n{self.system_dir}\n\n"
                f"📋 Скопировано файлов: {copied_files}\n\n"
                "Теперь вы можете использовать все функции системы."
            )
            
            self.check_installation_status()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка установки: {str(e)}")
            messagebox.showerror("Ошибка установки", f"Не удалось установить систему:\n{str(e)}")
    
    def create_windows_shortcut(self):
        """Создает ярлык на рабочем столе Windows"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            # Создаем ярлык на рабочем столе
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Система работы с семьями.lnk")
            
            target = sys.executable
            arguments = os.path.join(self.system_dir, "family_system_launcher.py")
            working_dir = self.system_dir
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.Arguments = f'"{arguments}"'
            shortcut.WorkingDirectory = working_dir
            shortcut.IconLocation = target  # Используем иконку Python
            shortcut.save()
            
            self.log_message("🖱️ Создан ярлык на рабочем столе Windows")
            return True
            
        except Exception as e:
            self.log_message(f"⚠️ Не удалось создать ярлык Windows: {e}")
            return False
    
    def create_linux_desktop_file(self):
        """Создает .desktop файл для Linux/RedOS"""
        try:
            desktop_file = os.path.join(self.desktop_path, "family_system.desktop")
            
            with open(desktop_file, 'w', encoding='utf-8') as f:
                f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Система работы с семьями
Comment=Запуск всех компонентов системы обработки семей
Exec=python3 {os.path.join(self.system_dir, 'family_system_launcher.py')}
Path={self.system_dir}
Icon=system-run
Terminal=false
Categories=Utility;Office;
StartupNotify=true
""")
            
            os.chmod(desktop_file, 0o755)
            self.log_message("🖱️ Создан .desktop файл на рабочем столе")
            return True
            
        except Exception as e:
            self.log_message(f"⚠️ Не удалось создать .desktop файл: {e}")
            return False
    
    def update_system(self):
        """Обновляет систему"""
        try:
            # Просто переустанавливаем (копируем заново)
            self.log_message("🔄 Начинаю обновление системы...")
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Создаем резервную копию конфига
            config_file = os.path.join(self.system_dir, "config.env")
            backup_file = os.path.join(self.system_dir, "config.env.backup")
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_file)
                self.log_message("📋 Создана резервная копия конфигурации")
            
            # Копируем файлы с заменой
            for filename in self.files_to_copy:
                src_path = os.path.join(script_dir, filename)
                dst_path = os.path.join(self.system_dir, filename)
                
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)
                    self.log_message(f"📄 Обновлен: {filename}")
            
            # Восстанавливаем конфиг из резервной копии
            if os.path.exists(backup_file):
                shutil.move(backup_file, config_file)
                self.log_message("⚙️ Восстановлена конфигурация из резервной копии")
            
            # Обновляем дату в конфиге
            self.config["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_config()
            
            self.log_message("✅ Обновление завершено")
            messagebox.showinfo("Обновление", "✅ Система успешно обновлена!")
            
            self.check_components()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка обновления: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось обновить систему:\n{str(e)}")
    
    def uninstall_system(self):
        """Удаляет систему"""
        try:
            response = messagebox.askyesno(
                "Подтверждение удаления",
                f"Вы уверены, что хотите удалить систему?\n\n"
                f"Папка: {self.system_dir}\n\n"
                "Все данные будут удалены без возможности восстановления!"
            )
            
            if not response:
                return
            
            # Удаляем папку системы
            if os.path.exists(self.system_dir):
                shutil.rmtree(self.system_dir)
                self.log_message(f"🗑️ Удалена папка: {self.system_dir}")
            
            # Удаляем ярлыки
            if platform.system() == "Windows":
                try:
                    import winshell
                    desktop = winshell.desktop()
                    shortcut = os.path.join(desktop, "Система работы с семьями.lnk")
                    if os.path.exists(shortcut):
                        os.remove(shortcut)
                        self.log_message("🗑️ Удален ярлык Windows")
                except:
                    pass
            
            elif platform.system() in ["Linux", "RedOS"]:
                desktop_files = [
                    os.path.join(self.desktop_path, "family_system.desktop"),
                    os.path.join(self.desktop_path, "Система_работы_с_семьями.desktop")
                ]
                
                for desktop_file in desktop_files:
                    if os.path.exists(desktop_file):
                        os.remove(desktop_file)
                        self.log_message(f"🗑️ Удален .desktop файл: {os.path.basename(desktop_file)}")
            
            self.log_message("✅ Система удалена")
            messagebox.showinfo("Удаление", "✅ Система успешно удалена!")
            
            self.check_installation_status()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка удаления: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось удалить систему:\n{str(e)}")
    
    def open_system_folder(self):
        """Открывает папку с системой"""
        try:
            if os.path.exists(self.system_dir):
                if platform.system() == "Windows":
                    os.startfile(self.system_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", self.system_dir])
                else:  # Linux/RedOS
                    subprocess.Popen(["xdg-open", self.system_dir])
                self.log_message("📁 Открыта папка системы")
            else:
                messagebox.showwarning("Папка не найдена", "Папка системы не найдена. Установите систему сначала.")
        except Exception as e:
            self.log_message(f"⚠️ Не удалось открыть папку: {e}")
    
    def launch_json_creator(self):
        """Запускает создателя JSON"""
        try:
            script_path = os.path.join(self.system_dir, "json_family_creator.py")
            
            if not os.path.exists(script_path):
                messagebox.showerror("Ошибка", "Файл json_family_creator.py не найден!")
                return
            
            self.log_message("🚀 Запускаю Создатель JSON...")
            
            if platform.system() == "Windows":
                subprocess.Popen([sys.executable, script_path], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["python3", script_path])
            
            self.log_message("✅ Создатель JSON запущен")
            
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось запустить Создатель JSON:\n{str(e)}")
    
    def launch_mass_processor(self):
        """Запускает массовый обработчик"""
        try:
            script_path = os.path.join(self.system_dir, "massform.py")
            
            if not os.path.exists(script_path):
                messagebox.showerror("Ошибка", "Файл massform.py не найден!")
                return
            
            self.log_message("🚀 Запускаю Массовый обработчик...")
            
            if platform.system() == "Windows":
                subprocess.Popen([sys.executable, script_path],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["python3", script_path])
            
            self.log_message("✅ Массовый обработчик запущен")
            
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось запустить Массовый обработчик:\n{str(e)}")
            
    def increment_success_count(self, count=1):
        """Увеличивает счетчик успешных обработок"""
        try:
            # Обновляем статистику
            self.update_statistics(count)
        except Exception as e:
            print(f"⚠️ Ошибка обновления статистики: {e}")
    
      

    

    # Добавьте эти методы в класс:
    def load_github_token(self):
        """Загружает токен GitHub из локального файла"""
        if self.github_token_file and os.path.exists(self.github_token_file):
            try:
                with open(self.github_token_file, 'r', encoding='utf-8') as f:
                    self.github_token = f.read().strip()
                    if self.github_token:
                        self.log_message("🔑 GitHub токен загружен из локального хранилища")
            except:
                self.github_token = None

    def save_github_token(self, token):
        """Сохраняет токен GitHub в локальный файл"""
        if not self.github_token_file:
            return False
        try:
            with open(self.github_token_file, 'w', encoding='utf-8') as f:
                f.write(token.strip())
            os.chmod(self.github_token_file, 0o600)  # Только для владельца
            self.github_token = token.strip()
            self.log_message("✅ GitHub токен сохранен локально")
            return True
        except Exception as e:
            self.log_message(f"❌ Ошибка сохранения токена: {e}")
            return False

    def ask_github_token(self):
        """Запрашивает токен GitHub у пользователя"""
        dialog = ctk.CTkInputDialog(
            text="Введите GitHub Personal Access Token (необязательно):\n\n"
                "Без токена: 60 запросов в час\n"
                "С токеном: 5000 запросов в час\n\n"
                "Как получить токен:\n"
                "1. GitHub → Settings → Developer settings\n"
                "2. Personal access tokens → Tokens (classic)\n"
                "3. Выберите scopes: repo (все)\n\n"
                "Оставьте поле пустым для работы без токена:",
            title="GitHub Token"
        )
        token = dialog.get_input()
        
        if token and token.strip():
            if self.save_github_token(token):
                return True
        elif token == "":  # Пользователь явно нажал OK без токена
            self.save_github_token("")  # Сохраняем пустой токен
            return True
        
        return False

    def update_from_github(self):
        """Обновляет файлы системы из GitHub репозитория"""
        try:
            if not self.is_installed:
                messagebox.showerror("Ошибка", "Сначала установите систему!")
                return
            
            # Запрашиваем токен при первом обновлении
            if self.github_token is None:
                if not self.ask_github_token():
                    self.log_message("⚠️ Обновление отменено пользователем")
                    return
            
            self.log_message("🔄 Проверяю обновления на GitHub...")
            
            # Запускаем обновление в отдельном потоке
            threading.Thread(target=self._github_update_thread, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска обновления: {str(e)}")

    def _github_update_thread(self):
        """Поток для обновления из GitHub"""
        try:
            import requests
            import hashlib
            
            repo_owner = "verblud1"
            repo_name = "AutoFormFiller"
            branch = "main"
            
            self.log_message(f"📡 Подключаюсь к репозиторию: {repo_owner}/{repo_name}")
            
            # Создаем сессию с токеном если есть
            session = requests.Session()
            if self.github_token:
                session.headers.update({"Authorization": f"token {self.github_token}"})
            
            # Получаем информацию о репозитории
            repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
            
            # Список файлов для обновления (исключая конфиги)
            files_to_update = [
                "json_family_creator.py",
                "massform.py",
                "database_client.sh",
                "family_system_launcher.py"
            ]
            
            updated_files = 0
            skipped_files = 0
            error_files = 0
            
            for filename in files_to_update:
                try:
                    # Получаем информацию о файле с GitHub
                    file_url = f"{repo_url}/{filename}?ref={branch}"
                    response = session.get(file_url, timeout=10)
                    
                    if response.status_code == 403 and "rate limit" in response.text.lower():
                        self.log_message("⚠️ Достигнут лимит запросов GitHub. Попробуйте позже или используйте токен.")
                        break
                    
                    if response.status_code != 200:
                        self.log_message(f"⚠️ Файл {filename} не найден на GitHub")
                        continue
                    
                    file_info = response.json()
                    content_encoded = file_info.get("content", "")
                    sha_github = file_info.get("sha", "")
                    
                    # Декодируем контент (base64)
                    import base64
                    content = base64.b64decode(content_encoded).decode('utf-8')
                    
                    # Путь к локальному файлу
                    local_path = os.path.join(self.system_dir, filename)
                    
                    # Проверяем, существует ли локальный файл
                    if os.path.exists(local_path):
                        # Читаем локальный файл и вычисляем хэш
                        with open(local_path, 'r', encoding='utf-8') as f:
                            local_content = f.read()
                        
                        # Сравниваем хэши
                        local_hash = hashlib.sha1(local_content.encode()).hexdigest()
                        
                        if local_hash == sha_github:
                            self.log_message(f"✓ {filename} уже актуален")
                            skipped_files += 1
                            continue
                    
                    # Создаем резервную копию если файл существует
                    if os.path.exists(local_path):
                        backup_path = local_path + ".backup"
                        shutil.copy2(local_path, backup_path)
                    
                    # Сохраняем новый файл
                    with open(local_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Делаем исполняемым если нужно
                    if filename.endswith(".sh"):
                        os.chmod(local_path, 0o755)
                    
                    self.log_message(f"✅ Обновлен: {filename}")
                    updated_files += 1
                    
                    # Небольшая задержка между запросами
                    import time
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.log_message(f"❌ Ошибка обновления {filename}: {str(e)}")
                    error_files += 1
            
            # Обновляем README если есть
            self.update_readme_from_github(session, repo_url, branch)
            
            # Итоговый отчет
            if updated_files > 0:
                self.log_message(f"\n✨ Обновление завершено!")
                self.log_message(f"📊 Обновлено файлов: {updated_files}")
                self.log_message(f"📊 Пропущено (актуальны): {skipped_files}")
                if error_files > 0:
                    self.log_message(f"⚠️ С ошибками: {error_files}")
                
                # Предлагаем перезапустить лаунчер
                self.app.after(100, lambda: self.show_restart_prompt())
            else:
                self.log_message("ℹ️ Все файлы уже актуальны. Обновлений не требуется.")
                
        except Exception as e:
            self.log_message(f"❌ Ошибка обновления: {str(e)}")

    def update_readme_from_github(self, session, repo_url, branch):
        """Обновляет README файл если есть изменения"""
        try:
            readme_files = ["README.md", "README.txt", "readme.md"]
            
            for readme_file in readme_files:
                file_url = f"{repo_url}/{readme_file}?ref={branch}"
                response = session.get(file_url, timeout=5)
                
                if response.status_code == 200:
                    file_info = response.json()
                    content_encoded = file_info.get("content", "")
                    
                    import base64
                    content = base64.b64decode(content_encoded).decode('utf-8')
                    
                    local_path = os.path.join(self.system_dir, "README_GITHUB.txt")
                    with open(local_path, 'w', encoding='utf-8') as f:
                        f.write(f"# ОБНОВЛЕНИЕ ИЗ GITHUB\n\n")
                        f.write(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                        f.write(f"Репо: https://github.com/verblud1/AutoFormFiller\n\n")
                        f.write(content)
                    
                    self.log_message(f"📄 Обновлен файл README_GITHUB.txt")
                    break
                    
        except:
            pass  # Игнорируем ошибки с README

    def show_restart_prompt(self):
        """Показывает предложение перезапустить лаунчер"""
        response = messagebox.askyesno(
            "Обновление завершено",
            f"Файлы успешно обновлены из GitHub!\n\n"
            f"Для применения изменений требуется перезапуск лаунчера.\n\n"
            f"Перезапустить сейчас?"
        )
        
        if response:
            # Перезапускаем лаунчер
            python = sys.executable
            script = os.path.join(self.system_dir, "family_system_launcher.py")
            
            # Запускаем новый процесс
            if platform.system() == "Windows":
                subprocess.Popen([python, script])
            else:
                subprocess.Popen(["python3", script])
            
            # Закрываем текущий
            self.app.quit()

    def launch_database(self):
        """Запускает клиент базы данных"""
        try:
            if platform.system() == "Windows":
                script_path = os.path.join(self.system_dir, "database_client.bat")
                if not os.path.exists(script_path):
                    # Создаем bat файл для Windows
                    self.create_windows_bat_file()
            else:  # Linux/RedOS
                script_path = os.path.join(self.system_dir, "database_client.sh")
            
            if not os.path.exists(script_path):
                messagebox.showerror("Ошибка", "Файл клиента базы данных не найден!")
                return
            
            self.log_message("🚀 Запускаю клиент базы данных...")
            
            if platform.system() == "Windows":
                subprocess.Popen([script_path], shell=True)
            else:
                subprocess.Popen(["bash", script_path])
            
            self.log_message("✅ Клиент базы данных запущен")
            
        except Exception as e:
            self.log_message(f"❌ Ошибка запуска: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось запустить клиент базы данных:\n{str(e)}")
    
    def create_windows_bat_file(self):
        """Создает bat файл для запуска базы данных на Windows"""
        bat_path = os.path.join(self.system_dir, "database_client.bat")
        
        with open(bat_path, 'w', encoding='cp1251') as f:
            f.write("""@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    КЛИЕНТ БАЗЫ ДАННЫХ ДЛЯ WINDOWS
echo ========================================
echo.

set "SCRIPT_DIR=%%~dp0"
set "CONFIG_FILE=%%SCRIPT_DIR%%config.env"
set "LOG_FILE=%%SCRIPT_DIR%%connection_windows.log"

echo [%%date%% %%time%%] - Запуск клиента базы данных >> "%%LOG_FILE%%"

REM Проверка конфигурации
if not exist "%%CONFIG_FILE%%" (
   echo ❌ Файл конфигурации не найден: %%CONFIG_FILE%%
   echo Создайте config.env со следующим содержимым:
   echo SSH_HOST="192.168.10.59"
   echo SSH_USER="sshuser"
   echo SSH_PASSWORD="orsd321"
   echo LOCAL_PORT="8080"
   echo REMOTE_HOST="172.30.1.18"
   echo REMOTE_PORT="80"
   echo WEB_PATH="/aspnetkp/common/FindInfo.aspx"
   pause
   exit /b 1
)

REM Чтение конфигурации
for /f "usebackq tokens=1,2 delims==" %%%%i in ("%%CONFIG_FILE%%") do (
   set "%%%%i=%%%%j"
)

REM Остановка старых подключений
echo 🔄 Останавливаю старые подключения...
taskkill /F /FI "WINDOWTITLE eq SSH_TUNNEL*" 2>nul
taskkill /F /IM plink.exe 2>nul
timeout /t 2 /nobreak >nul

REM Проверка наличия plink (PuTTY)
where plink >nul 2>nul
if errorlevel 1 (
   echo ❌ Не найден plink.exe (PuTTY)
   echo Скачайте PuTTY с: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
   echo И поместите plink.exe в папку с программой
   pause
   exit /b 1
)

echo 🚀 Запускаю подключение к базе данных...
echo [%%date%% %%time%%] - Запуск туннеля: plink -ssh %%SSH_USER%%@%%SSH_HOST%% -pw %%SSH_PASSWORD%% -L %%LOCAL_PORT%%:%%REMOTE_HOST%%:%%REMOTE_PORT%% -N >> "%%LOG_FILE%%"

REM Запуск туннеля в отдельном окне
start "SSH_TUNNEL_%%LOCAL_PORT%%" plink -ssh %%SSH_USER%%@%%SSH_HOST%% -pw %%SSH_PASSWORD%% -L %%LOCAL_PORT%%:%%REMOTE_HOST%%:%%REMOTE_PORT%% -N

timeout /t 5 /nobreak >nul

REM Проверка запуска
tasklist /FI "WINDOWTITLE eq SSH_TUNNEL*" 2>nul | find /i "plink" >nul
if errorlevel 1 (
   echo ❌ Не удалось запустить туннель
   echo [%%date%% %%time%%] - Ошибка запуска туннеля >> "%%LOG_FILE%%"
   pause
   exit /b 1
)

echo ✅ Туннель запущен на порту %%LOCAL_PORT%%

REM Открытие браузера
echo 🌐 Открываю браузер...
start http://localhost:%%LOCAL_PORT%%%%WEB_PATH%%

echo.
echo ========================================
echo    КЛИЕНТ БАЗЫ ДАННЫХ ЗАПУЩЕН
echo ========================================
echo.
echo 🌐 Адрес: http://localhost:%%LOCAL_PORT%%%%WEB_PATH%%
echo 📋 Лог: %%LOG_FILE%%
echo.
echo Нажмите любую клавишу для остановки...
pause >nul

REM Остановка туннеля
echo 🛑 Останавливаю туннель...
taskkill /F /FI "WINDOWTITLE eq SSH_TUNNEL*" 2>nul
echo [%%date%% %%time%%] - Туннель остановлен >> "%%LOG_FILE%%"
echo ✅ Туннель остановлен

pause
""")
        
        self.log_message("📄 Создан полноценный bat файл для Windows")
    
    def run(self):
        """Запускает приложение"""
        self.app.mainloop()

if __name__ == "__main__":
    launcher = FamilySystemLauncher()
    launcher.run()