@echo off
chcp 65001 >nul
echo =======================================
echo    УСТАНОВКА СИСТЕМЫ ДЛЯ WINDOWS
echo =======================================
echo.

echo 🔍 Проверяю Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен
    echo 📥 Скачайте с: https://www.python.org/downloads/
    echo 💡 При установке отметьте "Add Python to PATH"
    pause
    exit /b 1
)

echo 📦 Проверяю pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ pip не найден, обновляю Python...
    python -m ensurepip --upgrade
)

echo 📚 Устанавливаю зависимости...
pip install customtkinter selenium pandas openpyxl

echo 🚀 Запускаю установщик...
python install_system.py

echo.
echo ✅ Установка завершена!
echo 📁 Папка системы: %USERPROFILE%\Desktop\FamilySystem\
echo 🖱️ Ярлык: %USERPROFILE%\Desktop\Система работы с семьями.lnk
pause