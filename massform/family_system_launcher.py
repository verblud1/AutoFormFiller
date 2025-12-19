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
from datetime import datetime
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
            "config.env",
            "family_system_launcher.py"  # Этот файл
        ]
        
        # Проверяем установку
        self.is_installed = os.path.exists(self.system_dir)
        
        # Настройки
        self.config = self.load_config()
        
        self.setup_ui()
        
        # Автоматически проверяем установку при запуске
        self.app.after(100, self.check_installation_status)
    
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
        for file in ["json_family_creator.py", "massform.py", "database_client.sh"]:
            file_path = os.path.join(self.system_dir, file)
            if not os.path.exists(file_path):
                missing.append(file)
        
        if missing:
            self.log_message(f"⚠️ Отсутствуют файлы: {', '.join(missing)}")
            self.btn_json.configure(state="disabled")
            self.btn_mass.configure(state="disabled")
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
echo =======================================
echo    КЛИЕНТ БАЗЫ ДАННЫХ - WINDOWS
echo =======================================
echo.

REM Проверяем конфигурацию
if not exist "config.env" (
    echo ❌ Файл конфигурации не найден!
    pause
    exit /b 1
)

echo 🚀 Запускаю подключение к базе данных...
echo.

REM Здесь должна быть логика подключения для Windows
echo ⚠️  Для Windows требуется настроить подключение вручную
echo.
echo 📚 Инструкция:
echo 1. Установите PuTTY
echo 2. Создайте SSH туннель:
echo    plink -ssh sshuser@192.168.10.59 -pw orsd321 -L 8080:172.30.1.18:80 -N
echo 3. Откройте браузер: http://localhost:8080/aspnetkp/common/FindInfo.aspx
echo.

pause
""")
        
        self.log_message("📄 Создан bat файл для Windows")
    
    def run(self):
        """Запускает приложение"""
        self.app.mainloop()

if __name__ == "__main__":
    launcher = FamilySystemLauncher()
    launcher.run()