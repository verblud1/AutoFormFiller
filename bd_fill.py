from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support import expected_conditions as EC
import time

class AutoFormFiller:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        self.templates = self._setup_templates()
        
    def _setup_templates(self):
        """Настройка шаблонов текста"""
        return {
            'add_info': """Мать: 
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
""",
            'housing': ", комнат, кв.м., со всеми удобствами, в собственности у ",
            'living': "Санитарные условия удовлетворительные, для детей имеется отдельное спальное место, место для занятий и отдыха. Продукты питания в достаточном количестве.",
            'category_family': "полная, многодетная"
        }
    
    
    def login(self):
        """Выполнение входа в систему"""
        print("Выполняем вход в систему...")
        
        username = self.wait.until(
            EC.element_to_be_clickable((By.NAME, "tbUserName"))
        )
        username.clear()
        username.send_keys("СРЦ_Вол")
        
        password = self.wait.until(
            EC.element_to_be_clickable((By.NAME, "tbPassword"))
        )
        password.clear()
        password.send_keys("СРЦ_Вол1" + Keys.ENTER)
        
        print("Вход выполнен успешно!")
    

    def wait_for_user_command(self):
        """Ожидание команды от пользователя"""
        print("\n" + "="*50)
        print("Автоматизация готова к работе!")
        print("Перейдите на нужную страницу вручную...")
        print("Команды:")
        print("  's' - начать автоматизацию")
        print("  'e' - выход из программы")
        print("="*50)
        
        while True:
            command = input("Введите команду: ").strip().lower()
            if command == 's':
                return True
            elif command == 'e':
                return False
            else:
                print("Неизвестная команда. Введите 's' или 'e'")
    

    def get_element_text(self, element_id, default=""):
        """Безопасное получение текста элемента"""
        try:
            element = self.driver.find_element(By.ID, element_id)
            return element.text
        except:
            return default
    

    def click_checkboxes(self):
        """Отметка нужных чекбоксов"""
        print("Отмечаем чекбоксы...")
        
        target_ids = [8, 12, 13, 14, 15, 16, 17, 18]
        
        for checkbox_id in target_ids:
            try:
                checkbox = self.wait.until(
                    EC.element_to_be_clickable((By.ID, f"ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_{checkbox_id}"))
                )
                
                self.driver.execute_script("arguments[0].scrollIntoView();", checkbox)
                
                if not checkbox.is_selected():
                    checkbox.click()
                    print(f"✓ Отмечен чекбокс {checkbox_id}")
                
                # Ждем обновления страницы
                self.wait.until(EC.staleness_of(checkbox))
                
            except Exception as e:
                print(f"✗ Ошибка с чекбоксом {checkbox_id}: {e}")
                continue
    
    
    def fill_text_field(self, field_name, text):
        """Заполнение текстового поля"""
        try:
            field = self.wait.until(
                EC.element_to_be_clickable((By.NAME, field_name))
            )
            field.clear()
            field.send_keys(text)
            print(f"✓ Заполнено поле: {field_name.split('$')[-1]}")
        except Exception as e:
            print(f"✗ Ошибка заполнения поля {field_name}: {e}")
    

    def navigate_to_form(self):
        """Навигация по форме"""
        print("Переходим к форме...")
        
        # Получение данных
        phone_number = self.get_element_text("ctl00_cph_lblMobilPhone")
        address = self.get_element_text("ctl00_cph_lblRegAddress", "Адрес не найден")
        
        # Переход по вкладкам
        self.wait.until(
            EC.element_to_be_clickable((By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL"))
        ).click()
        
        
        
        # Редактирование
        self.wait.until(
            EC.element_to_be_clickable((By.ID, "ctl00_cph_lbtnEditAddInfo"))
        ).click()
        
        self.wait.until(
            EC.element_to_be_clickable((By.ID, "ctl00_cph_ctrlDopFields_lbtnAdd"))
        ).click()
        
        return phone_number, address
    

    def fill_all_fields(self, phone_number, address):
        """Заполнение всех полей формы"""
        print("Заполняем поля формы...")
        
        # Основные поля
        self.fill_text_field("ctl00$cph$tbAddInfo", self.templates['add_info'])
        
        # Телефон (если есть)
        # Дополнительная проверка для отладки
        if phone_number:
            print(f"Найден телефон: {phone_number}")
            self.fill_text_field("ctl00$cph$ctrlDopFields$gv$ctl02$tb", phone_number)
        else:
            print("Телефон не найден на странице")
        
        # Дополнительные поля
        fields_mapping = {
            "ctl00$cph$ctrlDopFields$gv$ctl04$tb": self.templates['category_family'],
            "ctl00$cph$ctrlDopFields$gv$ctl05$tb": address,
            "ctl00$cph$ctrlDopFields$gv$ctl08$tb": self.templates['housing'],
            "ctl00$cph$ctrlDopFields$gv$ctl09$tb": self.templates['living']
        }
        
        for field_name, text in fields_mapping.items():
            self.fill_text_field(field_name, text)
    

    def run_automation(self):
        """Запуск полного цикла автоматизации"""
        try:
            # Начальная настройка
            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
            self.login()
            
            # Главный цикл автоматизации
            while True:
                if not self.wait_for_user_command():
                    break
                
                print("\nНачинаем автоматизацию...")
                
                # Навигация и получение данных
                phone_number, address = self.navigate_to_form()
                
                # Работа с чекбоксами
                self.click_checkboxes()
                
                # Подтверждение выбора чекбоксов
                self.wait.until(
                    EC.element_to_be_clickable((By.ID, "ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_ctl06_AJOk"))
                ).click()
                
                # Заполнение полей
                self.fill_all_fields(phone_number, address)
                
                print("\n✅ Автоматизация завершена успешно!")
                
                # Запрос на повторение
                repeat = input("\nВведите 're' для повторения или любую клавишу для выхода: ").strip().lower()
                if repeat != 're':
                    break
                else:
                    print("Подготовка к повторной автоматизации...")
                    
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")
            
        finally:
            print("\nЗавершение работы...")
            self.driver.quit()


# Запуск программы
if __name__ == "__main__":
    filler = AutoFormFiller()
    filler.run_automation()