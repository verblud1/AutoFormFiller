from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, date
import time

class AutoFormFiller:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        self.templates = self._setup_templates()
        
    def _setup_templates(self):
        """Настройка шаблонов текста"""
        return {
            'housing': ", комнат, кв.м., со всеми удобствами, в собственности у ",
            'living': "Санитарные условия удовлетворительные, для детей имеется отдельное спальное место, место для занятий и отдыха. Продукты питания в достаточном количестве.",
            'category_family': "полная, многодетная"
        }
    
    # ===== USER INPUT METHODS =====
    
    def get_adpi_info(self):
        """Получение информации об АДПИ от пользователя"""
        print("\n" + "="*50)
        print("Информация об АДПИ:")
        
        has_adpi = self._get_yes_no_input("АДПИ установлен? (д/н): ")
        
        adpi_dates = {}
        if has_adpi == 'д':
            adpi_dates['install'] = self._get_date_input("Дата установки АДПИ")
            adpi_dates['check'] = self._get_date_input("Дата последней проверки АДПИ")
        
        return has_adpi, adpi_dates
    
    def get_family_info_from_user(self):
        """Получение информации о семье от пользователя"""
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
        
        category_family = "полная, многодетная" if father else "неполная, многодетная"
        add_info_text = self._create_add_info_text(mother, father, children)
        
        self._print_family_summary(mother, father, children)
        
        return add_info_text, category_family
    
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
    
    # ===== FORM INTERACTION METHODS =====
    
    def login(self):
        """Выполнение входа в систему"""
        print("Выполняем вход в систему...")
        
        self._fill_field(By.NAME, "tbUserName", "СРЦ_Вол")
        self._fill_field(By.NAME, "tbPassword", "СРЦ_Вол1", press_enter=True)
        
        print("Вход выполнен успешно!")
    
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
    
    def fill_all_fields(self, phone_number, address, housing_type, add_info_text, category_family, has_adpi, adpi_dates):
        """Заполнение всех полей формы"""
        print("Заполняем поля формы...")
        time.sleep(2)
        
        # Основные поля
        self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True)
        
        # Телефон
        if phone_number:
            self._fill_field(By.NAME, "ctl00$cph$ctrlDopFields$gv$ctl02$tb", phone_number)
        
        # АДПИ поля
        self._fill_adpi_fields(has_adpi, adpi_dates)
        
        # Дополнительные поля
        housing_text = f"{housing_type}{self.templates['housing']}"
        field_mappings = {
            "ctl00$cph$ctrlDopFields$gv$ctl04$tb": category_family,
            "ctl00$cph$ctrlDopFields$gv$ctl05$tb": address,
            "ctl00$cph$ctrlDopFields$gv$ctl08$tb": housing_text,
            "ctl00$cph$ctrlDopFields$gv$ctl09$tb": self.templates['living']
        }
        
        for field_name, text in field_mappings.items():
            self._fill_field(By.NAME, field_name, text)
    
    def click_checkboxes(self, has_adpi):
        """Отметка нужных чекбоксов с учетом АДПИ"""
        print("Отмечаем чекбоксы...")
        
        target_ids = [8, 12, 13, 14, 17, 18]
        if has_adpi == 'д':
            target_ids.extend([15, 16])
        
        for checkbox_id in target_ids:
            self._click_checkbox(checkbox_id)
    
    # ===== CORE AUTOMATION =====
    
    def run_automation(self):
        """Запуск полного цикла автоматизации"""
        try:
            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
            self.login()
            
            while True:
                if not self.wait_for_user_command():
                    break
                
                print("\nНачинаем автоматизацию...")
                
                # Получение данных
                add_info_text, category_family = self.get_family_info_from_user()
                has_adpi, adpi_dates = self.get_adpi_info()
                phone_number, address, housing_type = self.navigate_to_form()
                
                print(f"Определен тип жилья: {housing_type}")
                
                # Работа с формой
                self.click_checkboxes(has_adpi)
                self._click_element(By.ID, "ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_ctl06_AJOk")
                time.sleep(3)
                
                # Заполнение полей
                self.fill_all_fields(phone_number, address, housing_type, add_info_text, category_family, has_adpi, adpi_dates)
                
                print("\n✅ Автоматизация завершена успешно!")
                
                if not self._ask_for_repeat():
                    break
                    
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")
        finally:
            print("\nЗавершение работы...")
            self.driver.quit()
    
    # ===== PRIVATE HELPER METHODS =====
    
    def _get_yes_no_input(self, prompt):
        """Получение да/нет ответа от пользователя"""
        while True:
            response = input(prompt).strip().lower()
            if response in ['д', 'н']:
                return response
            print("Пожалуйста, введите 'д' или 'н'")
    
    def _get_date_input(self, prompt):
        """Получение даты от пользователя"""
        while True:
            date_str = input(f"{prompt} (в формате ДД.ММ.ГГГГ): ").strip()
            if self._validate_date(date_str):
                return date_str
            print("Неверный формат даты. Используйте ДД.ММ.ГГГГ")
    
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
    
    def _create_add_info_text(self, mother, father, children):
        """Создание текста для поля дополнительной информации"""
        lines = []
        
        # Родители
        if mother:
            lines.extend([f"Мать: {mother['full_name']} {mother['birth_date']}", "Работает: "])
        else:
            lines.extend(["Мать: ", "Работает: "])
        
        if father:
            lines.extend([f"Отец: {father['full_name']} {father['birth_date']}", "Работает: "])
        
        # Дети
        lines.append("Дети:")
        lines.extend(f"    {child['full_name']} {child['birth_date']} -" for child in children)
        
        # Доходы
        lines.extend([
            "Доход:", "з/п матери -", 
            *(["з/п отца -"] if father else []),
            "единое пособие -", "пособие по многодетности -", "пенсия по потере кормильца -"
        ])
        
        return "\n".join(lines)
    
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
    
    def _print_family_summary(self, mother, father, children):
        """Вывод сводки о семье"""
        print("\nОпределены следующие члены семьи:")
        if mother:
            print(f"Мать: {mother['full_name']} {mother['birth_date']}")
        if father:
            print(f"Отец: {father['full_name']} {father['birth_date']}")
        print(f"Дети: {len(children)}")
        for child in children:
            print(f"  - {child['full_name']} {child['birth_date']}")
    
    def _determine_housing_type(self, address):
        """Определяет тип жилья на основе адреса"""
        return "квартира" if any(word in address.lower() for word in ['кв.', 'квартира', 'кв ', 'кв,']) else "дом"
    
    def _get_element_text(self, element_id, default=""):
        """Безопасное получение текста элемента"""
        try:
            return self.driver.find_element(By.ID, element_id).text
        except:
            return default
    
    # ===== SELENIUM INTERACTION METHODS =====
    
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
    
    def _fill_date_field(self, field_id, date_text):
        """Заполнение поля даты с нажатием Enter"""
        return self._fill_field(By.ID, field_id, date_text, press_enter=True)
    
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
    
    def _fill_adpi_fields(self, has_adpi, adpi_dates):
        """Заполнение полей АДПИ с улучшенным подходом"""
        if has_adpi == 'д':
            # Выбираем радиокнопку "Да"
            self._click_element(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0")
            time.sleep(1)
            
            # Заполняем дату установки АДПИ
            self._fill_date_field_enhanced(
                "igtxtctl00_cph_ctrlDopFields_gv_ctl06_wdte", 
                adpi_dates['install'],
                "установки АДПИ"
            )
            
            time.sleep(1)
            
            # Заполняем дату проверки АДПИ
            self._fill_date_field_enhanced(
                "igtxtctl00_cph_ctrlDopFields_gv_ctl07_wdte", 
                adpi_dates['check'],
                "проверки АДПИ"
            )
        else:
            # Выбираем радиокнопку "Нет"
            self._click_element(By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_1")

    def _fill_date_field_enhanced(self, field_id, date_text, field_name):
        """Специализированное заполнение поля даты с маской"""
        try:
            print(f"Заполняем поле {field_name} датой: {date_text}")
            
            # Находим поле
            field = self.wait.until(EC.element_to_be_clickable((By.ID, field_id)))
            
            # Метод 1: Ввод с помощью Actions (более надежный)
            from selenium.webdriver.common.action_chains import ActionChains
            
            # Кликаем на поле
            field.click()
            time.sleep(0.5)
            
            # Очищаем поле с помощью Ctrl+A + Delete
            field.send_keys(Keys.CONTROL + "a")
            field.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            # Вводим дату по частям (день.месяц.год)
            actions = ActionChains(self.driver)
            for char in date_text:
                actions.send_keys(char)
                actions.pause(0.1)  # Небольшая пауза между символами
            actions.perform()
            
            print(f"✓ Ввели дату посимвольно: {date_text}")
            time.sleep(0.5)
            
            # Пробуем разные способы сохранения
            save_attempts = [
                lambda: field.send_keys(Keys.ENTER),
                lambda: field.send_keys(Keys.TAB),
                lambda: field.send_keys(Keys.RETURN),
                lambda: self.driver.execute_script("arguments[0].blur();", field),
            ]
            
            for i, attempt in enumerate(save_attempts):
                try:
                    attempt()
                    time.sleep(1)
                    
                    # Проверяем результат
                    current_value = field.get_attribute('value')
                    if current_value and current_value != "__.__.____":
                        print(f"✅ Поле {field_name} заполнено (способ {i+1}): {current_value}")
                        return True
                        
                except Exception as e:
                    print(f"⚠️ Способ {i+1} не сработал: {e}")
            
            # Метод 2: Прямая установка через JavaScript с принудительными событиями
            print("Пробуем прямой JavaScript...")
            self.driver.execute_script(f"""
                var field = arguments[0];
                field.value = '{date_text}';
                
                // Создаем и вызываем все возможные события
                var events = ['input', 'change', 'blur', 'keydown', 'keyup', 'keypress', 'focusout'];
                events.forEach(function(eventType) {{
                    var event = new Event(eventType, {{ bubbles: true }});
                    field.dispatchEvent(event);
                }});
                
                // Также пробуем jQuery события если они используются
                if (typeof jQuery !== 'undefined') {{
                    $(field).trigger('input');
                    $(field).trigger('change');
                    $(field).trigger('blur');
                }}
            """, field)
            
            time.sleep(2)
            
            # Проверяем результат после JavaScript
            current_value = field.get_attribute('value')
            if current_value and current_value != "__.__.____":
                print(f"✅ Поле {field_name} заполнено через JavaScript: {current_value}")
                return True
            
            # Метод 3: Имитация реального пользовательского ввода
            print("Пробуем имитацию пользовательского ввода...")
            field.click()
            time.sleep(0.3)
            
            # Очищаем поле полностью
            field.send_keys(Keys.CONTROL + "a")
            field.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            # Вводим медленно, как пользователь
            for i, char in enumerate(date_text):
                field.send_keys(char)
                time.sleep(0.2)  # Пауза как у пользователя
                # После ввода каждой части даты делаем небольшую паузу
                if i in [1, 4]:  # После дня и месяца
                    time.sleep(0.3)
            
            # Переходим на другое поле чтобы сохранить
            field.send_keys(Keys.TAB)
            time.sleep(1)
            
            # Финальная проверка
            current_value = field.get_attribute('value')
            if current_value and current_value != "__.__.____":
                print(f"✅ Поле {field_name} заполнено имитацией пользователя: {current_value}")
                return True
            
            print(f"❌ Не удалось заполнить поле {field_name}. Текущее значение: {current_value}")
            return False
            
        except Exception as e:
            print(f"❌ Критическая ошибка заполнения поля {field_name}: {e}")
            return False
    
# Запуск программы
if __name__ == "__main__":
    filler = AutoFormFiller()
    filler.run_automation()