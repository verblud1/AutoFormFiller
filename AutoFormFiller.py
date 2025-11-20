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
        self.templates = self._setup_templates()
        self._setup_driver()
        
    def _detect_os(self):
        """Определение операционной системы"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "linux":
            # Проверка для RED OS (основана на RHEL)
            if os.path.exists("/etc/redos-release"):
                return "redos"
            return "linux"
        else:
            return "unknown"
    
    def _detect_browsers(self):
        """Определение доступных браузеров в системе"""
        browsers = []
        current_os = self._detect_os()
        
        if current_os == "windows":
            import winreg
            # Проверка Chrome
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe') as key:
                    chrome_path = winreg.QueryValue(key, None)
                    if os.path.exists(chrome_path):
                        browsers.append(('chrome', 'Google Chrome', ChromeType.GOOGLE))
            except: pass
            
            # Проверка Yandex
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\browser.exe') as key:
                    yandex_path = winreg.QueryValue(key, None)
                    if os.path.exists(yandex_path):
                        browsers.append(('yandex', 'Yandex Browser', ChromeType.YANDEX))
            except: pass
            
        elif current_os in ["linux", "redos"]:
            # Проверка Chromium в Linux/RED OS
            chromium_paths = [
                '/usr/bin/chromium-browser',
                '/usr/bin/chromium',
                '/snap/bin/chromium'
            ]
            for path in chromium_paths:
                if os.path.exists(path):
                    browsers.append(('chromium', 'Chromium', ChromeType.CHROMIUM))
                    break
        
        return browsers
    
    def _setup_driver(self):
        """Настройка драйвера с автоматическим определением браузера"""
        print("Определение доступных браузеров...")
        browsers = self._detect_browsers()
        
        if not browsers:
            print("❌ Не найдены поддерживаемые браузеры (Chrome, Yandex, Chromium)")
            sys.exit(1)
        
        print("Найдены браузеры:")
        for i, (browser_id, browser_name, chrome_type) in enumerate(browsers):
            print(f"  {i+1}. {browser_name}")
        
        # Автовыбор первого найденного браузера
        selected_browser = browsers[0]
        print(f"🚀 Используется браузер: {selected_browser[1]}")
        
        try:
            # Автоматическая установка и настройка драйвера
            driver_path = ChromeDriverManager(chrome_type=selected_browser[2]).install()
            service = webdriver.chrome.service.Service(driver_path)
            
            # Настройки для разных ОС
            options = webdriver.ChromeOptions()
            
            if self._detect_os() in ["linux", "redos"]:
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--remote-debugging-port=9222')
            
            # Общие настройки
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 15)
            print(f"✅ Драйвер для {selected_browser[1]} успешно настроен")
            
        except Exception as e:
            print(f"❌ Ошибка настройки драйвера: {e}")
            # Попытка использовать следующий браузер
            if len(browsers) > 1:
                print("Попытка использовать следующий браузер...")
                selected_browser = browsers[1]
                try:
                    driver_path = ChromeDriverManager(chrome_type=selected_browser[2]).install()
                    service = webdriver.chrome.service.Service(driver_path)
                    self.driver = webdriver.Chrome(service=service)
                    self.wait = WebDriverWait(self.driver, 15)
                    print(f"✅ Драйвер для {selected_browser[1]} успешно настроен")
                except Exception as e2:
                    print(f"❌ Критическая ошибка: {e2}")
                    sys.exit(1)
            else:
                sys.exit(1)
    

    def _setup_templates(self):
        """Настройка шаблонов текста"""
        return {
            'living': "Санитарные условия удовлетворительные, для детей имеется отдельное спальное место, место для занятий и отдыха. Продукты питания в достаточном количестве.",
            'category_family': "полная, многодетная"
        }


    # ===== NEW METHODS FOR USER INPUT =====
    
    def get_children_education(self, children):
        """Запрос места учебы для каждого ребенка"""
        print("\n" + "="*50)
        print("Информация о месте учебы детей:")
        print("Нажмите Enter для пропуска, если информация отсутствует")
        print("="*50)
        
        children_with_education = []
        
        for child in children:
            education = input(f"Место учебы для {child['full_name']}: ").strip()
            child['education'] = education
            children_with_education.append(child)
            
        return children_with_education
    
    def get_adpi_info_with_skip(self):
        """Получение информации об АДПИ с возможностью пропуска"""
        print("\n" + "="*50)
        print("Информация об АДПИ:")
        print("Нажмите Enter для пропуска, если информация отсутствует")
        print("="*50)
        
        has_adpi = self._get_yes_no_input("АДПИ установлен? (д/н): ")
        
        adpi_dates = {}
        if has_adpi == 'д':
            install_date = input("Дата установки АДПИ (ДД.ММ.ГГГГ или Enter для пропуска): ").strip()
            if install_date and self._validate_date(install_date):
                adpi_dates['install'] = install_date
            
            check_date = input("Дата последней проверки АДПИ (ДД.ММ.ГГГГ или Enter для пропуска): ").strip()
            if check_date and self._validate_date(check_date):
                adpi_dates['check'] = check_date
        
        return has_adpi, adpi_dates
    
    def get_housing_info(self):
        """Получение подробной информации о жилье"""
        print("\n" + "="*50)
        print("Информация о жилье:")
        print("="*50)
        
        # Количество комнат
        while True:
            rooms = input("Сколько комнат? ").strip()
            if rooms:
                break
            print("Пожалуйста, введите количество комнат")
        
        # Площадь
        while True:
            square = input("Сколько кв.м.? ").strip()
            if square:
                break
            print("Пожалуйста, введите площадь")
        
        # Удобства
        has_amenities = self._get_yes_no_input("Со всеми удобствами? (д/н): ")
        amenities_text = "со всеми удобствами" if has_amenities == 'д' else "с частичными удобствами"
        
        # Собственник
        while True:
            owner = input("Кому принадлежит? ").strip()
            if owner:
                break
            print("Пожалуйста, укажите собственника")
        
        housing_text = f"{rooms} комнат, {square} кв.м., {amenities_text}, в собственности у {owner}"
        return housing_text
    
    # ===== UPDATED METHODS =====
    
    def get_family_info_from_user(self):
        """Получение информации о семье от пользователя с местом учебы"""
        print("\n" + "="*50)
        print("Введите данные о членах семьи:")
        print("Формат: Фамилия Имя Отчество ДатаРождения")
        print("Пример: Березин Арсений Евгеньевич 08.10.2019")
        print("Введите пустую строку для завершения ввода")
        print("="*50)
        
        input_text = self._get_multiline_input()
        
        if not input_text:
            print("Не удалось распознать данные о семье. Используется стандартный шаблон.")
            return self._get_default_add_info(), self.templates['category_family']
        
        people = self._parse_family_data(input_text)
        mother, father, children = self._identify_family_members(people)
        
        # Запрашиваем место учебы для детей
        children_with_education = self.get_children_education(children)
        
        category_family = "полная, многодетная" if father else "неполная, многодетная"
        add_info_text = self._create_add_info_text_with_education(mother, father, children_with_education)
        
        self._print_family_summary(mother, father, children_with_education)
        
        return add_info_text, category_family
    
    def _create_add_info_text_with_education(self, mother, father, children):
        """Создание текста с учетом места учебы детей"""
        lines = []
        
        # Родители
        if mother:
            lines.extend([f"Мать: {mother['full_name']} {mother['birth_date']}", "Работает: "])
        else:
            lines.extend(["Мать: ", "Работает: "])
        
        if father:
            lines.extend([f"Отец: {father['full_name']} {father['birth_date']}", "Работает: "])
        
        # Дети с местом учебы
        lines.append("Дети:")
        for child in children:
            education_suffix = f" - {child['education']}" if child.get('education') else " -"
            lines.append(f"    {child['full_name']} {child['birth_date']}{education_suffix}")
        
        # Доходы
        lines.extend([
            "Доход:", "з/п матери -", 
            *(["з/п отца -"] if father else []),
            "единое пособие -", "пособие по многодетности -", "пенсия по потере кормильца -"
        ])
        
        return "\n".join(lines)
    
    def _print_family_summary(self, mother, father, children):
        """Вывод сводки о семье с местом учебы"""
        print("\nОпределены следующие члены семьи:")
        if mother:
            print(f"Мать: {mother['full_name']} {mother['birth_date']}")
        if father:
            print(f"Отец: {father['full_name']} {father['birth_date']}")
        print(f"Дети: {len(children)}")
        for child in children:
            education_info = f" - {child['education']}" if child.get('education') else ""
            print(f"  - {child['full_name']} {child['birth_date']}{education_info}")
    
    # ===== UPDATED AUTOMATION FLOW =====
    
    def run_automation(self):
        """Запуск полного цикла автоматизации с новыми функциями"""
        try:
            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
            self.login()
            
            while True:
                if not self.wait_for_user_command():
                    break
                
                print("\nНачинаем автоматизацию...")
                
                # Получение данных
                add_info_text, category_family = self.get_family_info_from_user()
                has_adpi, adpi_dates = self.get_adpi_info_with_skip()
                housing_info = self.get_housing_info()
                phone_number, address, housing_type = self.navigate_to_form()
                
                print(f"Определен тип жилья: {housing_type}")
                
                # Работа с формой
                self.click_checkboxes(has_adpi)
                self._click_element(By.ID, "ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_ctl06_AJOk")
                time.sleep(3)
                
                # Заполнение полей
                self.fill_all_fields(phone_number, address, housing_info, add_info_text, category_family, has_adpi, adpi_dates)
                
                print("\n✅ Автоматизация завершена успешно!")
                
                if not self._ask_for_repeat():
                    break
                    
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")
        finally:
            print("\nЗавершение работы...")
            self.driver.quit()
    
    def fill_all_fields(self, phone_number, address, housing_info, add_info_text, category_family, has_adpi, adpi_dates):
        """Заполнение всех полей формы с обновленной информацией о жилье"""
        print("Заполняем поля формы...")
        time.sleep(2)
        
        # Основные поля
        self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True)
        
        # Телефон
        if phone_number:
            self._fill_field(By.NAME, "ctl00$cph$ctrlDopFields$gv$ctl02$tb", phone_number)
        
        # АДПИ поля
        self._fill_adpi_fields_with_skip(has_adpi, adpi_dates)
        
        # Дополнительные поля
        field_mappings = {
            "ctl00$cph$ctrlDopFields$gv$ctl04$tb": category_family,
            "ctl00$cph$ctrlDopFields$gv$ctl05$tb": address,
            "ctl00$cph$ctrlDopFields$gv$ctl08$tb": housing_info,
            "ctl00$cph$ctrlDopFields$gv$ctl09$tb": self.templates['living']
        }
        
        for field_name, text in field_mappings.items():
            self._fill_field(By.NAME, field_name, text)
    
    def _fill_adpi_fields_with_skip(self, has_adpi, adpi_dates):
        """Заполнение полей АДПИ с учетом пропущенных дат"""
        if has_adpi == 'д':
            # Выбираем радиокнопку "Да"
            self._click_element(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0")
            time.sleep(1)
            
            # Заполняем дату установки АДПИ только если она указана
            if adpi_dates.get('install'):
                self._fill_date_field_enhanced(
                    "igtxtctl00_cph_ctrlDopFields_gv_ctl06_wdte", 
                    adpi_dates['install'],
                    "установки АДПИ"
                )
                time.sleep(1)
            else:
                print("✓ Дата установки АДПИ пропущена")
            
            # Заполняем дату проверки АДПИ только если она указана
            if adpi_dates.get('check'):
                self._fill_date_field_enhanced(
                    "igtxtctl00_cph_ctrlDopFields_gv_ctl07_wdte", 
                    adpi_dates['check'],
                    "проверки АДПИ"
                )
            else:
                print("✓ Дата проверки АДПИ пропущена")
        else:
            # Выбираем радиокнопку "Нет"
            self._click_element(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_1")
    
    # ===== EXISTING HELPER METHODS (без изменений) =====
    
    def _get_yes_no_input(self, prompt):
        """Получение да/нет ответа от пользователя"""
        while True:
            response = input(prompt).strip().lower()
            if response in ['д', 'н']:
                return response
            print("Пожалуйста, введите 'д' или 'н'")
    
    def _get_multiline_input(self):
        """Получение многострочного ввода от пользователя"""
        lines = []
        while True:
            line = input().strip()
            if not line:
                break
            lines.append(line)
        return "\n".join(lines)
    
    def _get_command_input(self, valid_commands, prompt):
        """Получение команды от пользователя"""
        while True:
            command = input(prompt).strip().lower()
            if command in valid_commands:
                return command
            print(f"Неизвестная команда. Допустимые: {', '.join(valid_commands)}")
    
    def _ask_for_repeat(self):
        """Запрос на повторение автоматизации"""
        repeat = input("\nВведите 'с' для повторения или любую клавишу для выхода: ").strip().lower()
        if repeat == 'с':
            print("Подготовка к повторной автоматизации...")
            return True
        return False
    
    def _validate_date(self, date_string):
        """Проверка корректности даты"""
        try:
            datetime.strptime(date_string, '%d.%m.%Y')
            return True
        except ValueError:
            return False
    
    def _parse_family_data(self, input_text):
        """Парсинг введенных данных о семье"""
        people = []
        for line in input_text.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 4:
                people.append({
                    'last_name': parts[0],
                    'first_name': parts[1],
                    'patronymic': parts[2],
                    'birth_date': parts[3],
                    'full_name': f"{parts[0]} {parts[1]} {parts[2]}"
                })
        return people
    
    def _identify_family_members(self, people):
        """Идентификация родителей и детей"""
        today = date.today()
        parents, children = [], []
        
        for person in people:
            try:
                birth_date = datetime.strptime(person['birth_date'], '%d.%m.%Y').date()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                (parents if age >= 18 else children).append(person)
            except ValueError:
                children.append(person)
        
        mother, father = self._identify_parents(parents)
        return mother, father, children
    
    def _identify_parents(self, parents):
        """Идентификация матери и отца"""
        mother = father = None
        
        for parent in parents:
            if parent['patronymic'].endswith('на') or parent['last_name'].endswith('а'):
                mother = parent
            else:
                father = parent
        
        # Резервные стратегии идентификации
        if not mother and parents:
            mother = next((p for p in parents if p['last_name'].endswith('а')), parents[0])
        
        return mother, father
    
    def _get_default_add_info(self):
        """Получение стандартного шаблона дополнительной информации"""
        return """Мать: 
