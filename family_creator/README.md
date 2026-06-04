# Модуль family_creator

## Назначение
Создание и редактирование JSON файлов с данными семей.

## Модули

### `gui.py`
```python
class JSONFamilyCreatorGUI(BaseGUI):
    """Главный класс GUI для создания JSON файлов семей."""
    
    def __init__(self):
        """Инициализация GUI."""
    
    def setup_ui(self) -> None:
        """Настройка пользовательского интерфейса."""
    
    def load_register_file(self) -> None:
        """Загрузка файла реестра."""
    
    def load_adpi_file(self) -> None:
        """Загрузка файла АДПИ."""
    
    def add_family(self) -> None:
        """Добавление новой семьи."""
    
    def save_json(self) -> None:
        """Сохранение JSON файла."""
    
    def log_message(self, message: str) -> None:
        """Добавление сообщения в лог."""
```

### `json_generator.py`
```python
class JSONFamilyCreator:
    """Генератор JSON файлов с семьями."""
    
    def __init__(self):
        """Инициализация генератора."""
    
    def add_family(self, data: dict) -> None:
        """Добавление семьи в список."""
    
    def save_to_file(self, file_path: str) -> bool:
        """Сохранение в JSON файл."""
    
    def load_from_file(self, file_path: str) -> bool:
        """Загрузка из JSON файла."""
```

## Структура JSON файла
```json
[
    {
        "mother_fio": "Иванова Мария Петровна",
        "mother_birth": "01.01.1980",
        "mother_work": "Работает",
        "father_fio": "Иванов Петр Сергеевич",
        "father_birth": "15.05.1978",
        "children": [
            {"fio": "Иванов Алексей", "birth": "10.03.2010", "education": "Школьник"}
        ],
        "rooms": "3",
        "square": "75",
        "amenities": "со всеми удобствами",
        "ownership": "собственная",
        "address": "г. Москва, ул. Ленина, д. 1",
        "phone": "+79001234567",
        "incomes": {
            "mother_salary": "50000",
            "unified_benefit": "15000"
        },
        "adpi": "да",
        "install_date": "01.01.2024",
        "check_date": "01.06.2024"
    }
]