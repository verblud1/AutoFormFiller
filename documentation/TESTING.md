# Тестирование AutoFormFiller

## Обзор

В этом документе описаны подходы к тестированию проекта AutoFormFiller, включая юнит-тесты, интеграционные тесты и сценарии ручного тестирования.

## Типы тестов

### 1. Юнит-тесты

#### Тестирование утилитарных функций

##### utils.data_processing
```python
import unittest
from utils.data_processing import clean_fio, clean_date, clean_phone

class TestDataProcessing(unittest.TestCase):
    
    def test_clean_fio(self):
        """Тестирование очистки ФИО"""
        self.assertEqual(clean_fio("  Иванов   Иван   Иванович  "), "Иванов Иван Иванович")
        self.assertEqual(clean_fio("петров петр петрович"), "Петров Петр Петрович")
        self.assertEqual(clean_fio(""), "")
    
    def test_clean_date(self):
        """Тестирование очистки даты"""
        self.assertEqual(clean_date("28.12.202026"), "28.12.2020")
        self.assertEqual(clean_date("15/03/1985"), "15.03.1985")
        self.assertEqual(clean_date("01.01.2020.02.02.2021"), "02.02.2021")  # две даты
    
    def test_clean_phone(self):
        """Тестирование очистки телефона"""
        self.assertEqual(clean_phone("89123456789"), "79123456789")
        self.assertEqual(clean_phone("9123456789"), "79123456789")
        self.assertEqual(clean_phone("+79123456789"), "79123456789")
        self.assertEqual(clean_phone("79123456789"), "79123456789")

if __name__ == '__main__':
    unittest.main()
```

##### utils.validation
```python
import unittest
from utils.validation import validate_date, validate_number, validate_phone

class TestValidation(unittest.TestCase):
    
    def test_validate_date(self):
        """Тестирование валидации даты"""
        self.assertTrue(validate_date("15.03.1985"))
        self.assertTrue(validate_date("01.01.2020"))
        self.assertFalse(validate_date("99.99.9999"))  # неверная дата
        self.assertFalse(validate_date("invalid_date"))
    
    def test_validate_number(self):
        """Тестирование валидации числа"""
        self.assertTrue(validate_number("12345"))
        self.assertTrue(validate_number("123.45"))
        self.assertTrue(validate_number(""))
        self.assertFalse(validate_number("abc123"))
    
    def test_validate_phone(self):
        """Тестирование валидации телефона"""
        self.assertTrue(validate_phone("79123456789"))
        self.assertTrue(validate_phone(""))  # пустой телефон допустим
        self.assertFalse(validate_phone("12345"))  # слишком короткий
        self.assertFalse(validate_phone("891234567890"))  # неверный формат

if __name__ == '__main__':
    unittest.main()
```

##### utils.excel_utils
```python
import unittest
from unittest.mock import patch, mock_open
import pandas as pd
from utils.excel_utils import load_register_file, load_adpi_file

class TestExcelUtils(unittest.TestCase):
    
    @patch('pandas.read_excel')
    def test_load_register_file(self, mock_read_excel):
        """Тестирование загрузки реестра"""
        # Создаем тестовые данные
        df_data = {
            0: [1, 2],  # номер записи
            1: ['Иванов', 'Петров'],  # фамилия
            2: ['Иван', 'Петр'],      # имя
            3: ['Иванович', 'Петрович'],  # отчество
            4: ['15.03.1985', '10.05.1982'],  # дата рождения
            5: ['г. Москва', 'г. Санкт-Петербург'],  # регион
            10: ['79123456789', '79234567890']  # телефон
        }
        mock_df = pd.DataFrame(df_data)
        mock_read_excel.return_value = mock_df
        
        result = load_register_file("test_file.xlsx")
        
        self.assertIn('Иванов Иван Иванович', result)
        self.assertIn('Петров Петр Петрович', result)
        
        # Проверяем, что данные корректно извлечены
        ivanov_data = result['Иванов Иван Иванович']
        self.assertEqual(ivanov_data['main_person']['phone'], '79123456789')

if __name__ == '__main__':
    unittest.main()
```

#### Тестирование процессора данных

##### utils.family_processor
```python
import unittest
from utils.family_processor import FamilyDataProcessor

class TestFamilyProcessor(unittest.TestCase):
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.processor = FamilyDataProcessor()
    
    def test_collect_family_data(self):
        """Тестирование сбора данных семьи"""
        form_data = {
            'mother_fio': 'Иванова Мария Петровна',
            'mother_birth': '15.03.1990',
            'mother_work': 'ООО Ромашка',
            'children': [
                {
                    'fio': 'Иванов Петр Марьянович',
                    'birth': '10.05.2015',
                    'education': 'Школа №1'
                }
            ],
            'phone_number': '79123456789',
            'address': 'г. Москва, ул. Ленина, д. 1'
        }
        
        result = self.processor.collect_family_data(form_data)
        
        self.assertEqual(result['mother_fio'], 'Иванова Мария Петровна')
        self.assertEqual(len(result['children']), 1)
        self.assertEqual(result['phone_number'], '79123456789')
    
    def test_calculate_unified_benefit(self):
        """Тестирование расчета единого пособия"""
        # 2 ребенка, 100% пособия
        result = self.processor.calculate_unified_benefit(2, "100%")
        expected = 17000 * 2  # BASE_UNIFIED_BENEFIT * количество детей
        self.assertEqual(result, expected)
        
        # 3 ребенка, 75% пособия
        result = self.processor.calculate_unified_benefit(3, "75%")
        expected = int(17000 * 0.75 * 3)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
```

