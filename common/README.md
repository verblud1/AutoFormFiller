# Модуль common

## Назначение
Общие GUI компоненты, используемые во всех модулях проекта.

## Модули

### `gui_components.py`
```python
class BaseGUI:
    """Базовый класс для GUI приложений."""
    
    def __init__(self):
        """Инициализация базового GUI."""
    
    def setup_base_ui(self) -> None:
        """Настройка базового пользовательского интерфейса."""
    
    def setup_mouse_wheel_binding(self) -> None:
        """Привязка прокрутки колесиком мыши."""
    
    def _on_mousewheel(self, event) -> None:
        """Обработка события прокрутки колесиком мыши."""
    
    def create_income_field(self, parent, label: str, key: str):
        """Создание поля для ввода дохода."""
    
    def log_message(self, message: str, log_widget=None) -> None:
        """Добавление сообщения в лог."""
    
    def on_closing(self) -> None:
        """Обработка закрытия программы."""
```

## Наследование
Другие GUI классы наследуются от `BaseGUI`:
- `JSONFamilyCreatorGUI` (family_creator/gui.py)
- `MassFamilyProcessorGUI` (mass_processor/core.py)
- `LauncherGUI` (launcher/gui_components.py) - не наследуется, использует композицию

## Особенности
- Тёмная тема оформления
- Поддержка прокрутки колесиком мыши
- Базовые методы логирования и обработки событий