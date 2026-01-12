#!/bin/bash

echo "=== УСТАНОВКА СИСТЕМЫ ДЛЯ RED OS / LINUX ==="

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    echo "Установите: sudo dnf install python3 python3-tkinter"
    exit 1
fi

# Проверяем pip
if ! command -v pip3 &> /dev/null; then
    echo "📦 Устанавливаю pip..."
    sudo dnf install -y python3-pip || {
        echo "❌ Не удалось установить pip"
        exit 1
    }
fi

# Устанавливаем зависимости
echo "📚 Устанавливаю зависимости Python..."
pip3 install --user customtkinter selenium pandas openpyxl

# Запускаем Python установщик
echo "🚀 Запускаю установщик..."
python3 install_system.py

echo "✅ Установка завершена!"
echo "📁 Папка системы: ~/Desktop/FamilySystem/"
echo "🖱️ Ярлык: ~/Desktop/family_system.desktop"