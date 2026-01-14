# Примеры использования Google Sheets интеграции

## Автоматическое сохранение и подстановка ID таблицы и названия листа

Для автоматического сохранения и подстановки ID таблицы и названия листа используется модуль `config_manager`.

### Сохранение ID таблицы

```bash
python examples/save_spreadsheet_id.py
```

Этот скрипт сохранит ID таблицы `1REAUDJZCLqu7Vn_UcIGiVG9CqPWpNnGrD-luCIrDz2c` для листа "АСП_Многодетные" в конфигурационный файл `config/app_config.json`.

### Сохранение названия листа

```bash
python examples/save_sheet_name_example.py
```

Этот скрипт сохранит название листа "Список граждан (Лист 1)" для оригинального названия "АСП_Многодетные" в конфигурационный файл `config/app_config.json`.

### Использование автоматической подстановки ID и названия листа с подтверждением

Функция `get_both_ids_with_confirmation()` в модуле `utils.google_sheets_handler` автоматически:

1. Проверяет наличие сохраненного ID таблицы и названия листа в конфигурации
2. Если значения найдены, показывает их пользователю
3. Предлагает пользователю подтвердить использование этих данных или ввести новые
4. При необходимости сохраняет новые значения в конфигурацию

### Пример использования

```python
from utils.google_sheets_handler import interactive_check_existing_colors_and_highlight_with_auto_config

success = interactive_check_existing_colors_and_highlight_with_auto_config(
    credentials_file="your_credentials.json",
    json_file_path="path/to/families.json",
    sheet_name="АСП_Многодетные"
)
```

После первого запуска, ID таблицы и название листа будут сохранены в конфигурацию и использоваться автоматически в последующих запусках с возможностью проверки и корректировки пользователем.