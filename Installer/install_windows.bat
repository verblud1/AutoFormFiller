@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    УСТАНОВКА СИСТЕМЫ РАБОТЫ С СЕМЬЯМИ
echo    Для Windows 7/8
echo ========================================
echo.

REM Определение директории скрипта
set "SCRIPT_DIR=%~dp0"
set "INSTALLER_DIR=%SCRIPT_DIR%..\Installer"
set "LOG_FILE=%TEMP%\family_system_install.log"

REM Логирование
echo [%date% %time%] - Начало установки >> "%LOG_FILE%"

REM Проверка Python
echo Проверка наличия Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден
    echo Установите Python 3.6 или выше
    echo [%date% %time%] - Ошибка: Python не найден >> "%LOG_FILE%"
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✅ Найден Python !PYTHON_VERSION!
    echo [%date% %time%] - Найден Python !PYTHON_VERSION! >> "%LOG_FILE%"
)

REM Проверка версии Python
for /f "tokens=1,2,3 delims=." %%a in ("!PYTHON_VERSION!") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if !MAJOR! lss 3 (
    echo ❌ Требуется Python 3.6+, у вас !PYTHON_VERSION!
    echo [%date% %time%] - Ошибка: старая версия Python >> "%LOG_FILE%"
    pause
    exit /b 1
)

