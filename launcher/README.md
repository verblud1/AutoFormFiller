# Модуль launcher

## Назначение
Единая точка входа в систему работы с семьями. Содержит лаунчер GUI и управление компонентами.

## Модули

### `launcher.py`
```python
class FamilySystemLauncher:
    """Координатор всех компонентов системы."""
    
    def __init__(self):
        """Инициализация лаунчера."""
    
    def run(self) -> None:
        """Запуск приложения."""
    
    def launch_json_creator(self) -> None:
        """Запуск создателя JSON файлов."""
    
    def launch_mass_processor(self) -> None:
        """Запуск массового обработчика."""
    
    def launch_database(self) -> None:
        """Запуск клиента базы данных."""
    
    def get_statistics_for_period(self) -> Tuple[int, int]:
        """Получение статистики за день и неделю."""
```

### `gui_components.py`
```python
class LauncherGUI:
    """GUI лаунчера на CustomTkinter."""
    
    def __init__(self, launcher_instance: FamilySystemLauncher):
        """Инициализация GUI."""
    
    def run(self) -> None:
        """Запуск интерфейса."""
    
    def log_message(self, message: str) -> None:
        """Добавление сообщения в лог."""
    
    def update_statistics_display(self) -> None:
        """Обновление отображения статистики."""
```

### `statistics_manager.py`
```python
class StatisticsManager(BaseStatisticsManager):
    """Менеджер статистики (обёртка над utils/statistics.py)."""
    
    def update(self, success_count: int) -> bool:
        """Обновление статистики с выводом сообщения."""
```

### `github_manager.py`
```python
class GitHubManager:
    """Управление обновлениями через GitHub."""
    
    def update_from_github(self) -> None:
        """Проверка и применение обновлений."""
```

### `component_launcher.py`
```python
class ComponentLauncher:
    """Запуск отдельных компонентов."""
    
    def launch_json_creator(self) -> None:
        """Запуск JSON создателя."""
    
    def launch_mass_processor(self) -> None:
        """Запуск массового обработчика."""
```

## Структура данных
- `config/` - конфигурационные файлы
- `logs/` - файлы логов
- `screenshots/` - скриншоты
