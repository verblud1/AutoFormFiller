#!/usr/bin/env python3
"""Скрипт для отладки цветов ячеек в Excel файле"""

import openpyxl


def debug_cell_colors(file_path):
    """Отладка цветов ячеек в файле"""
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    print(f"Отладка цветов ячеек в файле: {file_path}")
    print("="*50)
    
    for row in ws.iter_rows(min_row=1, max_row=5, min_col=1, max_col=5):
        for cell in row:
            print(f"Ячейка {cell.coordinate}: значение='{cell.value}'")
            print(f"  - fill.type: {getattr(cell.fill, 'type', 'Нет атрибута type')}")
            print(f"  - fill.fill_type: {getattr(cell.fill, 'fill_type', 'Нет атрибута fill_type')}")
            print(f"  - fill: {cell.fill}")
            print(f"  - fill.__class__: {cell.fill.__class__}")
            
            # Проверяем атрибуты цвета
            if hasattr(cell.fill, 'start_color'):
                print(f"  - start_color: {cell.fill.start_color}")
                print(f"    - start_color.rgb: {getattr(cell.fill.start_color, 'rgb', 'Нет атрибута rgb')}")
            if hasattr(cell.fill, 'end_color'):
                print(f"  - end_color: {cell.fill.end_color}")
                print(f"    - end_color.rgb: {getattr(cell.fill.end_color, 'rgb', 'Нет атрибута rgb')}")
            if hasattr(cell.fill, 'fgColor'):
                print(f"  - fgColor: {cell.fill.fgColor}")
                print(f"    - fgColor.rgb: {getattr(cell.fill.fgColor, 'rgb', 'Нет атрибута rgb')}")
            if hasattr(cell.fill, 'bgColor'):
                print(f"  - bgColor: {cell.fill.bgColor}")
                print(f"    - bgColor.rgb: {getattr(cell.fill.bgColor, 'rgb', 'Нет атрибута rgb')}")
            
            print("-" * 30)


if __name__ == "__main__":
    debug_cell_colors("test_colored_file.xlsx")