if !MAJOR! equ 3 (
    if !MINOR! lss 6 (
        echo ❌ Требуется Python 3.6+, у вас !PYTHON_VERSION!
        echo [%date% %time%] - Ошибка: старая версия Python >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

REM Установка зависимостей
echo Установка зависимостей...
echo [%date% %time%] - Установка зависимостей >> "%LOG_FILE%"

python -m pip install --user selenium==3.141.0 webdriver-manager==3.8.0 >nul 2>&1
if errorlevel 1 (
    echo [%date% %time%] - Ошибка установки selenium >> "%LOG_FILE%"
    echo Повторная попытка установки...
    python -m pip install --user --upgrade --force-reinstall selenium==3.141.0 webdriver-manager==3.8.0 >nul 2>&1
    if errorlevel 1 (
        echo ❌ Ошибка установки зависимостей
        echo [%date% %time%] - Ошибка установки зависимостей >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

REM Проверка установки customtkinter
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo Установка customtkinter...
    python -m pip install --user customtkinter >nul 2>&1
    if errorlevel 1 (
        echo ⚠️ Не удалось установить customtkinter, продолжение без него
        echo [%date% %time%] - customtkinter не установлен >> "%LOG_FILE%"
    ) else (
        echo ✅ customtkinter установлен
        echo [%date% %time%] - customtkinter установлен >> "%LOG_FILE%"
    )
) else (
    echo ✅ customtkinter уже установлен
)

REM Определение пути установки
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "INSTALL_DIR=!DESKTOP_DIR!\FamilySystem"

echo Установка в: !INSTALL_DIR!
echo [%date% %time%] - Установка в !INSTALL_DIR! >> "%LOG_FILE%"

REM Создание папки установки
if not exist "!INSTALL_DIR!" (
    mkdir "!INSTALL_DIR!"
    echo ✅ Создана папка установки
)

REM Создание подпапок
mkdir "!INSTALL_DIR!\config" 2>nul
mkdir "!INSTALL_DIR!\config\logs" 2>nul
mkdir "!INSTALL_DIR!\config\screenshots" 2>nul
mkdir "!INSTALL_DIR!\config\adpi" 2>nul
mkdir "!INSTALL_DIR!\config\register" 2>nul

REM Копирование файлов
echo Копирование файлов системы...
copy /Y "!INSTALLER_DIR!\json_family_creator.py" "!INSTALL_DIR!" >nul
if not errorlevel 1 (echo ✅ json_family_creator.py скопирован) else (echo ⚠️ json_family_creator.py не найден)
copy /Y "!INSTALLER_DIR!\massform.py" "!INSTALL_DIR!" >nul
if not errorlevel 1 (echo ✅ massform.py скопирован) else (echo ⚠️ massform.py не найден)
copy /Y "!INSTALLER_DIR!\family_system_launcher.py" "!INSTALL_DIR!" >nul
if not errorlevel 1 (echo ✅ family_system_launcher.py скопирован) else (echo ⚠️ family_system_launcher.py не найден)
copy /Y "!INSTALLER_DIR!\chrome_driver_helper.py" "!INSTALL_DIR!" >nul
if not errorlevel 1 (echo ✅ chrome_driver_helper.py скопирован) else (echo ⚠️ chrome_driver_helper.py не найден)
copy /Y "!INSTALLER_DIR!\database_client.bat" "!INSTALL_DIR!" >nul
if not errorlevel 1 (echo ✅ database_client.bat скопирован) else (echo ⚠️ database_client.bat не найден)
copy /Y "!INSTALLER_DIR!\autosave_families.json" "!INSTALL_DIR!" >nul
if not errorlevel 1 (echo ✅ autosave_families.json скопирован) else (echo ⚠️ autosave_families.json не найден)

REM Копирование папки registry если она существует
if exist "!INSTALLER_DIR!\registry" (
    echo Копирование папки registry...
    xcopy /E /I /Y "!INSTALLER_DIR!\registry" "!INSTALL_DIR!\registry" >nul
    if not errorlevel 1 (echo ✅ Папка registry скопирована) else (echo ⚠️ Ошибка копирования папки registry)
) else (
    echo Папка registry не найдена - пропущена
)

REM Создание конфигурационного файла
if not exist "!INSTALL_DIR!\config.env" (
    echo Создание config.env...
    (
        echo SSH_HOST="192.168.10.59"
        echo SSH_USER="sshuser"
        echo SSH_PASSWORD="orsd321"
        echo LOCAL_PORT="8080"
        echo REMOTE_HOST="172.30.1.18"
        echo REMOTE_PORT="80"
        echo WEB_PATH="/aspnetkp/common/FindInfo.aspx"
    ) > "!INSTALL_DIR!\config.env"
    echo ✅ config.env создан
)

REM Создание ярлыка BAT
set "BAT_FILE=!DESKTOP_DIR!\Запуск_системы.bat"
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo echo Запуск системы работы с семьями...
    echo cd /D "!INSTALL_DIR!"
    echo python family_system_launcher.py
    echo pause
) > "!BAT_FILE!"

echo ✅ Ярлык создан на рабочем столе

REM Создание ярлыка LNK (если возможно)
echo [%date% %time%] - Попытка создания .lnk ярлыка >> "%LOG_FILE%"
(
    echo Set oWS = CreateObject^("WScript.Shell"^)
    echo sLinkFile = "!DESKTOP_DIR!\Система работы с семьями.lnk"
    echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
    echo oLink.TargetPath = "cmd.exe"
    echo oLink.Arguments = "/k cd /D !INSTALL_DIR! ^&^& python family_system_launcher.py"
    echo oLink.Save
) > "%TEMP%\create_shortcut.vbs"

cscript //nologo "%TEMP%\create_shortcut.vbs" >nul 2>&1
if not errorlevel 1 (
    echo ✅ .lnk ярлык создан
    echo [%date% %time%] - .lnk ярлык создан >> "%LOG_FILE%"
) else (
    echo ⚠️ Не удалось создать .lnk ярлык, используем BAT файл
    echo [%date% %time%] - .lnk ярлык не создан >> "%LOG_FILE%"
)

REM Удаление временного файла
del "%TEMP%\create_shortcut.vbs" >nul 2>&1

echo.
echo ========================================
echo    УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО
echo ========================================
echo.
echo 📁 Папка системы: !INSTALL_DIR!
echo 🚀 Запуск: !BAT_FILE!
echo 📋 Лог: %LOG_FILE%
echo.
echo Нажмите любую клавишу для запуска системы...
pause >nul

REM Запуск системы
start "Family System" cmd /k "cd /D !INSTALL_DIR! && python family_system_launcher.py"

echo [%date% %time%] - Установка завершена успешно >> "%LOG_FILE%"
pause