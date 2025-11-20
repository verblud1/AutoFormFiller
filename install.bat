@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Установка автоформатировщика
echo ========================================

:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не установлен или не добавлен в PATH
    echo Установите Python 3.8+ с официального сайта
    pause
    exit /b 1
)

:: Создание виртуального окружения
echo Создание виртуального окружения...
python -m venv venv
if errorlevel 1 (
    echo Ошибка создания виртуального окружения
    pause
    exit /b 1
)

:: Активация venv
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

:: Установка зависимостей
echo Установка зависимостей...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo Ошибка установки зависимостей
    pause
    exit /b 1
)

:: Определение и установка драйверов
echo Определение установленных браузеров...
python -c "
import os
import winreg
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

def find_browsers():
    browsers = []
    # Проверка Chrome
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe') as key:
            chrome_path = winreg.QueryValue(key, None)
            if os.path.exists(chrome_path):
                browsers.append(('chrome', 'Google Chrome'))
    except: pass
    
    # Проверка Yandex
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\browser.exe') as key:
            yandex_path = winreg.QueryValue(key, None)
            if os.path.exists(yandex_path):
                browsers.append(('yandex', 'Yandex Browser'))
    except: pass
    
    # Проверка Chromium
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chromium.exe') as key:
            chromium_path = winreg.QueryValue(key, None)
            if os.path.exists(chromium_path):
                browsers.append(('chromium', 'Chromium'))
    except: pass
    
    return browsers

browsers = find_browsers()
print(f'Найдены браузеры: {browsers}')

# Установка драйверов
for browser_type, browser_name in browsers:
    try:
        if browser_type == 'yandex':
            driver_path = ChromeDriverManager(chrome_type=ChromeType.YANDEX).install()
        else:
            driver_path = ChromeDriverManager(chrome_type=ChromeType.GOOGLE if browser_type == 'chrome' else ChromeType.CHROMIUM).install()
        print(f'✓ Драйвер для {browser_name} установлен: {driver_path}')
    except Exception as e:
        print(f'✗ Ошибка установки драйвера для {browser_name}: {e}')
"

echo.
echo ========================================
echo Установка завершена успешно!
echo ========================================
echo Для запуска выполните:
echo   venv\Scripts\activate
echo   python auto_form_filler.py
echo.
pause