### 2. Интеграционные тесты

#### Тестирование взаимодействия компонентов

```python
import unittest
from unittest.mock import patch, MagicMock
from family_creator.json_generator import JSONFamilyCreator
from utils.data_processing import clean_family_data

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.creator = JSONFamilyCreator()
    
    def test_add_and_save_family(self):
        """Тестирование добавления и сохранения семьи"""
        family_data = {
            'mother_fio': 'Тестова Анна Петровна',
            'mother_birth': '01.01.1990',
            'children': [
                {
                    'fio': 'Тестов Иван Анатольевич',
                    'birth': '01.01.2010',
                    'education': 'Школа'
                }
            ]
        }
        
        # Добавляем семью
        success = self.creator.add_family(family_data)
        self.assertTrue(success)
        
        # Проверяем, что семья добавлена
        self.assertEqual(len(self.creator.families), 1)
        self.assertEqual(self.creator.families[0]['mother_fio'], 'Тестова Анна Петровна')
        
        # Проверяем, что данные очищены
        cleaned_family = clean_family_data(family_data)
        self.assertEqual(self.creator.families[0], cleaned_family)
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.dump')
    def test_save_to_json(self, mock_json_dump, mock_file):
        """Тестирование сохранения в JSON"""
        # Добавляем тестовую семью
        test_family = {
            'mother_fio': 'Тестова Анна Петровна',
            'mother_birth': '01.01.1990'
        }
        self.creator.families = [test_family]
        
        # Сохраняем в JSON
        result = self.creator.save_to_json('/fake/path/test.json')
        
        self.assertTrue(result)
        mock_json_dump.assert_called_once()
        
        # Проверяем, что в файл записаны очищенные данные
        called_args = mock_json_dump.call_args[0]
        saved_data = called_args[0]
        self.assertEqual(len(saved_data), 1)
        self.assertEqual(saved_data[0]['mother_fio'], 'Тестова Анна Петровна')

if __name__ == '__main__':
    unittest.main()
```

### 3. Сценарии ручного тестирования

#### Тестирование GUI компонентов

##### Создатель JSON файлов
1. **Запуск приложения**
   - Запустить `python main.py --mode creator`
   - Проверить, что интерфейс загружается без ошибок
   - Проверить, что все вкладки доступны

2. **Загрузка реестра**
   - Перейти на вкладку "🤖 Автоопределение"
   - Нажать "📋 Загрузить реестр (xls/xlsx)"
   - Выбрать тестовый файл реестра
   - Проверить, что данные загрузились и отображаются в поле информации

3. **Автоматическое определение семьи**
   - Ввести ФИО в поле поиска
   - Нажать "🔄 Автоопределить семью"
   - Проверить, что форма заполнилась корректными данными

4. **Сохранение JSON**
   - Заполнить данные семьи
   - Перейти на вкладку "📋 Управление"
   - Нажать "💾 Сохранить в JSON"
   - Проверить, что файл создался и содержит корректные данные

##### Массовый обработчик
1. **Запуск приложения**
   - Запустить `python main.py --mode processor`
   - Проверить, что интерфейс загружается без ошибок

2. **Загрузка JSON файла**
   - Нажать "📝 Загрузить из JSON"
   - Выбрать тестовый JSON файл
   - Проверить, что данные загрузились и отображаются в таблице

3. **Начало обработки**
   - Нажать "🚀 Начать обработку"
   - Проверить, что появилось окно выбора стартовой семьи
   - Выбрать семью и начать обработку
   - Проверить, что процесс идет без ошибок

#### Тестирование функций обработки данных

##### Тестирование загрузки Excel файлов
1. Подготовить тестовые файлы реестра и АДПИ
2. Загрузить файлы в приложение
3. Проверить, что данные корректно извлекаются
4. Проверить, что не возникает ошибок при обработке разных форматов дат

##### Тестирование валидации данных
1. Ввести заведомо некорректные данные (например, дату рождения > 2003 для родителя)
2. Проверить, что система выдает соответствующие предупреждения
3. Проверить, что некорректные данные не сохраняются

### 4. Тестирование в разных средах

#### Тестирование на разных ОС
- Windows
- Linux
- macOS

#### Тестирование с разными версиями Python
- Python 3.7
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11

#### Тестирование с разными браузерами
- Chrome
- Yandex Browser
- Chromium

### 5. Тестирование производительности