Работает: 
Отец:
Работает:
Дети:
Доход:
з/п матери -
з/п отца - 
единое пособие - 
пособие по многодетности - 
пенсия по потере кормильца - 
"""
    
    def _determine_housing_type(self, address):
        """Определяет тип жилья на основе адреса"""
        return "квартира" if any(word in address.lower() for word in ['кв.', 'квартира', 'кв ', 'кв,']) else "дом"
    
    def _get_element_text(self, element_id, default=""):
        """Безопасное получение текста элемента"""
        try:
            return self.driver.find_element(By.ID, element_id).text
        except:
            return default
    
    def _fill_field(self, by, selector, text, press_enter=False):
        """Заполнение поля с обработкой ошибок"""
        try:
            field = self.wait.until(EC.element_to_be_clickable((by, selector)))
            field.clear()
            field.send_keys(text + (Keys.ENTER if press_enter else ""))
            print(f"✓ Заполнено поле: {selector}")
            return True
        except Exception as e:
            print(f"✗ Ошибка заполнения поля {selector}: {e}")
            return False
    
    def _fill_textarea(self, field_name, text, resize=False):
        """Заполнение текстовой области с возможностью изменения размера"""
        if self._fill_field(By.NAME, field_name, text):
            if resize:
                field = self.driver.find_element(By.NAME, field_name)
                self.driver.execute_script("""
                    arguments[0].style.height = '352px';
                    arguments[0].style.width = '1151px';
                """, field)
            return True
        return False
    
    def _fill_date_field_enhanced(self, field_id, date_text, field_name):
        """Улучшенное заполнение поля даты"""
        try:
            print(f"Заполняем поле {field_name} датой: {date_text}")
            
            field = self.wait.until(EC.element_to_be_clickable((By.ID, field_id)))
            
            # Используем ActionChains для надежного ввода
            actions = ActionChains(self.driver)
            
            # Кликаем и очищаем поле
            field.click()
            time.sleep(0.5)
            field.send_keys(Keys.CONTROL + "a")
            field.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            # Вводим дату по частям
            for char in date_text:
                actions.send_keys(char)
                actions.pause(0.1)
            actions.perform()
            
            print(f"✓ Ввели дату: {date_text}")
            time.sleep(0.5)
            
            # Сохраняем разными способами
            save_attempts = [
                lambda: field.send_keys(Keys.ENTER),
                lambda: field.send_keys(Keys.TAB),
                lambda: self.driver.execute_script("arguments[0].blur();", field),
            ]
            
            for i, attempt in enumerate(save_attempts):
                try:
                    attempt()
                    time.sleep(1)
                    
                    current_value = field.get_attribute('value')
                    if current_value and current_value != "__.__.____":
                        print(f"✅ Поле {field_name} заполнено: {current_value}")
                        return True
                        
                except Exception as e:
                    print(f"⚠️ Способ {i+1} не сработал: {e}")
            
            print(f"❌ Не удалось заполнить поле {field_name}")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка заполнения поля {field_name}: {e}")
            return False
    
    def _click_element(self, by, selector):
        """Клик по элементу с обработкой ошибок"""
        try:
            element = self.wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            print(f"✓ Кликнут элемент: {selector}")
            return True
        except Exception as e:
            print(f"✗ Ошибка клика по элементу {selector}: {e}")
            return False
    
    def _click_checkbox(self, checkbox_id):
        """Клик по чекбоксу с обработкой обновления страницы"""
        try:
            checkbox = self.wait.until(
                EC.element_to_be_clickable((By.ID, f"ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_{checkbox_id}"))
            )
            
            self.driver.execute_script("arguments[0].scrollIntoView();", checkbox)
            
            if not checkbox.is_selected():
                checkbox.click()
                print(f"✓ Отмечен чекбокс {checkbox_id}")
            
            self.wait.until(EC.staleness_of(checkbox))
            return True
            
        except Exception as e:
            print(f"✗ Ошибка с чекбоксом {checkbox_id}: {e}")
            return False
    
    def click_checkboxes(self, has_adpi):
        """Отметка нужных чекбоксов с учетом АДПИ"""
        print("Отмечаем чекбоксы...")
        
        target_ids = [8, 12, 13, 14, 17, 18]
        if has_adpi == 'д':
            target_ids.extend([15, 16])
        
        for checkbox_id in target_ids:
            self._click_checkbox(checkbox_id)
    
    def login(self):
        """Выполнение входа в систему"""
        print("Выполняем вход в систему...")
        
        self._fill_field(By.NAME, "tbUserName", "СРЦ_Вол")
        self._fill_field(By.NAME, "tbPassword", "СРЦ_Вол1", press_enter=True)
        
        print("Вход выполнен успешно!")
    
    def wait_for_user_command(self):
        """Ожидание команды от пользователя"""
        print("\n" + "="*50)
        print("Автоматизация готова к работе!")
        print("Перейдите на нужную страницу вручную...")
        print("Команды:")
        print("  'с' - начать автоматизацию")
        print("  'в' - выход из программы")
        print("="*50)
        
        return self._get_command_input(['с', 'в'], "Введите команду: ") == 'с'
    
    def navigate_to_form(self):
        """Навигация по форме"""
        print("Переходим к форме...")
        
        phone_number = self._get_element_text("ctl00_cph_lblMobilPhone")
        address = self._get_element_text("ctl00_cph_lblRegAddress", "Адрес не найден")
        housing_type = self._determine_housing_type(address)
        
        self._click_element(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL")
        self._click_element(By.ID, "ctl00_cph_lbtnEditAddInfo")
        self._click_element(By.ID, "ctl00_cph_ctrlDopFields_lbtnAdd")
        
        return phone_number, address, housing_type


# Запуск программы
if __name__ == "__main__":
    print("=" * 60)
    print("Автоматизатор форм - Загрузка...")
    print(f"ОС: {platform.system()} {platform.release()}")
    print("=" * 60)
    
    try:
        filler = AutoFormFiller()
        filler.run_automation()
    except KeyboardInterrupt:
        print("\n⏹️ Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("Попробуйте переустановить драйверы: запустите install.bat заново")
    finally:
        if 'filler' in locals() and filler.driver:
            filler.driver.quit()