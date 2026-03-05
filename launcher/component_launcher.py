#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Component Launcher for Family System Launcher
Handles launching of different system components
Портативный режим - использует текущую директорию
"""

import os
import sys
import platform
import subprocess
from tkinter import messagebox


class ComponentLauncher:
    def __init__(self, app_dir, log_callback=None):
        self.app_dir = app_dir
        self.log_callback = log_callback

    def launch_json_creator(self):
        """Launch JSON creator"""
        try:
            if self.log_callback:
                self.log_callback("Запускаю Создатель JSON...")
            
            # Run the family_creator module
            if platform.system() == "Windows":
                subprocess.Popen([sys.executable, "-m", "family_creator.main"],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, "-m", "family_creator.main"])
            
            if self.log_callback:
                self.log_callback("Создатель JSON запущен")
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Ошибка запуска: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось запустить Создатель JSON:\n{str(e)}")

    def launch_mass_processor(self):
        """Launch mass processor"""
        try:
            if self.log_callback:
                self.log_callback("Запускаю Массовый обработчик...")
            
            # Run the mass_processor module
            if platform.system() == "Windows":
                subprocess.Popen([sys.executable, "-m", "mass_processor.main"],
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, "-m", "mass_processor.main"])
            
            if self.log_callback:
                self.log_callback("Массовый обработчик запущен")
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Ошибка запуска: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось запустить Массовый обработчик:\n{str(e)}")

    def launch_database(self):
        """Launch database client"""
        try:
            if platform.system() == "Windows":
                script_path = os.path.join(self.app_dir, "database_client.bat")
                if not os.path.exists(script_path):
                    # Create bat file for Windows
                    self.create_windows_bat_file()
            else:  # Linux/RedOS
                script_path = os.path.join(self.app_dir, "database_client.sh")
            
            if not os.path.exists(script_path):
                messagebox.showerror("Ошибка", "Файл клиента базы данных не найден!")
                return
            
            if self.log_callback:
                self.log_callback("Запускаю клиент базы данных...")
            
            if platform.system() == "Windows":
                subprocess.Popen([script_path], shell=True)
            else:
                subprocess.Popen(["bash", script_path])
            
            if self.log_callback:
                self.log_callback("Клиент базы данных запущен")
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Ошибка запуска: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось запустить клиент базы данных:\n{str(e)}")
    
    def create_windows_bat_file(self):
        """Create bat file for Windows database client"""
        bat_path = os.path.join(self.app_dir, "database_client.bat")
        
        with open(bat_path, 'w', encoding='cp1251') as f:
            f.write("""@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    КЛИЕНТ БАЗЫ ДАННЫХ ДЛЯ WINDOWS
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "CONFIG_FILE=%SCRIPT_DIR%config.env"
set "LOG_FILE=%SCRIPT_DIR%connection_windows.log"

echo [%date% %time%] - Запуск клиента базы данных >> "%LOG_FILE%"

REM Проверка конфигурации
if not exist "%CONFIG_FILE%" (
   echo ❌ Файл конфигурации не найден: %CONFIG_FILE%
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
for /f "usebackq tokens=1,2 delims==" %%i in ("%CONFIG_FILE%") do (
   set "%%i=%%j"
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
echo [%date% %time%] - Запуск туннеля: plink -ssh %SSH_USER%@%SSH_HOST% -pw %SSH_PASSWORD% -L %LOCAL_PORT%:%REMOTE_HOST%:%REMOTE_PORT% -N >> "%LOG_FILE%"

REM Запуск туннеля в отдельном окне
start "SSH_TUNNEL_%LOCAL_PORT%" plink -ssh %SSH_USER%@%SSH_HOST% -pw %SSH_PASSWORD% -L %LOCAL_PORT%:%REMOTE_HOST%:%REMOTE_PORT% -N

timeout /t 5 /nobreak >nul

REM Проверка запуска
tasklist /FI "WINDOWTITLE eq SSH_TUNNEL*" 2>nul | find /i "plink" >nul
if errorlevel 1 (
   echo ❌ Не удалось запустить туннель
   echo [%date% %time%] - Ошибка запуска туннеля >> "%LOG_FILE%"
   pause
   exit /b 1
)

echo ✅ Туннель запущен на порту %LOCAL_PORT%

REM Открытие браузера
echo 🌐 Открываю браузер...
start http://localhost:%LOCAL_PORT%%WEB_PATH%

echo.
echo ========================================
echo    КЛИЕНТ БАЗЫ ДАННЫХ ЗАПУЩЕН
echo ========================================
echo.
echo 🌐 Адрес: http://localhost:%LOCAL_PORT%%WEB_PATH%
echo 📋 Лог: %LOG_FILE%
echo.
echo Нажмите любую клавишу для остановки...
pause >nul

REM Остановка туннеля
echo 🛑 Останавливаю туннель...
taskkill /F /FI "WINDOWTITLE eq SSH_TUNNEL*" 2>nul
echo [%date% %time%] - Туннель остановлен >> "%LOG_FILE%"
echo ✅ Туннель остановлен

pause
""")
        
        if self.log_callback:
            self.log_callback("Создан bat-файл для Windows")

    def open_system_folder(self):
        """Open system folder (app directory)"""
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(self.app_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", self.app_dir])
            else:  # Linux
                subprocess.call(["xdg-open", self.app_dir])
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Ошибка открытия папки: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось открыть папку системы:\n{str(e)}")
