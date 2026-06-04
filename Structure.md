
## Архитектурный анализ проекта AutoFormFiller

### 1. Основные слои логики

**Слой 1: Точки входа (Entry Points)**
- [`main.py`](main.py:1) - корневой launcher
- [`launcher/launcher.py`](launcher/launcher.py:18) - `FamilySystemLauncher` (координатор)
- [`family_creator/main.py`](family_creator/main.py:1) - `JSONFamilyCreatorGUI`
- [`mass_processor/main.py`](mass_processor/main.py:1) - `MassFamilyProcessorGUI`

**Слой 2: UI (CustomTkinter)**
- [`common/gui_components.py`](common/gui_components.py:19) - `BaseGUI` (базовые UI компоненты)
- [`launcher/gui_components.py`](launcher/gui_components.py:15) - `LauncherGUI`
- [`family_creator/gui.py`](family_creator/gui.py:38) - `JSONFamilyCreatorGUI` (2786 строк - нарушение SRP)
- [`mass_processor/core.py`](mass_processor/core.py:27) - `MassFamilyProcessorGUI`

**Слой 3: Бизнес-логика (Domain/Logic)**
- [`utils/family_processor.py`](utils/family_processor.py:10) - `FamilyDataProcessor`
- [`family_creator/json_generator.py`](family_creator/json_generator.py:11) - `JSONFamilyCreator`

**Слой 4: Data/IO**
- [`utils/data_processing.py`](utils/data_processing.py:1) - функции очистки данных
- [`utils/excel_utils.py`](utils/excel_utils.py:1) - работа с Excel
- [`utils/file_utils.py`](utils/file_utils.py:1) - работа с файлами
- [`utils/validation.py`](utils/validation.py:1) - валидация
- [`utils/mothers_exporter.py`](utils/mothers_exporter.py:1) - экспорт ФИО матерей

**Слой 5: Инфраструктура**
- [`launcher/statistics_manager.py`](launcher/statistics_manager.py:12) - статистика
- [`launcher/github_manager.py`](launcher/github_manager.py) - обновления
- [`utils/config_manager.py`](utils/config_manager.py:9) - конфигурация

### 2. Потенциально изолированные/избыточные модули

| Модуль | Статус | Рекомендация |
|--------|--------|--------------|
| [`utils/config_manager.py`](utils/config_manager.py:9) | **Не используется** | Можно удалить. Дублирует функционал `utils/file_utils.py` (функции `load_config`, `save_config`). В примерах кода (README) используется, но не импортируется в продакшен. |
| [`utils/mothers_exporter.py`](utils/mothers_exporter.py:1) | **Изолирован** | Можно вынести в отдельный инструмент или удалить. Не импортируется ни в один модуль. Выполняет специфичную задачу экспорта. |
| [`launcher/statistics_manager.py`](launcher/statistics_manager.py:12) | **Дублирует** | Избыточен. Аналогичный функционал есть в `mass_processor/core.py` (методы `load_statistics`, `save_statistics`, `update_statistics`, `get_statistics_for_period`). |
| [`utils/family_processor_fixed.py`](utils/family_processor_fixed.py) | **Не существует** | Файл отсутствует, но упомянут в открытых табах. Нужно проверить, используется ли. |
| `test_*.py` файлы | **Тестовые** | Можно вынести в `tests/` или удалить из продакшена. |

