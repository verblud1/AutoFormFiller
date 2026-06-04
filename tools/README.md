# Модуль tools

## Назначение
Изолированные инструменты, не входящие в основной поток продакшена.

## Модули

### `mothers_exporter.py`
```python
def extract_mothers_from_week_folder(week_folder_path: str) -> Tuple[list, int]:
    """
    Извлечение ФИО матерей из JSON файлов в папке недели.
    
    Args:
        week_folder_path: Путь к папке недели (например, 'completed/2026-W03')
    
    Returns:
        Кортеж (список ФИО матерей, общее количество семей)
    """

def export_mothers_to_txt(mothers_fio: list, output_folder: str, week_name: str, total_families_count: int) -> str:
    """
    Экспорт ФИО матерей в текстовый файл.
    
    Args:
        mothers_fio: Список ФИО матерей
        output_folder: Папка для сохранения файла
        week_name: Название недели (например, '2026-W03')
        total_families_count: Общее количество семей
    
    Returns:
        Путь к созданному файлу
    """

def select_and_export_mothers() -> None:
    """
    Основная функция для выбора папки недели и экспорта ФИО матерей.
    Запускает GUI-диалог выбора папок.
    """
```

## Использование
```bash
python tools/mothers_exporter.py
```

## Назначение
Инструмент для экспорта ФИО матерей из обработанных семей в текстовый файл. Используется для дальнейшего анализа или импорта в другие системы.