# AutoFormFiller

Автоматизированное заполнение форм в системе работы с семьями.

## Архитектура проекта

```
AutoFormFiller/
├── main.py                          # Точка входа
├── common/                          # Общие GUI компоненты
│   ├── gui_components.py            # Базовый класс BaseGUI
│   └── README.md
├── family_creator/                  # Создание JSON файлов
│   ├── gui.py                       # GUI создателя семей
│   ├── json_generator.py            # Генератор JSON
│   └── README.md
├── mass_processor/                  # Массовая обработка
│   ├── core.py                      # GUI массового обработчика
│   ├── processor.py                 # Процессор семей
│   └── README.md
├── launcher/                        # Лаунчер системы
│   ├── launcher.py                  # FamilySystemLauncher
│   ├── gui_components.py            # LauncherGUI
│   ├── statistics_manager.py        # Менеджер статистики
│   ├── github_manager.py            # Обновления
│   └── README.md
├── utils/                           # Утилиты
│   ├── file_utils.py                # Работа с файлами
│   ├── statistics.py                # Статистика (унифицированный)
│   ├── data_processing.py           # Очистка данных
│   ├── validation.py                # Валидация
│   ├── excel_utils.py               # Работа с Excel
│   ├── family_processor.py          # Процессор данных
│   └── README.md
└── tools/                           # Изолированные инструменты
    ├── mothers_exporter.py          # Экспорт ФИО матерей
    └── README.md
```

## Установка

```bash
pip install -r requirements.txt
```

## Использование

```bash
python main.py
```

## Изменения

### v2.0 (Рефакторинг)
- Удалён дублирующий модуль `utils/config_manager.py`
- Перенесён `utils/mothers_exporter.py` в `tools/`
- Создан унифицированный модуль `utils/statistics.py`
- Обновлены зависимости `launcher/statistics_manager.py` и `mass_processor/core.py`
- Добавлены README.md для всех модулей