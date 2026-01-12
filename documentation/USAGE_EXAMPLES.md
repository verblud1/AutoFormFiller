# Примеры использования AutoFormFiller

## Содержание

1. [Базовое использование](#базовое-использование)
2. [Создание JSON файлов](#создание-json-файлов)
3. [Массовая обработка](#массовая-обработка)
4. [Работа с Excel файлами](#работа-с-excel-файлами)
5. [Обработка ошибок](#обработка-ошибок)
6. [Примеры кода](#примеры-кода)

## Базовое использование

### Запуск приложения

```bash
# Запуск лаунчера (рекомендуемый способ)
python main.py

# Запуск в режиме создателя JSON файлов
python main.py --mode creator

# Запуск в режиме массового обработчика
python main.py --mode processor
```

### Запуск конкретного компонента

```python
# Запуск создателя JSON файлов
from family_creator.main import main as creator_main
creator_main()

# Запуск массового обработчика
from mass_processor.main import main as processor_main
processor_main()
```

## Создание JSON файлов

### Создание новой семьи

```python
from family_creator.json_generator import JSONFamilyCreator

# Создание экземпляра генератора
creator = JSONFamilyCreator()

# Подготовка данных семьи
family_data = {
    "mother_fio": "Иванова Анна Петровна",
    "mother_birth": "15.03.1990",
    "mother_work": "ООО Ромашка",
    "mother_disability_care": False,
    "mother_not_working": False,
    "father_fio": "Иванов Петр Александрович",
    "father_birth": "20.06.1988",
    "father_work": "ООО Ландыш",
    "father_not_working": False,
    "children": [
        {
            "fio": "Иванов Михаил Петрович",
            "birth": "10.05.2015",
            "education": "Школа №1"
        }
    ],
    "phone_number": "79123456789",
    "address": "г. Москва, ул. Ленина, д. 1",
    "rooms": "2",
    "square": "45",
    "amenities": "со всеми удобствами",
    "ownership": "в собственности",
    "adpi": "нет",
    "install_date": "",
    "check_date": "",
    "incomes": {
        "mother_salary": "25000",
        "father_salary": "30000",
        "unified_benefit": "12000",
        "large_family_benefit": "1900"
    }
}

# Добавление семьи в список
creator.add_family(family_data)

# Сохранение в JSON файл
creator.save_to_json("families.json")
```

### Загрузка и редактирование JSON файла

```python
from family_creator.json_generator import JSONFamilyCreator

# Загрузка существующего файла
creator = JSONFamilyCreator()
success = creator.load_from_json("existing_families.json")

if success:
    # Добавление новой семьи
    new_family = {
        # ... данные семьи ...
    }
    creator.add_family(new_family)
    
    # Сохранение изменений
    creator.save_to_json("updated_families.json")
```

## Массовая обработка

### Инициализация обработчика

```python
from mass_processor.processor import MassFamilyProcessor

# Создание экземпляра обработчика
processor = MassFamilyProcessor(
    pause=0.5,  # Пауза между обработкой семей (в секундах)
    screenshot=True,  # Делать ли скриншоты
    screenshot_dir="./screenshots",  # Папка для скриншотов
    stop_on_error=True  # Останавливаться при ошибке
)

# Загрузка JSON файла с семьями
processor.load_json_file("families.json")

# Запуск обработки
processor.start_processing()
```

### Обработка отдельной семьи

```python
from mass_processor.processor import MassFamilyProcessor

processor = MassFamilyProcessor()

# Подготовка данных семьи
family_data = {
    # ... данные семьи в формате JSON ...
}

# Обработка одной семьи
success = processor.process_single_family(family_data, family_number=1)

if success:
    print("Семья успешно обработана")
else:
    print("Ошибка при обработке семьи")
```

## Работа с Excel файлами

### Загрузка реестра многодетных

```python
from utils.excel_utils import load_register_file

# Загрузка файла реестра
register_data = load_register_file("register.xlsx")

# Просмотр загруженных данных
for family_fio, family_info in register_data.items():
    print(f"Семья: {family_fio}")
    print(f"Адрес: {family_info['address']}")
    print(f"Дети: {len(family_info['children'])}")
    print("---")
```

### Загрузка данных АДПИ

```python
from utils.excel_utils import load_adpi_file

# Загрузка файла АДПИ
adpi_data = load_adpi_file("adpi.xlsx")

# Просмотр загруженных данных
for fio, adpi_info in adpi_data.items():
    print(f"ФИО: {fio}")
    print(f"Адрес: {adpi_info['address']}")
    print(f"Дата установки: {adpi_info['install_date']}")
    print(f"Дата проверки: {adpi_info['check_date']}")
    print("---")
```

### Автоопределение семьи из реестра

```python
from utils.family_processor import FamilyDataProcessor

processor = FamilyDataProcessor()

# Загрузка файлов реестра и АДПИ
processor.load_register_file("register.xlsx")
processor.load_adpi_file("adpi.xlsx")

# Автоопределение семьи по ФИО
mother_fio = "Иванова Анна Петровна"
result = processor.auto_detect_family(mother_fio)

if result:
    print(f"Найдена семья: {result['mother_fio']}")
    print(f"Адрес: {result['address']}")
    print(f"Телефон: {result['phone']}")
else:
    print("Семья не найдена")
```

## Обработка ошибок

### Обработка ошибок валидации

```python
from utils.validation import validate_family_data

family_data = {
    # ... данные семьи ...
}

errors = validate_family_data(family_data)

if errors:
    print("Найдены ошибки валидации:")
    for error in errors:
        print(f"- {error}")
else:
    print("Данные прошли валидацию")
```

### Обработка ошибок загрузки файлов

```python
from family_creator.json_generator import JSONFamilyCreator

creator = JSONFamilyCreator()

try:
    success = creator.load_from_json("nonexistent_file.json")
    if not success:
        print("Не удалось загрузить файл")
except FileNotFoundError:
    print("Файл не найден")
except json.JSONDecodeError as e:
    print(f"Ошибка парсинга JSON: {e}")
except Exception as e:
    print(f"Неизвестная ошибка: {e}")
```

### Обработка ошибок при автоматизации

```python
from mass_processor.processor import MassFamilyProcessor

processor = MassFamilyProcessor(stop_on_error=False)

try:
    processor.start_processing()
except KeyboardInterrupt:
    print("Обработка прервана пользователем")
    processor.stop_processing()
except Exception as e:
    print(f"Критическая ошибка: {e}")
    processor.stop_processing()
```

## Примеры кода

### Полный пример создания и обработки JSON файла

```python
import json
from family_creator.json_generator import JSONFamilyCreator
from mass_processor.processor import MassFamilyProcessor

def create_and_process_families():
    # 1. Создание JSON файла с семьями
    creator = JSONFamilyCreator()
    
    # Подготовка данных для нескольких семей
    families = [
        {
            "mother_fio": "Иванова Анна Петровна",
            "mother_birth": "15.03.1990",
            "children": [
                {"fio": "Иванов Михаил Петрович", "birth": "10.05.2015", "education": "Школа №1"}
            ],
            # ... другие данные ...
        },
        {
            "mother_fio": "Петрова Мария Сергеевна",
            "mother_birth": "22.07.1985",
            "children": [
                {"fio": "Петров Алексей Михайлович", "birth": "05.12.2010", "education": "Школа №5"},
                {"fio": "Петрова Екатерина Михайловна", "birth": "18.03.2012", "education": "Школа №5"}
            ],
            # ... другие данные ...
        }
    ]
    
    # Добавление семей в создатель
    for family in families:
        creator.add_family(family)
    
    # Сохранение в JSON файл
    creator.save_to_json("sample_families.json")
    print("JSON файл создан: sample_families.json")
    
    # 2. Загрузка и обработка файла
    processor = MassFamilyProcessor(
        pause=1.0,
        screenshot=True,
        screenshot_dir="./screenshots",
        stop_on_error=False
    )
    
    # Загрузка файла
    processor.load_json_file("sample_families.json")
    
    # Запуск обработки
    print("Начинаем обработку семей...")
    processor.start_processing()
    
    print("Обработка завершена!")

if __name__ == "__main__":
    create_and_process_families()
```

### Пример использования утилитарных функций

```python
from utils.data_processing import (
    clean_fio, clean_date, clean_phone, clean_address,
    clean_string, clean_numeric_field
)
from utils.validation import validate_date, validate_phone, validate_number

# Очистка данных
raw_fio = "  иванова    аННА   петровна  "
cleaned_fio = clean_fio(raw_fio)
print(f"Очищенное ФИО: {cleaned_fio}")  # "Иванова Анна Петровна"

raw_date = "28.12.202026"
cleaned_date = clean_date(raw_date)
print(f"Очищенная дата: {cleaned_date}")  # "28.12.2020"

raw_phone = "+7 (912) 345-67-89"
cleaned_phone = clean_phone(raw_phone)
print(f"Очищенный телефон: {cleaned_phone}")  # "79123456789"

# Валидация данных
is_valid_date = validate_date("15.03.1990")
print(f"Дата корректна: {is_valid_date}")  # True

is_valid_phone = validate_phone("79123456789")
print(f"Телефон корректен: {is_valid_phone}")  # True

is_valid_number = validate_number("25000")
print(f"Число корректно: {is_valid_number}")  # True
```

### Пример работы с GUI компонентами

```python
import customtkinter as ctk
from common.gui_components import BaseGUI

class MyFamilyApp(BaseGUI):
    def __init__(self):
        super().__init__()
        self.app.title("Мое приложение для работы с семьями")
        self.app.geometry("800x600")
        
        # Создание вкладок
        self.setup_tabs()
        
        # Настройка обработки закрытия
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_tabs(self):
        """Настройка вкладок приложения"""
        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.family_tab = self.tabview.add("Семьи")
        self.settings_tab = self.tabview.add("Настройки")
        self.logs_tab = self.tabview.add("Логи")
        
        # Настройка каждой вкладки
        self.setup_family_tab()
        self.setup_settings_tab()
        self.setup_logs_tab()
    
    def setup_family_tab(self):
        """Настройка вкладки семей"""
        frame = ctk.CTkFrame(self.family_tab)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(frame, text="Информация о семье", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Поля для ввода данных
        self.setup_family_inputs(frame)
    
    def setup_family_inputs(self, parent):
        """Настройка полей ввода информации о семье"""
        # Поле ФИО матери
        mother_frame = ctk.CTkFrame(parent)
        mother_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(mother_frame, text="ФИО матери:").pack(anchor="w", padx=5)
        self.mother_fio = ctk.CTkEntry(mother_frame, placeholder_text="Фамилия Имя Отчество")
        self.mother_fio.pack(fill="x", padx=5, pady=2)
        
        # Поле даты рождения матери
        birth_frame = ctk.CTkFrame(parent)
        birth_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(birth_frame, text="Дата рождения матери:").pack(anchor="w", padx=5)
        self.mother_birth = ctk.CTkEntry(birth_frame, placeholder_text="ДД.ММ.ГГГГ")
        self.mother_birth.pack(fill="x", padx=5, pady=2)
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        if messagebox.askokcancel("Выход", "Закрыть приложение?"):
            # Сохранение конфигурации перед выходом
            self.save_config()
            self.app.destroy()

# Запуск приложения
if __name__ == "__main__":
    app = MyFamilyApp()
    app.run()
```

### Пример продвинутой обработки данных

```python
from utils.family_processor import FamilyDataProcessor
from utils.excel_utils import load_register_file, load_adpi_file

def advanced_family_processing():
    # Создание процессора данных
    processor = FamilyDataProcessor()
    
    # Загрузка внешних файлов
    try:
        processor.load_register_file("real_register.xlsx")
        processor.load_adpi_file("real_adpi.xlsx")
        print("Файлы успешно загружены")
    except Exception as e:
        print(f"Ошибка загрузки файлов: {e}")
        return
    
    # Подготовка данных для обработки
    search_requests = [
        "Иванова Анна Петровна",
        "Петрова Мария Сергеевна",
        "Сидорова Елена Викторовна"
    ]
    
    results = []
    for search_fio in search_requests:
        try:
            # Автоопределение семьи
            result = processor.auto_detect_family(search_fio)
            if result:
                results.append(result)
                print(f"Найдена семья: {result['mother_fio']}")
            else:
                print(f"Семья не найдена: {search_fio}")
        except Exception as e:
            print(f"Ошибка при поиске {search_fio}: {e}")
            continue
    
    # Обработка результатов
    print(f"\nНайдено {len(results)} семей из {len(search_requests)} запросов")
    
    # Форматирование результатов для сохранения
    formatted_results = []
    for result in results:
        # Форматирование данных в нужный формат
        formatted_family = {
            "mother_fio": result["mother_fio"],
            "mother_birth": result["mother_birth"],
            "address": result["address"],
            "phone": result["phone"],
            "children_count": len(result.get("children", [])),
            "adpi_info": result.get("adpi", {})
        }
        formatted_results.append(formatted_family)
    
    # Сохранение результатов
    with open("search_results.json", "w", encoding="utf-8") as f:
        json.dump(formatted_results, f, ensure_ascii=False, indent=2)
    
    print("Результаты сохранены в search_results.json")

if __name__ == "__main__":
    advanced_family_processing()
```

## Практические советы

### Оптимизация производительности

1. **Паузы между операциями**: Установите оптимальное значение паузы в массовом обработчике (обычно 0.5-1.0 секунды)
2. **Сохранение скриншотов**: Включайте только при отладке, отключайте при массовой обработке
3. **Проверка на ошибки**: Используйте опцию `stop_on_error=False` для продолжения обработки при ошибках

### Обработка больших файлов

1. **Разделение файлов**: Разделяйте большие JSON файлы на части по 50-100 семей
2. **Прогресс обработки**: Отслеживайте прогресс и делайте промежуточные сохранения
3. **Автосохранение**: Используйте встроенную функцию автосохранения

### Работа с разными форматами дат

Библиотека поддерживает следующие форматы дат:
- `ДД.ММ.ГГГГ` (например: 15.03.1990)
- `ДД/ММ/ГГГГ` (например: 15/03/1990)
- `ММ.ДД.ГГГГ` (например: 03.15.1990) - для американского формата
- `ГГГГ-ММ-ДД` (например: 1990-03-15) - для ISO формата

Функция `clean_date()` автоматически приводит все форматы к стандартному `ДД.ММ.ГГГГ`.

### Работа с разными форматами телефонов

Поддерживаются следующие форматы:
- `+7 XXX XXX-XX-XX`
- `8 XXX XXX-XX-XX`
- `7XXXXXXXXXX`
- `XXX-XX-XX` (с автоматическим добавлением кода страны)

Функция `clean_phone()` приводит все форматы к виду `7XXXXXXXXXX`.

## Распространенные проблемы и решения

### Проблемы с Selenium

1. **Устаревший драйвер**: Используйте `webdriver-manager` для автоматического обновления драйверов
2. **Проблемы с браузером**: Проверьте совместимость версий Chrome/Chromium и драйвера
3. **Проблемы с авторизацией**: Убедитесь, что учетные данные корректны и аккаунт активен

### Проблемы с файлами Excel

1. **Формат файла**: Убедитесь, что файлы в формате `.xlsx`, `.xls` или `.ods`
2. **Структура файла**: Проверьте, что столбцы имеют правильные заголовки
3. **Кодировка**: Используйте UTF-8 при сохранении файлов

### Проблемы с валидацией данных

1. **Некорректные даты**: Используйте `clean_date()` для нормализации
2. **Некорректные ФИО**: Используйте `clean_fio()` для очистки
3. **Некорректные телефоны**: Используйте `clean_phone()` для нормализации

Для получения дополнительной информации смотрите документацию по API в файле [API.md](API.md).