@echo off
echo Установка автоматизатора заполнения форм...
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не установлен!
    echo Установите Python с официального сайта: https://python.org
    echo Затем запустите этот файл снова.
    pause
    exit /b 1
)

echo Установка зависимостей...
pip install -r requirements.txt

if errorlevel 1 (
    echo ОШИБКА: Не удалось установить зависимости!
    pause
    exit /b 1
)

echo.
echo Установка завершена успешно!
echo Для запуска программы выполните: python auto_form_filler.py
echo.
pause