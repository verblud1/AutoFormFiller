#!/usr/bin/env python3
"""Скрипт для сортировки Excel файла по цветам ячеек"""

import argparse
import sys
import os
from pathlib import Path

# Добавляем директорию проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(__file__))

from utils.color_sorter import sort_excel_by_colors, print_color_summary


def main():
    parser = argparse.ArgumentParser(
        description='Сортировка Excel файла по цветам ячеек'
    )
    parser.add_argument(
        'input_file',
        help='Путь к входному Excel файлу'
    )
    parser.add_argument(
        '-o', '--output',
        help='Путь к выходному файлу (по умолчанию: sorted_by_colors.xlsx)',
        default='sorted_by_colors.xlsx'
    )
    parser.add_argument(
        '-s', '--sheet',
        help='Имя листа для обработки (по умолчанию: первый лист)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Проверяем существование входного файла
    if not os.path.exists(args.input_file):
        print(f"Ошибка: файл {args.input_file} не найден")
        sys.exit(1)
    
    # Проверяем расширение файла
    if not args.input_file.lower().endswith(('.xlsx', '.xls')):
        print(f"Ошибка: файл {args.input_file} не является Excel файлом")
        sys.exit(1)
    
    try:
        print(f"Обработка файла: {args.input_file}")
        print(f"Лист: {args.sheet if args.sheet else 'по умолчанию (первый)'}")
        
        # Выполняем сортировку по цветам
        categories = sort_excel_by_colors(
            args.input_file,
            args.output,
            args.sheet
        )
        
        # Выводим сводку
        print_color_summary(categories)
        
        print(f"\nРезультаты сохранены в '{args.output}'")
        print("\nСтатистика по категориям:")
        for color, cells in categories.items():
            status_map = {
                'red': 'Не ответили на звонок',
                'yellow': 'Занесено в базу данных',
                'green': 'Занесено в базу данных',
                'gray': 'Только позвонили, но не занесли в базу данных',
                'none': 'Еще не сделано'
            }
            
            status = status_map.get(color, 'Неизвестная категория')
            print(f"- {status}: {len(cells)} ячеек")
        
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()