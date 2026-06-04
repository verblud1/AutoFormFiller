# Модуль mass_processor

## Назначение
Массовая обработка семей через автоматизацию браузера (Selenium).

## Модули

### `core.py`
```python
class MassFamilyProcessorGUI(BaseGUI):
    """Главный класс массового обработчика семей."""
    
    def __init__(self):
        """Инициализация GUI и подключение к базе данных."""
    
    def setup_ui(self) -> None:
        """Настройка пользовательского интерфейса."""
    
    def load_json(self, file_path: str = None) -> None:
        """Загрузка семей из JSON файла."""
    
    def start_processing(self) -> None:
        """Начало обработки семей."""
    
    def process_families(self) -> None:
        """Основной цикл обработки семей (в потоке)."""
    
    def process_single_family_with_retry(self, family_data: dict, family_number: int) -> bool:
        """Обработка одной семьи с повторными попытками."""
    
    def log_message(self, message: str) -> None:
        """Добавление сообщения в лог."""
```

### `processor.py`
```python
class FamilyProcessor:
    """Процессор для обработки отдельных семей."""
    
    def process(self, family_data: dict) -> bool:
        """Обработка данных семьи."""
```

## Поток обработки
1. Загрузка JSON файла с семьями
2. Выбор стартовой семьи
3. Подключение к базе данных через Selenium
4. Автоматическое заполнение форм
5. Сохранение результатов
6. Обновление статистики

## Требования
- Установленный Chrome/Chromium браузер
- ChromeDriver
- Подключение к базе данных (локальный сервер)