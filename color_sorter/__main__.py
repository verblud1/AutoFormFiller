#!/usr/bin/env python3
"""Основной модуль для запуска программы сортировки по цветам"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Основная функция запуска"""
    print("Выберите режим работы:")
    print("1. Графический интерфейс")
    print("2. Командная строка (сортировка семей)")
    print("3. Командная строка (общая сортировка ячеек)")
    
    choice = input("Введите номер (1-3) или 'q' для выхода: ").strip()
    
    if choice == '1':
        import gui_color_sorter
        gui_color_sorter.main()
    elif choice == '2':
        import argparse
        import sort_families_by_colors
        sort_families_by_colors.main()
    elif choice == '3':
        import argparse
        import sort_by_colors
        sort_by_colors.main()
    elif choice.lower() == 'q':
        print("Выход...")
        return
    else:
        print("Неверный выбор. Попробуйте снова.")
        main()


if __name__ == "__main__":
    main()