#### Тестирование с большими файлами
```python
def test_performance_with_large_files():
    """Тестирование производительности с большими файлами"""
    import time
    from family_creator.json_generator import JSONFamilyCreator
    
    creator = JSONFamilyCreator()
    
    # Создаем тестовые данные с 1000 семей
    large_family_list = []
    for i in range(1000):
        family = {
            'mother_fio': f'Тестова{i} Анна Петровна',
            'mother_birth': '01.01.1990',
            'children': [
                {
                    'fio': f'Тестов{i} Иван Анатольевич',
                    'birth': '01.01.2010',
                    'education': 'Школа'
                }
            ]
        }
        large_family_list.append(family)
    
    start_time = time.time()
    creator.families = large_family_list
    save_result = creator.save_to_json('test_large_file.json')
    end_time = time.time()
    
    print(f"Сохранение 1000 семей заняло {end_time - start_time:.2f} секунд")
    assert save_result, "Сохранение не выполнено"
```

### 6. Тестирование автосохранения

```python
def test_autosave_functionality():
    """Тестирование функции автосохранения"""
    import os
    from family_creator.json_generator import JSONFamilyCreator
    
    creator = JSONFamilyCreator()
    
    # Добавляем семью
    test_family = {
        'mother_fio': 'Автосохраняемая Анна Петровна',
        'mother_birth': '01.01.1990'
    }
    creator.families = [test_family]
    
    # Вызываем автосохранение
    creator.autosave_families()
    
    # Проверяем, что файл автосохранения существует
    assert os.path.exists(creator.autosave_filename), "Файл автосохранения не создан"
    
    # Загружаем файл автосохранения и проверяем содержимое
    with open(creator.autosave_filename, 'r', encoding='utf-8') as f:
        import json
        saved_data = json.load(f)
        assert len(saved_data) == 1, "Данные не сохранились корректно"
        assert saved_data[0]['mother_fio'] == 'Автосохраняемая Анна Петровна', "Содержимое не совпадает"
```

### 7. Тестирование обработки ошибок

```python
def test_error_handling():
    """Тестирование обработки ошибок"""
    from utils.validation import validate_family_data
    
    # Проверяем валидацию данных с ошибками
    invalid_family = {
        'mother_fio': '',  # пустое поле - ошибка
        'mother_birth': 'invalid_date',  # неверный формат даты
        'children': [
            {
                'fio': 'Ребенок',  # ребенок младше 2000 года - ошибка
                'birth': '15.03.1995'
            }
        ]
    }
    
    errors = validate_family_data(invalid_family)
    assert len(errors) > 0, "Ошибки не обнаружены"
    
    # Проверяем, что каждая ошибка логична
    error_messages = [str(error) for error in errors]
    assert any('ФИО матери' in msg for msg in error_messages), "Ошибка ФИО матери не обнаружена"
    assert any('дата' in msg.lower() for msg in error_messages), "Ошибка даты не обнаружена"
```

### 8. Запуск тестов

#### Запуск всех тестов
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

#### Запуск конкретного теста
```bash
python -m unittest tests.test_data_processing.TestDataProcessing.test_clean_fio -v
```

#### Запуск тестов с покрытием
```bash
pip install coverage
coverage run -m unittest discover -s tests -p "test_*.py"
coverage report -m
```

### 9. CI/CD Pipeline (пример)

#### .github/workflows/tests.yml
```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest coverage
    
    - name: Run tests
      run: |
        python -m unittest discover -s tests -p "test_*.py" -v
    
    - name: Coverage report
      run: |
        coverage run -m unittest discover -s tests -p "test_*.py"
        coverage report
```

### 10. Тестирование GUI (опционально)

Для тестирования GUI можно использовать библиотеку `pyautogui` или `botcity-framework-core`:

```python
import unittest
import time
import subprocess
import sys
from unittest.mock import patch

class TestGUI(unittest.TestCase):
    
    def setUp(self):
        """Подготовка GUI теста"""
        # Запускаем приложение в фоновом режиме
        self.process = subprocess.Popen([sys.executable, "main.py", "--mode", "creator"])
        time.sleep(3)  # Даем время для запуска GUI
    
    def tearDown(self):
        """Завершение GUI теста"""
        self.process.terminate()
        self.process.wait()
    
    def test_gui_launch(self):
        """Тест запуска GUI"""
        # В реальной ситуации здесь будет проверка видимости окна
        # или использование инструментов автоматизации GUI
        self.assertTrue(self.process.poll() is None, "Приложение завершилось с ошибкой")
    
    @patch('tkinter.messagebox.showinfo')
    def test_gui_functionality(self, mock_showinfo):
        """Тест функциональности GUI"""
        # В реальной ситуации здесь будут эмулироваться действия пользователя
        # и проверяться результаты
        mock_showinfo.assert_not_called()
```

Этот документ предоставляет полное руководство по тестированию проекта AutoFormFiller, включая примеры юнит-тестов, интеграционных тестов и сценариев ручного тестирования.