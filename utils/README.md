# Модуль utils

## Назначение
Вспомогательные утилиты для работы с файлами, данными, валидацией и статистикой.

## Модули

### `file_utils.py`
```python
def setup_config_directory(base_dir: str) -> Tuple[str, str, str]:
    """Создание папок для конфигурации, скриншотов и логов."""

def load_config(config_file: str, default_config: dict) -> dict:
    """Загрузка конфигурации из файла."""

def save_config(config_file: str, config: dict) -> bool:
    """Сохранение конфигурации в файл."""

def find_registry_directory(start_dir: str) -> str:
    """Поиск папки registry."""

def load_last_files(register_dir: str, adpi_dir: str) -> Tuple[str, str]:
    """Загрузка последних файлов реестра и АДПИ."""
```

### `statistics.py`
```python
def load_statistics(stats_file: str) -> Dict:
    """Загрузка статистики обработки."""

def save_statistics(stats_file: str, stats: Dict) -> bool:
    """Сохранение статистики в файл."""

def update_statistics(stats: Dict, success_count: int) -> bool:
    """Обновление статистики."""

def get_statistics_for_period(stats: Dict) -> Tuple[int, int]:
    """Получение статистики за день и неделю."""

class StatisticsManager:
    """Класс-обёртка для управления статистикой."""
    
    def __init__(self, config_dir: str):
        """Инициализация с путём к директории конфигурации."""
    
    def load(self) -> Dict:
        """Загрузка статистики."""
    
    def save(self) -> bool:
        """Сохранение статистики."""
    
    def update(self, success_count: int) -> bool:
        """Обновление статистики."""
    
    def get_for_period(self) -> Tuple[int, int]:
        """Получение статистики за период."""
```

### `data_processing.py`
```python
def clean_string(value: str) -> str:
    """Очистка строки от лишних пробелов."""

def clean_fio(value: str) -> str:
    """Нормализация ФИО (замена ё на е)."""

def clean_date(value: str) -> str:
    """Очистка даты."""

def clean_phone(value: str) -> str:
    """Очистка номера телефона."""

def clean_family_data(data: dict) -> dict:
    """Очистка всех полей семьи."""
```

### `validation.py`
```python
def validate_family_data(data: dict) -> Tuple[bool, str]:
    """Валидация данных семьи."""
```

### `excel_utils.py`
```python
def load_register_file(file_path: str) -> pd.DataFrame:
    """Загрузка файла реестра."""

def load_adpi_file(file_path: str) -> pd.DataFrame:
    """Загрузка файла АДПИ."""

def parse_adpi_date(date_str: str) -> str:
    """Парсинг даты из АДПИ."""

def normalize_fio(fio: str) -> str:
    """Нормализация ФИО для сравнения."""

def is_fio_similar(fio1: str, fio2: str) -> bool:
    """Проверка совпадения ФИО с нормализацией."""
```

### `family_processor.py`
```python
class FamilyDataProcessor:
    """Процессор данных семей."""
    
    def process_family(self, data: dict) -> dict:
        """Обработка данных семьи."""
```

## Структура данных статистики
```python
{
    'daily': {
        '2026-06-04': 150,  # количество обработанных семей за день
        ...
    },
    'weekly': {
        '2026-W23': 850,  # количество обработанных семей за неделю
        ...
    }
}