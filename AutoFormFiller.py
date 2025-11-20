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

class AutoFormFiller:
    def __init__(self):
        self.driver = None
        self.wait = None
        self._setup_driver()
        
    def _setup_driver(self):
        """Настройка драйвера с автоопределением браузера"""
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
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            print(f"✅ Драйвер настроен")
            
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

    # ===== УПРОЩЕННЫЕ МЕТОДЫ ВВОДА =====
    
    def get_family_info(self):
        """Получение всей информации о семье"""
        print("\n" + "="*50)
        print("📋 ВВОД ДАННЫХ О СЕМЬЕ")
        print("="*50)
        
        family_data = self._input_family_members()
        family_data['children'] = self._input_children_education(family_data['children'])
        family_data['incomes'] = self._input_income_info(family_data)
        family_data['adpi'] = self._input_adpi_info()
        family_data['housing'] = self._input_housing_info()
        
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
                people.append({
                    'fio': f"{parts[0]} {parts[1]} {parts[2]}",
                    'birth_date': parts[3],
                    'full_name': f"{parts[0]} {parts[1]} {parts[2]}"
                })
        
        if not people:
            print("⚠️ Используется шаблон")
            return self._get_default_family_data()
        
        return self._categorize_family_members(people)
    
    def _input_children_education(self, children):
        """Ввод информации об образовании детей"""
        print("\n🎓 Место учебы детей (Enter - пропустить):")
        for child in children:
            child['education'] = input(f"  {child['fio']}: ").strip()
        return children
    
    def _input_income_info(self, family_data):
        """Ввод информации о доходах с возможностью пропуска"""
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
            # Пропускаем зарплату отца, если его нет
            if key == 'father_salary' and not family_data.get('father'):
                continue
                
            value = input(f"  {label}: ").strip()
            if value:
                incomes[key] = value
        
        return incomes
    
    def _input_adpi_info(self):
        """Ввод информации об АДПИ"""
        print("\n📟 ИНФОРМАЦИЯ ОБ АДПИ")
        has_adpi = self._get_yes_no_input("АДПИ установлен? (д/н): ")
        
        adpi_data = {'has_adpi': has_adpi}
        if has_adpi == 'д':
            install_date = input("Дата установки (ДД.ММ.ГГГГ или Enter): ").strip()
            if install_date and self._validate_date(install_date):
                adpi_data['install_date'] = install_date
            
            check_date = input("Дата проверки (ДД.ММ.ГГГГ или Enter): ").strip()
            if check_date and self._validate_date(check_date):
                adpi_data['check_date'] = check_date
        
        return adpi_data
    
    def _input_housing_info(self):
        """Ввод информации о жилье"""
        print("\n🏠 ИНФОРМАЦИЯ О ЖИЛЬЕ")
        rooms = self._get_required_input("Количество комнат: ")
        square = self._get_required_input("Площадь (кв.м.): ")
        amenities = "со всеми удобствами" if self._get_yes_no_input("Со всеми удобствами? (д/н): ") == 'д' else "с частичными удобствами"
        owner = self._get_required_input("Собственник: ")
        
        return f"{rooms} комнат, {square} кв.м., {amenities}, в собственности у {owner}"

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
            
            add_info_text, category, housing_info, adpi_data, incomes = data
            
            # Выводим все данные
            print("📋 ИНФОРМАЦИЯ О СЕМЬЕ:")
            print(add_info_text)
            
            print(f"\n🏷️  КАТЕГОРИЯ СЕМЬИ: {category}")
            
            print(f"\n🏠 ИНФОРМАЦИЯ О ЖИЛЬЕ: {housing_info}")
            
            print(f"\n📟 АДПИ: {'Установлен' if adpi_data['has_adpi'] == 'д' else 'Не установлен'}")
            if adpi_data.get('install_date'):
                print(f"   Дата установки: {adpi_data['install_date']}")
            if adpi_data.get('check_date'):
                print(f"   Дата проверки: {adpi_data['check_date']}")
            
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
            print("0 - Отменить и выйти")
            
            choice = input("\nВаш выбор: ").strip()
            
            if choice == '1':
                return data
            elif choice == '2':
                new_family_data = self.get_family_info()
                data = (new_family_data[0], new_family_data[1], housing_info, adpi_data, incomes)
            elif choice == '3':
                housing_info = self._input_housing_info()
                data = (add_info_text, category, housing_info, adpi_data, incomes)
            elif choice == '4':
                adpi_data = self._input_adpi_info()
                data = (add_info_text, category, housing_info, adpi_data, incomes)
            elif choice == '5':
                family_data = self._get_default_family_data()
                if 'mother' in add_info_text:
                    family_data['mother'] = {'fio': 'Мать'}
                if 'Отец:' in add_info_text:
                    family_data['father'] = {'fio': 'Отец'}
                incomes = self._input_income_info(family_data)
                data = (add_info_text, category, housing_info, adpi_data, incomes)
            elif choice == '0':
                return None
            else:
                print("❌ Неверный выбор")

    def _format_family_data(self, data):
        """Форматирование всех данных в финальный текст"""
        lines = []
        
        # Родители
        mother_line = f"Мать: {data['mother']['fio']} {data['mother']['birth_date']}" if data.get('mother') else "Мать:"
        lines.extend([mother_line, "Работает: "])
        
        if data.get('father'):
            lines.extend([f"Отец: {data['father']['fio']} {data['father']['birth_date']}", "Работает: "])
        
        # Дети
        lines.append("Дети:")
        for child in data['children']:
            edu = f" - {child['education']}" if child.get('education') else ""
            lines.append(f"    {child['fio']} {child['birth_date']}{edu}")
        
        # Доходы (только указанные)
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
        
        # Категория семьи
        category = "полная, многодетная" if data.get('father') else "неполная, многодетная"
        
        return "\n".join(lines), category, data['housing'], data['adpi'], data['incomes']

    # ===== УПРОЩЕННЫЕ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====
    
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
        
        # Простое определение родителей (первый взрослый - мать, второй - отец)
        mother = parents[0] if parents else None
        father = parents[1] if len(parents) > 1 else None
        
        return {'mother': mother, 'father': father, 'children': children}
    
    def _get_default_family_data(self):
        """Данные по умолчанию"""
        return {
            'mother': None, 
            'father': None, 
            'children': [],
            'incomes': {}
        }
    
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
            print("❌ Неверный формат даты")
            return False

    # ===== ОСНОВНОЙ ЦИКЛ =====
    
    def run_automation(self):
        """Основной цикл автоматизации"""
        try:
            # Переходим на начальную страницу и логинимся
            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
            self._login()
            
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
                add_info_text, category, housing_info, adpi_data, incomes = confirmed_data
                self._fill_form(phone, address, housing_info, add_info_text, category, adpi_data)
                
                print("\n✅ Автоматизация завершена!")
                if not self._ask_repeat(): break
                    
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
        """Заполнение формы"""
        print("📝 Заполнение формы...")
        time.sleep(2)
        # Чекбоксы
        self._click_checkboxes(adpi_data['has_adpi'])
        self._click_element(By.ID, "ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_ctl06_AJOk")
        time.sleep(3)
        
        # Основные поля
        self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True)
        if phone:
            self._fill_field(By.NAME, "ctl00$cph$ctrlDopFields$gv$ctl02$tb", phone)
        
        # АДПИ
        self._fill_adpi_fields(adpi_data)
        
        
        
        # Остальные поля
        fields = {
            "ctl00$cph$ctrlDopFields$gv$ctl04$tb": category,
            "ctl00$cph$ctrlDopFields$gv$ctl05$tb": address,
            "ctl00$cph$ctrlDopFields$gv$ctl08$tb": housing_info,
            "ctl00$cph$ctrlDopFields$gv$ctl09$tb": "Санитарные условия удовлетворительные, для детей имеется отдельное спальное место, место для занятий и отдыха. Продукты питания в достаточном количестве."
        }
        
        for field, text in fields.items():
            self._fill_field(By.NAME, field, text)
    
    def _fill_adpi_fields(self, adpi_data):
        """Заполнение полей АДПИ"""
        if adpi_data['has_adpi'] == 'д':
            self._click_element(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0")
            time.sleep(1)
            
            if adpi_data.get('install_date'):
                self._fill_date_field("igtxtctl00_cph_ctrlDopFields_gv_ctl06_wdte", adpi_data['install_date'])
                time.sleep(1)
            
            if adpi_data.get('check_date'):
                self._fill_date_field("igtxtctl00_cph_ctrlDopFields_gv_ctl07_wdte", adpi_data['check_date'])
        else:
            self._click_element(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_1")

    def _click_checkboxes(self, has_adpi):
        """Отметка чекбоксов с учетом АДПИ"""
        print("✅ Отмечаем чекбоксы...")
        
        target_ids = [8, 12, 13, 14, 17, 18]
        if has_adpi == 'д':
            target_ids.extend([15, 16])
        
        for checkbox_id in target_ids:
            self._click_checkbox(checkbox_id)

    def _click_checkbox(self, checkbox_id):
        """Клик по чекбоксу"""
        try:
            checkbox = self.wait.until(
                EC.element_to_be_clickable((By.ID, f"ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_{checkbox_id}"))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView();", checkbox)
            
            if not checkbox.is_selected():
                checkbox.click()
            
            self.wait.until(EC.staleness_of(checkbox))
            return True
            
        except Exception as e:
            print(f"⚠️ Ошибка чекбокса {checkbox_id}: {e}")
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
            
            # Ввод даты посимвольно с паузами
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