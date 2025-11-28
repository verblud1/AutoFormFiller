# ускорить работу 
# сделать возможность сохранения в json вместо базы данных и одновременного заполнения за один раз после запуска подстановки из  json
# сделать автопечать на принтер
# убрать в опред случаях в собственности у
# адпи в последнюю очередь
# ожидание сохранения должно быть не более 2 сек
# сделать массовое сохранение
# сделать автоизвлечение даты адпи по ФИО из двух столбцов напротив фио и подтверждение
# сделать автоизвлечение данных о составе семьи по ФИО и подтверждение
# ускорение заполнения чекбоксов
# ускорение заполнения  данных одновременное
# возрасть родителей более 20+ лет
# проверка на правильность нацденных родителей(если правильно, то продолжаем, если нет, меняем)
# неккоректно добавляется отец
# баг если не заполнить адпи
# кв м расчет за счет комнат

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import platform
import os
import sys
from datetime import datetime, date
import time
import re

class AutoFormFiller:
    def __init__(self):
        self.driver = None
        self.wait = None
        self._setup_driver()
        
    def _setup_driver(self):
        """Настройка драйвера с автоопределением браузера и полноэкранным режимом"""
        print("🔍 Определение браузера...")
        browser = self._detect_browser()
        
        if not browser:
            print("❌ Не найден Chrome, Yandex или Chromium")
            sys.exit(1)
            
        print(f"🚀 Используется: {browser['name']}")
        
        try:
            driver_path = ChromeDriverManager(chrome_type=browser['type']).install()
            service = webdriver.chrome.service.Service(driver_path)
            
            options = webdriver.ChromeOptions()
            if platform.system().lower() in ["linux", "redos"]:
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
            
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--start-maximized')
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            self.driver.maximize_window()
            
            print(f"✅ Драйвер настроен (полноэкранный режим)")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            sys.exit(1)
    
    def _detect_browser(self):
        """Определение доступного браузера"""
        system = platform.system().lower()
        
        if system == "windows":
            import winreg
            browsers = [
                (r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe', 'Chrome', ChromeType.GOOGLE),
                (r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\browser.exe', 'Yandex', ChromeType.YANDEX),
            ]
            
            for path, name, btype in browsers:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                        if os.path.exists(winreg.QueryValue(key, None)):
                            return {'name': name, 'type': btype}
                except: pass
                
        elif system in ["linux", "redos"]:
            for path in ['/usr/bin/chromium-browser', '/usr/bin/chromium']:
                if os.path.exists(path):
                    return {'name': 'Chromium', 'type': ChromeType.CHROMIUM}
        
        return None

    def _bulk_click_checkboxes(self, checkbox_ids):
        """Массовое нажатие чекбоксов через JavaScript"""
        script = """
        var ids = arguments[0];
        for (var i = 0; i < ids.length; i++) {
            var checkbox = document.getElementById('ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_' + ids[i]);
            if (checkbox && !checkbox.checked) {
                checkbox.click();
            }
        }
        return ids.length;
        """
        
        try:
            clicked = self.driver.execute_script(script, checkbox_ids)
            print(f"✅ Отмечено {clicked} чекбоксов")
            return True
        except Exception as e:
            print(f"⚠️ Ошибка массового отметки: {e}")
            return False

    def _bulk_fill_fields(self, field_data):
        """Массовое заполнение полей через JavaScript"""
        script = """
        var fields = arguments[0];
        var results = [];
        
        for (var i = 0; i < fields.length; i++) {
            var fieldInfo = fields[i];
            var element;
            
            if (fieldInfo.by === 'name') {
                element = document.querySelector('[name="' + fieldInfo.selector + '"]');
            } else if (fieldInfo.by === 'id') {
                element = document.getElementById(fieldInfo.selector);
            }
            
            if (element) {
                try {
                    var oldValue = element.value;
                    element.value = fieldInfo.value;
                    
                    // Триггерим события
                    var events = ['change', 'input', 'blur'];
                    for (var j = 0; j < events.length; j++) {
                        element.dispatchEvent(new Event(events[j], { bubbles: true }));
                    }
                    
                    results.push({
                        selector: fieldInfo.selector,
                        success: true,
                        oldValue: oldValue,
                        newValue: fieldInfo.value
                    });
                    
                } catch (e) {
                    results.push({
                        selector: fieldInfo.selector,
                        success: false,
                        error: e.toString()
                    });
                }
            } else {
                results.push({
                    selector: fieldInfo.selector,
                    success: false,
                    error: 'Element not found'
                });
            }
        }
        return results;
        """
        
        try:
            results = self.driver.execute_script(script, field_data)
            
            success_count = 0
            for result in results:
                if result['success']:
                    success_count += 1
                else:
                    print(f"⚠️ Не удалось заполнить {result['selector']}: {result['error']}")
            
            print(f"✅ Заполнено {success_count}/{len(field_data)} полей")
            return success_count == len(field_data)
            
        except Exception as e:
            print(f"❌ Ошибка массового заполнения: {e}")
            return False

    def _check_additional_info_empty(self):
        """Проверка, что поле дополнительной информации пустое"""
        try:
            # Переходим на вкладку доп. информации
            self._click_element(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL")
            time.sleep(2)
            
            # Проверяем текст в поле
            info_text = self._get_element_text("ctl00_cph_lblAddInfo2", "").strip()
            
            if info_text == "Информация отсутствует" or not info_text:
                return True
            else:
                print(f"❌ Найдены существующие данные: {info_text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Ошибка проверки поля: {e}")
            return True

    def _warn_existing_data(self):
        """Предупреждение о существующих данных и запрос подтверждения"""
        print("\n" + "!"*60)
        print("⚠️  ВНИМАНИЕ: В разделе 'Дополнительная информация' уже есть данные!")
        print("Все предыдущие данные будут УДАЛЕНЫ и заменены новыми.")
        print("!"*60)
        
        return self._get_yes_no_input("Продолжить автоматизацию? (д/н): ")

    def _check_correct_page(self):
        """Проверка что мы на правильной странице по наличию поля телефона"""
        try:
            if self._is_element_present(By.ID, "ctl00_cph_lblMobilPhone"):
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ Ошибка проверки страницы: {e}")
            return False

    def _is_element_present(self, by, selector):
        """Проверка наличия элемента на странице"""
        try:
            self.driver.find_element(by, selector)
            return True
        except:
            return False

    def _wait_for_correct_page(self):
        """Ожидание пока пользователь перейдет на правильную страницу"""
        while True:
            print("\n" + "="*60)
            print("📋 ДАННЫЕ СОБРАНЫ! ТЕПЕРЬ ПЕРЕЙДИТЕ НА СТРАНИЦУ")
            print("матери/отца семейства в базе данных")
            print("="*60)
            input("Когда будете готовы, нажмите Enter для проверки страницы...")
            
            if self._check_correct_page():
                print("✅ Вы на правильной странице! Начинаем автоматизацию...")
                return True
            else:
                print("❌ Вы не на правильной странице!")
                print("Убедитесь, что открыта страница конкретного человека (матери/отца семейства)")
                print("где отображается номер телефона и адрес")

    def _initialize_connection(self):
        """Инициализация подключения к базе данных с обработкой ошибок"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(f"🔗 Попытка подключения к базе данных ({attempt + 1}/{max_attempts})...")
                self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
                print("✅ Подключение успешно!")
                return True
                
            except Exception as e:
                if "ERR_CONNECTION_REFUSED" in str(e):
                    print("❌ Не удалось подключиться к базе данных")
                    print("🔌 Убедитесь, что база данных запущена и доступна по адресу http://localhost:8080")
                    
                    if attempt < max_attempts - 1:
                        input("🔄 Запустите базу данных и нажмите Enter для повторной попытки...")
                        if self.driver:
                            self.driver.quit()
                        self._setup_driver()
                    else:
                        print("❌ Не удалось подключиться после нескольких попыток")
                        return False
                else:
                    print(f"❌ Неизвестная ошибка: {e}")
                    return False
        return False

    # ===== УЛУЧШЕННЫЕ МЕТОДЫ ВВОДА С ПРОВЕРКАМИ =====
    
    def get_family_info(self):
        """Получение всей информации о семье"""
        print("\n" + "="*50)
        print("📋 ВВОД ДАННЫХ О СЕМЬЕ")
        print("="*50)
        
        family_data = self._input_family_members()
        family_data['work_places'] = self._input_work_places(family_data)
        family_data['children'] = self._input_children_education(family_data['children'])
        family_data['incomes'] = self._input_income_info(family_data)
        family_data['housing'] = self._input_housing_info()
        family_data['adpi'] = self._input_adpi_info()  # АДПИ перенесен после жилья
        
        return self._format_family_data(family_data)
    
    def _input_family_members(self):
        """Ввод данных о членах семьи"""
        print("\n👨‍👩‍👧‍👦 Члены семьи (ФИО и дата рождения):")
        print("Пример: Иванов Иван Иванович 15.05.2010")
        print("Пустая строка - завершить ввод")
        
        people = []
        while True:
            line = input().strip()
            if not line: break
            
            parts = line.split()
            if len(parts) >= 4:
                if not self._validate_date(parts[3]):
                    print(f"❌ Неверный формат даты: {parts[3]}. Используйте ДД.ММ.ГГГГ")
                    continue
                    
                people.append({
                    'fio': f"{parts[0]} {parts[1]} {parts[2]}",
                    'birth_date': parts[3],
                    'full_name': f"{parts[0]} {parts[1]} {parts[2]}"
                })
        
        if not people:
            print("⚠️ Используется шаблон")
            return self._get_default_family_data()
        
        return self._categorize_family_members(people)
    
    def _input_work_places(self, family_data):
        """Ввод информации о местах работы родителей"""
        print("\n💼 МЕСТА РАБОТЫ РОДИТЕЛЕЙ")
        work_places = {}
        
        if family_data.get('mother'):
            mother_work = input(f"Место работы матери ({family_data['mother']['fio']}): ").strip()
            if mother_work:
                work_places['mother'] = mother_work
        
        if family_data.get('father'):
            father_work = input(f"Место работы отца ({family_data['father']['fio']}): ").strip()
            if father_work:
                work_places['father'] = father_work
        
        return work_places
    
    def _input_children_education(self, children):
        """Ввод информации об образовании детей"""
        print("\n🎓 Место учебы детей (Enter - пропустить):")
        for child in children:
            child['education'] = input(f"  {child['fio']}: ").strip()
        return children
    
    def _input_income_info(self, family_data):
        """Ввод информации о доходах с проверкой чисел"""
        print("\n💰 ДОХОДЫ СЕМЬИ")
        print("Введите сумму или Enter для пропуска:")
        
        incomes = {}
        income_types = [
            ('mother_salary', 'Зарплата матери'),
            ('father_salary', 'Зарплата отца'),
            ('unified_benefit', 'Единое пособие'),
            ('large_family_benefit', 'Пособие по многодетности'),
            ('survivor_pension', 'Пенсия по потере кормильца'),
            ('alimony', 'Алименты'),
            ('disability_pension', 'Пенсия по инвалидности')
        ]
        
        for key, label in income_types:
            if key == 'father_salary' and not family_data.get('father'):
                continue
                
            while True:
                value = input(f"  {label}: ").strip()
                if not value:
                    break
                if self._validate_number(value):
                    incomes[key] = value
                    break
                else:
                    print("❌ Введите число (например: 15000 или 15000.50)")
        
        return incomes
    
    def _input_adpi_info(self):
        """Ввод информации об АДПИ с улучшенной проверкой дат"""
        print("\n📟 ИНФОРМАЦИЯ ОБ АДПИ")
        has_adpi = self._get_yes_no_input("АДПИ установлен? (д/н): ")
        
        adpi_data = {'has_adpi': has_adpi}
        if has_adpi == 'д':
            while True:
                install_date = input("Дата установки АДПИ (ДД.ММ.ГГГГ или Enter для пропуска): ").strip()
                if not install_date:
                    break
                if self._validate_date(install_date):
                    adpi_data['install_date'] = install_date
                    break
                else:
                    print("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")
            
            while True:
                check_date = input("Дата последней проверки АДПИ (ДД.ММ.ГГГГ или Enter для пропуска): ").strip()
                if not check_date:
                    break
                if self._validate_date(check_date):
                    adpi_data['check_date'] = check_date
                    break
                else:
                    print("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")
        
        return adpi_data
    
    def _input_housing_info(self):
        """Ввод информации о жилье с проверкой чисел и уточнением о собственности"""
        print("\n🏠 ИНФОРМАЦИЯ О ЖИЛЬЕ")
        
        while True:
            rooms = input("Количество комнат: ").strip()
            if rooms and self._validate_positive_number(rooms):
                break
            print("❌ Введите положительное число (например: 2, 3, 4)")
        
        while True:
            square = input("Площадь (кв.м.): ").strip()
            if square and self._validate_positive_number(square):
                break
            print("❌ Введите положительное число (например: 45.5, 60, 75.3)")
        
        amenities = self._get_amenities_input()
        
        print("\n🏠 В СОБСТВЕННОСТИ У:")
        print("(Можно указать: ФИО собственника, 'долевая собственность', 'приобретено на маткапитал', 'муниципальная' и т.д.)")
        print("Enter - пропустить")
        owner = input("> ").strip()
        
        if owner:
            return f"{rooms} комнат, {square} кв.м., {amenities}, в собственности у {owner}"
        else:
            return f"{rooms} комнат, {square} кв.м., {amenities}"
    
    def _get_amenities_input(self):
        """Выбор варианта удобств с тремя опциями"""
        print("\n🏠 УДОБСТВА В ЖИЛЬЕ:")
        print("д - со всеми удобствами")
        print("н - без удобств") 
        print("ч - с частичными удобствами")
        
        while True:
            choice = input("Выберите вариант (д/н/ч): ").strip().lower()
            if choice == 'д':
                return "со всеми удобствами"
            elif choice == 'н':
                return "без удобств"
            elif choice == 'ч':
                return "с частичными удобствами"
            else:
                print("❌ Введите 'д', 'н' или 'ч'")

    def _verify_and_edit_address(self, extracted_address):
        """Проверка и редактирование адреса"""
        print(f"\n🏠 Извлеченный адрес: {extracted_address}")
        
        if self._get_yes_no_input("Адрес верен? (д/н): ") == 'н':
            print("Введите правильный адрес:")
            new_address = input("> ").strip()
            return new_address if new_address else extracted_address
        
        return extracted_address

    def _review_all_data(self, data):
        """Просмотр и подтверждение всех данных перед заполнением"""
        while True:
            print("\n" + "="*60)
            print("👁️  ПРОСМОТР ВСЕХ ДАННЫХ")
            print("="*60)
            
            add_info_text, category, housing_info, adpi_data, incomes, work_places = data
            
            print("📋 ИНФОРМАЦИЯ О СЕМЬЕ:")
            print(add_info_text)
            
            print(f"\n🏷️  КАТЕГОРИЯ СЕМЬИ: {category}")
            print(f"\n🏠 ИНФОРМАЦИЯ О ЖИЛЬЕ: {housing_info}")
            print(f"\n📟 АДПИ: {'Установлен' if adpi_data['has_adpi'] == 'д' else 'Не установлен'}")
            
            if adpi_data.get('install_date'):
                print(f"   Дата установки: {adpi_data['install_date']}")
            if adpi_data.get('check_date'):
                print(f"   Дата проверки: {adpi_data['check_date']}")
            
            if work_places:
                print(f"\n💼 МЕСТА РАБОТЫ:")
                if work_places.get('mother'):
                    print(f"   Мать: {work_places['mother']}")
                if work_places.get('father'):
                    print(f"   Отец: {work_places['father']}")
            
            if incomes:
                print(f"\n💰 ДОХОДЫ:")
                income_labels = {
                    'mother_salary': 'Зарплата матери',
                    'father_salary': 'Зарплата отца', 
                    'unified_benefit': 'Единое пособие',
                    'large_family_benefit': 'Пособие по многодетности',
                    'survivor_pension': 'Пенсия по потере кормильца',
                    'alimony': 'Алименты',
                    'disability_pension': 'Пенсия по инвалидности'
                }
                for key, value in incomes.items():
                    print(f"   {income_labels[key]}: {value}")
            
            print("\n" + "="*60)
            print("Выберите действие:")
            print("1 - Подтвердить и начать заполнение")
            print("2 - Изменить информацию о семье")
            print("3 - Изменить информацию о жилье")
            print("4 - Изменить информацию об АДПИ")
            print("5 - Изменить информацию о доходах")
            print("6 - Изменить информацию о местах работы")
            print("0 - Отменить и выйти")
            
            choice = input("\nВаш выбор: ").strip()
            
            if choice == '1':
                return data
            elif choice == '2':
                new_family_data = self.get_family_info()
                data = (new_family_data[0], new_family_data[1], housing_info, adpi_data, incomes, work_places)
            elif choice == '3':
                housing_info = self._input_housing_info()
                data = (add_info_text, category, housing_info, adpi_data, incomes, work_places)
            elif choice == '4':
                adpi_data = self._input_adpi_info()
                data = (add_info_text, category, housing_info, adpi_data, incomes, work_places)
            elif choice == '5':
                family_data = self._get_default_family_data()
                if 'mother' in add_info_text:
                    family_data['mother'] = {'fio': 'Мать'}
                if 'Отец:' in add_info_text:
                    family_data['father'] = {'fio': 'Отец'}
                incomes = self._input_income_info(family_data)
                data = (add_info_text, category, housing_info, adpi_data, incomes, work_places)
            elif choice == '6':
                family_data = self._get_default_family_data()
                if 'mother' in add_info_text:
                    family_data['mother'] = {'fio': 'Мать'}
                if 'Отец:' in add_info_text:
                    family_data['father'] = {'fio': 'Отец'}
                work_places = self._input_work_places(family_data)
                data = (add_info_text, category, housing_info, adpi_data, incomes, work_places)
            elif choice == '0':
                return None
            else:
                print("❌ Неверный выбор")

    def _format_family_data(self, data):
        """Форматирование всех данных в финальный текст с учетом мест работы"""
        lines = []
        
        if data.get('mother'):
            mother_work = data['work_places'].get('mother', '')
            mother_line = f"Мать: {data['mother']['fio']} {data['mother']['birth_date']}"
            lines.extend([mother_line, f"Работает: {mother_work}"])
        else:
            lines.extend(["Мать: ", "Работает: "])
        
        if data.get('father'):
            father_work = data['work_places'].get('father', '')
            lines.extend([f"Отец: {data['father']['fio']} {data['father']['birth_date']}", f"Работает: {father_work}"])
        
        lines.append("Дети:")
        for child in data['children']:
            edu = f" - {child['education']}" if child.get('education') else ""
            lines.append(f"    {child['fio']} {child['birth_date']}{edu}")
        
        if data['incomes']:
            lines.append("Доход:")
            income_labels = {
                'mother_salary': 'з/п матери',
                'father_salary': 'з/п отца', 
                'unified_benefit': 'единое пособие',
                'large_family_benefit': 'пособие по многодетности',
                'survivor_pension': 'пенсия по потере кормильца',
                'alimony': 'алименты',
                'disability_pension': 'пенсия по инвалидности'
            }
            
            for key, value in data['incomes'].items():
                lines.append(f"{income_labels[key]} - {value}")
        
        category = "полная, многодетная" if data.get('father') else "неполная, многодетная"
        
        return "\n".join(lines), category, data['housing'], data['adpi'], data['incomes'], data['work_places']

    # ===== УЛУЧШЕННЫЕ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ С ПРОВЕРКАМИ =====
    
    def _categorize_family_members(self, people):
        """Разделение на родителей и детей"""
        today = date.today()
        parents, children = [], []
        
        for person in people:
            try:
                birth_date = datetime.strptime(person['birth_date'], '%d.%m.%Y').date()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                (parents if age >= 18 else children).append(person)
            except ValueError:
                children.append(person)
        
        mother = parents[0] if parents else None
        father = parents[1] if len(parents) > 1 else None
        
        return {'mother': mother, 'father': father, 'children': children}
    
    def _get_default_family_data(self):
        """Данные по умолчанию"""
        return {
            'mother': None, 
            'father': None, 
            'children': [],
            'incomes': {},
            'work_places': {}
        }
    
    def _validate_number(self, value):
        """Проверка что значение является числом (целым или дробным)"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _validate_positive_number(self, value):
        """Проверка что значение является положительным числом"""
        try:
            num = float(value)
            return num > 0
        except ValueError:
            return False
    
    def _get_required_input(self, prompt):
        """Получение обязательного ввода"""
        while True:
            value = input(prompt).strip()
            if value: return value
            print("⚠️ Это поле обязательно для заполнения")
    
    def _get_yes_no_input(self, prompt):
        """Получение ответа да/нет"""
        while True:
            response = input(prompt).strip().lower()
            if response in ['д', 'н']: return response
            print("Введите 'д' или 'н'")
    
    def _validate_date(self, date_string):
        """Проверка даты"""
        try:
            datetime.strptime(date_string, '%d.%m.%Y')
            return True
        except ValueError:
            return False

    # ===== МЕТОДЫ ДЛЯ СОХРАНЕНИЯ И СКРИНШОТОВ =====
    
    def _final_verification(self):
        """Финальная проверка перед сохранением"""
        print("\n" + "="*60)
        print("👁️  ФИНАЛЬНАЯ ПРОВЕРКА")
        print("="*60)
        print("Проверьте все введенные данные непосредственно на странице.")
        print("Если нужно что-то исправить - сделайте это сейчас вручную.")
        print("="*60)
        input("Когда все проверено и исправлено, нажмите Enter для сохранения...")
        return True
    
    def _save_and_exit(self):
        """Сохранение данных и выход с ожиданием завершения"""
        print("💾 Сохраняем данные...")
        
        # Нажимаем кнопку сохранения
        success = self._click_element_with_retry(By.ID, "ctl00_cph_lbtnExitSave")
        
        if success:
            print("⏳ Ожидаем завершения сохранения...")
            time.sleep(2)  # Уменьшено до 2 секунд
            
            # Проверяем, что сохранение прошло успешно
            try:
                # Ждем исчезновения элементов загрузки или появления подтверждения
                self.wait.until(EC.invisibility_of_element_located((By.ID, "ctl00_cph_lbtnExitSave")))
                print("✅ Данные успешно сохранены!")
                return True
            except Exception as e:
                print(f"⚠️ Сохранение завершено с предупреждением: {e}")
                return True
        else:
            print("❌ Не удалось сохранить данные")
            return False
    
    def _take_screenshot(self, family_data):
        """Создание скриншота страницы"""
        try:
            # Получаем ФИО для имени файла
            file_name = self._get_screenshot_filename(family_data)
            if not file_name:
                print("❌ Не удалось определить ФИО для скриншота")
                return False
            
            # Получаем путь к папке screenshots
            screenshots_dir = self._get_screenshots_directory()
            if not screenshots_dir:
                return False
            
            # Создаем полный путь к файлу
            file_path = os.path.join(screenshots_dir, f"{file_name}.png")
            
            # Делаем скриншот только области страницы (без браузерных элементов)
            self.driver.save_screenshot(file_path)
            print(f"📸 Скриншот сохранен: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания скриншота: {e}")
            return False
    
    def _get_screenshot_filename(self, family_data):
        """Получение имени файла для скриншота на основе ФИО"""
        add_info_text, _, _, _, _, _ = family_data
        
        # Извлекаем ФИО матери из текста
        lines = add_info_text.split('\n')
        for line in lines:
            if line.startswith('Мать: '):
                # Извлекаем ФИО (убираем "Мать: " и дату рождения)
                mother_info = line[6:]  # Убираем "Мать: "
                # Убираем дату рождения (последние 10 символов - ДД.ММ.ГГГГ)
                if len(mother_info) > 10:
                    mother_name = mother_info[:-10].strip()
                    # Заменяем пробелы и специальные символы
                    safe_name = re.sub(r'[\\/*?:"<>|]', '_', mother_name)
                    return safe_name if safe_name else "неизвестно"
        
        # Если матери нет, ищем отца
        for line in lines:
            if line.startswith('Отец: '):
                father_info = line[6:]
                if len(father_info) > 10:
                    father_name = father_info[:-10].strip()
                    safe_name = re.sub(r'[\\/*?:"<>|]', '_', father_name)
                    return safe_name if safe_name else "неизвестно"
        
        return "неизвестно"
    
    def _get_screenshots_directory(self):
        """Получение пути к папке для скриншотов"""
        try:
            # Определяем путь к рабочему столу в зависимости от ОС
            if platform.system() == "Windows":
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            else:  # Linux/RED OS
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                # Если папки Desktop нет, используем домашнюю директорию
                if not os.path.exists(desktop):
                    desktop = os.path.expanduser("~")
            
            screenshots_dir = os.path.join(desktop, "database_screens")
            
            # Проверяем существование папки
            if not os.path.exists(screenshots_dir):
                print(f"❌ Папка для скриншотов не найдена: {screenshots_dir}")
                print("Пожалуйста, создайте папку 'database_screens' на рабочем столе")
                input("После создания папки нажмите Enter...")
                
                # Проверяем еще раз
                if not os.path.exists(screenshots_dir):
                    print("❌ Папка все еще не создана. Скриншот не будет сохранен.")
                    return None
            
            return screenshots_dir
            
        except Exception as e:
            print(f"❌ Ошибка определения пути: {e}")
            return None

    # ===== ОСНОВНОЙ ЦИКЛ =====
    
    def run_automation(self):
        """Основной цикл автоматизации"""
        try:
            # Инициализация подключения к базе данных
            if not self._initialize_connection():
                print("❌ Не удалось подключиться к базе данных. Программа завершена.")
                return
            
            # Логин в систему
            self._login()
            
            # Проверяем, нет ли уже данных в доп. информации
            if not self._check_additional_info_empty():
                if self._warn_existing_data() != 'д':
                    print("❌ Автоматизация отменена пользователем")
                    return
            
            while True:
                # Получение всех данных от пользователя
                family_data = self.get_family_info()
                
                # Просмотр и подтверждение всех данных
                confirmed_data = self._review_all_data(family_data)
                if confirmed_data is None:
                    print("❌ Заполнение отменено")
                    break
                
                # Ждем пока пользователь перейдет на правильную страницу
                if not self._wait_for_correct_page():
                    break
                
                # Навигация и получение данных со страницы
                phone, address = self._navigate_to_form()
                
                # Проверка и редактирование адреса
                address = self._verify_and_edit_address(address)
                
                # Заполнение формы
                add_info_text, category, housing_info, adpi_data, incomes, work_places = confirmed_data
                self._fill_form(phone, address, housing_info, add_info_text, category, adpi_data)
                
                # Финальная проверка и сохранение
                if self._final_verification():
                    if self._save_and_exit():
                        # Создаем скриншот
                        self._take_screenshot(confirmed_data)
                        print("\n✅ Автоматизация завершена успешно!")
                    else:
                        print("\n⚠️ Автоматизация завершена с ошибками")
                
                if not self._ask_repeat(): 
                    break
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def _login(self):
        """Вход в систему"""
        print("🔐 Выполняем вход в систему...")
        self._fill_field(By.NAME, "tbUserName", "СРЦ_Вол")
        self._fill_field(By.NAME, "tbPassword", "СРЦ_Вол1", press_enter=True)
        print("✅ Вход выполнен")
    
    def _navigate_to_form(self):
        """Навигация к форме"""
        print("🔍 Извлекаем данные со страницы...")
        phone = self._get_element_text("ctl00_cph_lblMobilPhone")
        address = self._get_element_text("ctl00_cph_lblRegAddress", "Адрес не найден")
        
        print("📍 Переходим к форме дополнительной информации...")
        self._click_element(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL")
        self._click_element(By.ID, "ctl00_cph_lbtnEditAddInfo")
        self._click_element(By.ID, "ctl00_cph_ctrlDopFields_lbtnAdd")
        
        return phone, address
    
    def _fill_form(self, phone, address, housing_info, add_info_text, category, adpi_data):
        """Заполнение формы с массовым вводом полей"""
        print("📝 Заполнение формы...")
        time.sleep(2)

        # 1. Сначала отмечаем все чекбоксы одновременно
        checkbox_ids = [8, 12, 13, 14, 17, 18]
        if adpi_data['has_adpi'] == 'д':
            checkbox_ids.extend([15, 16])
        
        self._bulk_click_checkboxes(checkbox_ids)
        self._click_element_with_retry(By.ID, "ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_ctl06_AJOk")
        time.sleep(2)

        # 2. Заполняем текстовую область отдельно (она требует resize)
        self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True)
        
        # 3. Массовое заполнение всех остальных полей (кроме дат АДПИ)
        field_data = [
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl02$tb', 'value': phone or ''},
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl04$tb', 'value': category},
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl05$tb', 'value': address},
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl08$tb', 'value': housing_info},
            {'by': 'name', 'selector': 'ctl00$cph$ctrlDopFields$gv$ctl09$tb', 
             'value': "Санитарные условия удовлетворительные, для детей имеется отдельное спальное место, место для занятий и отдыха. Продукты питания в достаточном количестве."}
        ]
        
        self._bulk_fill_fields(field_data)
        
        # 4. Заполняем АДПИ: сначала радио-кнопку, потом даты
        self._fill_adpi_radio_button(adpi_data)
        
        # 5. Заполняем даты АДПИ (если нужно)
        if adpi_data['has_adpi'] == 'д':
            self._fill_adpi_dates(adpi_data)
    
    def _fill_adpi_radio_button(self, adpi_data):
        """Заполнение радио-кнопки АДПИ"""
        if adpi_data['has_adpi'] == 'д':
            self._click_element_with_retry(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0")
        else:
            self._click_element_with_retry(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_1")
    
    def _fill_adpi_dates(self, adpi_data):
        """Заполнение дат АДПИ"""
        if adpi_data.get('install_date'):
            self._fill_date_field("igtxtctl00_cph_ctrlDopFields_gv_ctl06_wdte", adpi_data['install_date'])
            time.sleep(1)
        
        if adpi_data.get('check_date'):
            self._fill_date_field("igtxtctl00_cph_ctrlDopFields_gv_ctl07_wdte", adpi_data['check_date'])

    def _click_checkboxes_with_retry(self, has_adpi):
        """Отметка чекбоксов с повторными попытками при ошибках"""
        print("✅ Отмечаем чекбоксы...")
        
        target_ids = [8, 12, 13, 14, 17, 18]
        if has_adpi == 'д':
            target_ids.extend([15, 16])
        
        for checkbox_id in target_ids:
            success = self._click_checkbox_with_retry(checkbox_id)
            if not success:
                print(f"⚠️ Не удалось отметить чекбокс {checkbox_id} после нескольких попыток")

    def _click_checkbox_with_retry(self, checkbox_id, max_attempts=3):
        """Клик по чекбоксу с повторными попытками"""
        for attempt in range(max_attempts):
            try:
                checkbox = self.wait.until(
                    EC.element_to_be_clickable((By.ID, f"ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_{checkbox_id}"))
                )
                
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                
                if not checkbox.is_selected():
                    checkbox.click()
                    print(f"✓ Чекбокс {checkbox_id} отмечен (попытка {attempt + 1})")
                
                self.wait.until(EC.staleness_of(checkbox))
                return True
                
            except Exception as e:
                print(f"⚠️ Ошибка чекбокса {checkbox_id} (попытка {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    
        return False

    def _click_element_with_retry(self, by, selector, max_attempts=3):
        """Клик по элементу с повторными попытками"""
        for attempt in range(max_attempts):
            try:
                element = self.wait.until(EC.element_to_be_clickable((by, selector)))
                element.click()
                print(f"✓ Элемент {selector} кликнут (попытка {attempt + 1})")
                return True
            except Exception as e:
                print(f"⚠️ Ошибка клика {selector} (попытка {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
        return False

    # ===== БАЗОВЫЕ МЕТОДЫ Selenium =====
    
    def _fill_field(self, by, selector, text, press_enter=False):
        """Заполнение поля"""
        try:
            field = self.wait.until(EC.element_to_be_clickable((by, selector)))
            field.clear()
            field.send_keys(text + (Keys.ENTER if press_enter else ""))
            return True
        except Exception as e:
            print(f"⚠️ Ошибка поля {selector}: {e}")
            return False
    
    def _fill_textarea(self, field_name, text, resize=False):
        """Заполнение текстовой области"""
        if self._fill_field(By.NAME, field_name, text) and resize:
            field = self.driver.find_element(By.NAME, field_name)
            self.driver.execute_script("arguments[0].style.height = '352px'; arguments[0].style.width = '1151px';", field)
    
    def _fill_date_field(self, field_id, date_text):
        """Заполнение поля даты"""
        try:
            field = self.wait.until(EC.element_to_be_clickable((By.ID, field_id)))
            field.click()
            field.send_keys(Keys.CONTROL + "a")
            field.send_keys(Keys.DELETE)
            
            actions = ActionChains(self.driver)
            for char in date_text:
                actions.send_keys(char)
                actions.pause(0.1)
            actions.perform()
            
            field.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка даты {field_id}: {e}")
            return False
    
    def _click_element(self, by, selector):
        """Клик по элементу"""
        try:
            element = self.wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            return True
        except Exception as e:
            print(f"⚠️ Ошибка клика {selector}: {e}")
            return False
    
    def _get_element_text(self, element_id, default=""):
        """Получение текста элемента"""
        try:
            return self.driver.find_element(By.ID, element_id).text
        except:
            return default
    
    def _ask_repeat(self):
        """Запрос на повтор"""
        return input("\n🔄 Повторить? ('с' - да, Enter - нет): ").strip().lower() == 'с'


if __name__ == "__main__":
    print("=" * 50)
    print("🤖 АВТОМАТИЗАТОР ФОРМ")
    print("=" * 50)
    
    try:
        filler = AutoFormFiller()
        filler.run_automation()
    except KeyboardInterrupt:
        print("\n⏹️ Остановлено пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")