#!/usr/bin/env python3
"""Пример использования скрипта сортировки Excel файла по цветам"""

from utils.color_sorter import sort_excel_by_colors, print_color_summary


def main():
    # Путь к входному файлу
    input_file = "АСП_Многодетные.xlsx"
    
    # Путь к выходному файлу
    output_file = "sorted_by_colors.xlsx"
    
    print("Начинаем обработку файла...")
    print(f"Входной файл: {input_file}")
    print(f"Выходной файл: {output_file}")
    
    try:
        # Выполняем сортировку по цветам
        categories = sort_excel_by_colors(input_file, output_file)
        
        # Выводим сводку
        print_color_summary(categories)
        
        print(f"\nРезультаты сохранены в '{output_file}'")
        
        # Выводим дополнительную статистику
        print("\nДетальная статистика:")
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
            
            # Показываем первые 3 ячейки для каждой категории
            if cells:
                print("  Примеры ячеек:")
                for i, cell_data in enumerate(cells[:3]):
                    print(f"    {cell_data['cell']}: {cell_data['value']}")
                if len(cells) > 3:
                    print(f"    ... и еще {len(cells) - 3} ячеек")
                print()
    
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()