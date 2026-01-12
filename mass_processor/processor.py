"""Модуль для обработки данных в массовом обработчике семей"""

import json
import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import platform
import time
import pandas as pd
from utils.data_processing import clean_string, clean_fio, clean_date, clean_phone, clean_address, clean_numeric_field, parse_date
from utils.validation import validate_family_data
from utils.excel_utils import load_register_file, load_adpi_file, parse_adpi_date, parse_single_date, normalize_fio, is_fio_similar


class AutoFormFillerMass:
    """Класс для массовой обработки семей с улучшенной обработкой ошибок"""
    
    def __init__(self, gui_app):
        self.gui = gui_app
        self.driver = None
        self.wait = None
        self.screenshot_dir = None
        self.should_stop = False
        self.phone = ""
        self.address = ""
        
    def log(self, message):
        """Логирование в GUI"""
        self.gui.log_message(message)
        
    def stop_processing(self):
        """Остановка обработки"""
        self.should_stop = True
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def wait_for_manual_intervention(self, message):
        """Ожидание ручного вмешательства пользователя"""
        self.log(f"🛠️ {message}")
        
        self.gui.manual_intervention_required = True

        # Показываем сообщение пользователю
        messagebox.showinfo("Требуется ручное вмешательство",
                           f"{message}\n\n"
                           "Пожалуйста, перейдите на нужную страницу в браузере и нажмете 'Продолжить' в программе.")
        
        # Ждем, пока пользователь не нажмет "Продолжить"
        while self.gui.manual_intervention_required and not self.should_stop:
            time.sleep(0.5)
        
        return not self.should_stop
        
    def process_family(self, family_data, family_number):
        """Обработка одной семьи"""
        try:
            # 1. Возвращаемся на страницу поиска
            self.log("🔙 Возвращаемся на страницу поиска...")
            try:
                self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
                time.sleep(0.2)  # Уменьшено с 0.5 до 0.2 секунды
            except Exception as e:
                self.log(f"❌ Не удалось загрузить страницу поиска: {e}")
                
                # Запрашиваем ручное вмешательство
                if self.wait_for_manual_intervention("Не удалось загрузить страницу поиска"):
                    self.log("▶️ Продолжаем после ручного вмешательства")
                    # Проверяем, что страница доступна после ручного вмешательства
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, "ctl00_cph_ctrlFastFind_tbFind"))
                        )
                        self.log("✅ Страница поиска доступна после ручного вмешательства")
                    except:
                        self.log("❌ Страница поиска все еще недоступна после ручного вмешательства")
                        return False
                else:
                    return False
            
            # 2. Поиск семьи по ФИО матери
            mother_fio = family_data.get('mother_fio', '')
            father_fio = family_data.get('father_fio', '')
            
            # Если нет ФИО матери, используем ФИО отца для поиска
            search_fio = mother_fio if mother_fio else father_fio
            
            if not search_fio:
                self.log("❌ Не указано ФИО матери или отца")
                return False
                
            self.log(f"🔍 Поиск семьи: {search_fio}")
            
            # Выполняем поиск
            if not self._fast_search_mother(search_fio):
                self.log("❌ Не удалось найти семью")
                
                # Запрашиваем ручное вмешательство
                if self.wait_for_manual_intervention(f"Не удалось найти семью: {mother_fio}"):
                    self.log("▶️ Продолжаем после ручного вмешательства")
                    # Предполагаем, что пользователь уже на нужной странице
                else:
                    return False
            
            # 3. Анализ результатов поиска и автоматический выбор карточки
            self.log("🤖 Анализируем результаты поиска...")
            result = self._analyze_search_results(family_number, search_fio)
            
            if not result:
                self.log("❌ Не удалось автоматически выбрать карточку")
                
                # Запрашиваем ручное вмешательство
                if self.wait_for_manual_intervention("Не удалось автоматически выбрать карточку"):
                    self.log("▶️ Продолжаем после ручного вмешательства")
                    # Предполагаем, что пользователь уже на нужной карточке
                else:
                    return False
            
            # 4. ПЕРЕД ПЕРЕХОДОМ НА ДОПОЛНИТЕЛЬНУЮ ИНФОРМАЦИЮ - ПОЛУЧАЕМ ТЕЛЕФОН И АДРЕС
            # Ждем, пока страница карточки полностью загрузится
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: "CardInfo.aspx" in driver.current_url or "ПКУ" in driver.title or
                    driver.execute_script("return document.readyState") == "complete"
                )
                self.log("📱 Получаем телефон и адрес СРАЗУ ПОСЛЕ ПЕРЕХОДА НА КАРТОЧКУ...")
                
                # Получаем данные из family_data (из JSON)
                self._get_phone_and_address_from_family_data(family_data)
                
                # Также пытаемся получить со страницы (если не удалось из JSON)
                self._get_phone_and_address_from_page()
            except Exception as e:
                self.log(f"⚠️ Не удалось дождаться полной загрузки карточки или получить данные: {e}")
                # Возвращаемся на страницу поиска
                self._return_to_search_page()
                return False
            
            # 5. Проверка и заполнение данных
            if not self._check_additional_info_empty():
                if not self._warn_existing_data():
                    self.log("⚠️ Пропускаем - данные уже существуют")
                    # Возвращаемся на страницу поиска
                    self._return_to_search_page()
                    return True  # Возвращаем True, так как это не ошибка
                    
            # 6. Навигация к форме дополнительной информации
            self.log("🔄 Переходим на вкладку доп. информации...")
            if not self._navigate_to_additional_info():
                # Запрашиваем ручное вмешательство при ошибке навигации
                if self.wait_for_manual_intervention("Не удалось перейти на вкладку доп. информации"):
                    self.log("▶️ Продолжаем после ручного вмешательства")
                    # Предполагаем, что пользователь уже на нужной форме
                else:
                    return False
                
            # 7. Форматирование данных семьи (с доходами)
            formatted_data = self._format_family_data(family_data)
            
            # 8. Заполнение формы
            if not self._fill_form(*formatted_data):
                self.log("❌ Ошибка заполнения формы")
                return False
            
            # 9. Сохранение
            if self._final_verification(family_data):
                if self._save_and_exit():
                    # 10. Скриншот
                    if self.screenshot_dir:
                        self._take_screenshot(formatted_data, family_number, family_data)

                    # 11. Возвращаемся на страницу поиска без закрытия браузера
                    time.sleep(0.2)
                    self._return_to_search_page()

                    self.log("✅ Семья обработана успешно")
                    return True
            return False
            
        except Exception as e:
            self.log(f"❌ Ошибка при обработке семьи: {str(e)}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _get_phone_and_address_from_family_data(self, family_data):
        """Получение телефона и адреса из данных семьи (JSON)"""
        try:
            # Телефон из данных
            phone_from_data = family_data.get('phone', '')
            if phone_from_data:
                self.phone = phone_from_data
                self.log(f"📱 Используем телефон из JSON данных: {self.phone}")
            else:
                self.log("⚠️ Телефон не найден в JSON данных")
                self.phone = ""
            
            # Адрес из данных
            address_from_data = family_data.get('address', '')
            if address_from_data:
                self.address = address_from_data
                self.log(f"🏠 Используем адрес из JSON данных: {self.address}")
            else:
                self.log("⚠️ Адрес не найден в JSON данных")
                self.address = ""
                
        except Exception as e:
            self.log(f"⚠️ Ошибка получения данных из JSON: {e}")
            self.phone = ""
            self.address = ""
    
    def _get_phone_and_address_from_page(self):
        """Дополнительная попытка получить телефон и адрес со страницы"""
        try:
            # Если телефон из JSON не получен, пытаемся со страницы
            if not self.phone:
                try:
                    # Ждем появления элемента телефона
                    phone_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "ctl00_cph_lblMobilPhone"))
                    )
                    phone_text = phone_element.text.strip() if phone_element else ""
                    if phone_text:
                        self.phone = phone_text
                        self.log(f"📱 Телефон со страницы: {self.phone}")
                except Exception as e:
                    self.log("⚠️ Телефон не найден на странице")
            
            # Если адрес из JSON не получен, пытаемся со страницы
            if not self.address or self.address == "Адрес не найден":
                try:
                    # Ждем появления элемента адреса
                    address_element = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.ID, "ctl00_cph_lblRegAddress"))
                    )
                    address_text = address_element.text.strip() if address_element else ""
                    if address_text:
                        self.address = address_text
                        self.log(f"🏠 Адрес со страницы: {self.address}")
                        
                        # Спрашиваем пользователя, верен ли адрес
                        result = messagebox.askyesno(
                            "Проверка адреса", 
                            f"Адрес верен?\n{self.address}\n\nЕсли нет - отредактируйте в следующих шагах."
                        )
                        
                        if not result:
                            address_dialog = ctk.CTkInputDialog(
                                text=f"Введите правильный адрес:",
                                title="Исправление адреса"
                            )
                            new_address = address_dialog.get_input()
                            if new_address:
                                self.address = new_address
                except Exception as e:
                    self.log("⚠️ Адрес не найден на странице")
                    if not self.address:
                        self.address = "Адрес не найден"
                        
        except Exception as e:
            self.log(f"⚠️ Ошибка получения данных со страницы: {e}")
    
    def _return_to_search_page(self):
        """Возврат на страницу поиска без закрытия браузера"""
        try:
            self.log("🔄 Возвращаемся на страницу поиска...")
            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
            
            # Ждем полной загрузки страницы
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Дополнительно ждем появление элемента поиска и проверяем, что он доступен для ввода
            search_element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "ctl00$cph$ctrlFastFind$tbFind"))
            )
            
            # Убедимся, что поле поиска пустое перед следующим использованием
            search_element.clear()
            
            # Дополнительно проверяем, что страница полностью загружена и готова к поиску
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_cph_dTabsContainer"))  # Убедимся, что контейнер результатов поиска присутствует
            )
            
            self.log("✅ Вернулись на страницу поиска")
        except Exception as e:
            self.log(f"⚠️ Не удалось вернуться на страницу поиска: {e}")
    
    def _analyze_search_results(self, family_number, mother_fio):
        """Анализ результатов поиска и автоматический выбор карточки"""
        try:
            # Добавляем дополнительное ожидание полной загрузки страницы результатов поиска
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Ждем появления контейнера с результатами поиска
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer"))
            )
            
            # Повторяем попытку нахождения карточек с несколькими попытками
            cards = None
            for attempt in range(3):
                try:
                    cards = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers"))
                    )
                    break
                except:
                    self.log(f"⚠️ Попытка {attempt + 1} нахождения карточек не удалась, ожидание и повтор...")
                    time.sleep(1)
                    continue
            
            if not cards:
                self.log("❌ Карточки не найдены")
                return False
                
            self.log(f"📊 Найдено карточек: {len(cards)}")
            
            # Убираем автоматический выбор первой карточки, если найдена только одна
            # Теперь будем искать карточки по приоритетам: "Вышневолоцкий городской округ" -> "Вышневолоцкий" -> "Вышний Волочек" -> выбор пользователем
            
            # Получаем свежий список карточек для анализа
            fresh_cards = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers")
            
            # Поиск по приоритетам
            vyishnevolotsk_ao_cards = []  # "Вышневолоцкий городской округ"
            vyishnevolotsk_cards = []     # "Вышневолоцкий"
            vyshniy_volochek_cards = []   # "Вышний Волочек"
            
            for i, card in enumerate(fresh_cards):
                try:
                    # Используем более надежный способ получения текста
                    fio = ""
                    try:
                        fio_element = card.find_element(By.CSS_SELECTOR, ".fio")
                        fio = fio_element.text if fio_element else ""
                    except:
                        # Альтернативный способ получения ФИО
                        try:
                            fio = card.text.split('\n')[0] if card.text else ""
                        except:
                            fio = f"Карточка {i+1}"
                    
                    address = ""
                    try:
                        details_table = card.find_element(By.CSS_SELECTOR, "table.tbl-details")
                        rows = details_table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2 and "Проживает:" in cells[0].text:
                                address = cells[1].text
                                break
                    except:
                        # Альтернативный способ получения адреса
                        address = card.text
                    
                    self.log(f"  Карточка {i+1}: {fio}")
                    self.log(f"    Адрес: {address[:50]}..." if len(address) > 50 else f"    Адрес: {address}")
                    
                    # Проверяем по приоритетам
                    address_lower = address.lower()
                    if "вышневолоцкий городской округ" in address_lower:
                        vyishnevolotsk_ao_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышневолоцкий городской округ")
                    elif "вышневолоцкий" in address_lower:
                        vyishnevolotsk_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышневолоцкий район")
                    elif "вышний волочек" in address_lower:
                        vyshniy_volochek_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышний Волочек")
                    elif "вышневолоцкий" in address_lower:
                        vyishnevolotsk_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышневолоцкий район (альтернативное написание)")
                    elif "вышнего волочка" in address_lower:
                        vyshniy_volochek_cards.append({
                            'index': i,
                            'card': card,
                            'fio': fio,
                            'address': address
                        })
                        self.log(f"    ✅ Подходит под Вышний Волочек (альтернативное написание)")
                        
                except Exception as e:
                    self.log(f"⚠️ Ошибка анализа карточки {i+1}: {e}")
                    continue
            
            # Проверяем карточки по приоритетам
            selected_cards = []
            priority_name = ""
            
            if vyishnevolotsk_ao_cards:
                selected_cards = vyishnevolotsk_ao_cards
                priority_name = "Вышневолоцкий городской округ"
                self.log(f"✅ Найдено {len(vyishnevolotsk_ao_cards)} карточек в {priority_name}")
            elif vyishnevolotsk_cards:
                selected_cards = vyishnevolotsk_cards
                priority_name = "Вышневолоцкий район"
                self.log(f"✅ Найдено {len(vyishnevolotsk_cards)} карточек в {priority_name}")
            elif vyshniy_volochek_cards:
                selected_cards = vyshniy_volochek_cards
                priority_name = "Вышний Волочек"
                self.log(f"✅ Найдено {len(vyshniy_volochek_cards)} карточек в {priority_name}")
            else:
                self.log("❌ Не найдено карточек в указанных районах (Вышневолоцкий городской округ, Вышневолоцкий район, Вышний Волочек)")
                # Получаем свежий список карточек для передачи в выбор
                fresh_cards_for_selection = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers")
                return self._show_cards_for_selection(fresh_cards_for_selection, family_number, mother_fio)
                
            # Обработка выбранного приоритета
            if len(selected_cards) == 1:
                self.log(f"✅ Найдена 1 карточка в {priority_name}")
                try:
                    # Используем свежую карточку из selected_cards
                    card = selected_cards[0]['card']
                    # Ищем ссылку с атрибутом title='Переход в просмотр ПКУ' с обработкой stale элементов
                    try:
                        links = card.find_elements(By.CSS_SELECTOR, "a[title='Переход в просмотр ПКУ']")
                    except Exception as e:
                        if "stale element reference" in str(e).lower():
                            # Получаем свежий список карточек и пробуем снова
                            fresh_cards = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers")
                            if len(fresh_cards) > selected_cards[0]['index']:
                                card = fresh_cards[selected_cards[0]['index']]
                                links = card.find_elements(By.CSS_SELECTOR, "a[title='Переход в просмотр ПКУ']")
                            else:
                                self.log("❌ Не удалось получить свежий список карточек")
                                return False
                        else:
                            raise e
                    
                    if len(links) > 0:
                        link = links[0]
                        # Получаем ID ссылки для использования в случае stale element reference
                        link_id = link.get_attribute("id")
                        
                        if link_id:
                            # Используем ID для получения свежего элемента перед кликом
                            try:
                                fresh_link = WebDriverWait(self.driver, 10).until(
                                    EC.element_to_be_clickable((By.ID, link_id))
                                )
                                # Прокручиваем к элементу перед кликом
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", fresh_link)
                                time.sleep(0.5)  # Небольшая задержка для завершения прокрутки
                                
                                # Используем JavaScript для клика, чтобы избежать stale element reference
                                try:
                                    self.driver.execute_script("arguments[0].click();", fresh_link)
                                except:
                                    # Если JavaScript клик не работает, используем обычный клик
                                    fresh_link.click()
                            except:
                                # Если не удается найти элемент по ID, используем JavaScript напрямую
                                link_script = f"document.querySelector('a[title=\"Переход в просмотр ПКУ\"][id=\"{link_id}\"]')"
                                try:
                                    self.driver.execute_script(f"({link_script}).click();")
                                except Exception as js_error:
                                    self.log(f"❌ Не удалось кликнуть через JavaScript по ID: {js_error}")
                                    # Попробуем универсальный селектор
                                    try:
                                        self.driver.execute_script("document.querySelector('a[title=\"Переход в просмотр ПКУ\"]').click();")
                                    except Exception as universal_error:
                                        self.log(f"❌ Не удалось кликнуть через универсальный селектор: {universal_error}")
                                        return False
                        else:
                            # Если у ссылки нет ID, используем общий селектор
                            try:
                                # Прокручиваем к элементу перед кликом
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", link)
                                time.sleep(0.5)  # Небольшая задержка для завершения прокрутки
                                
                                # Используем JavaScript для клика, чтобы избежать stale element reference
                                try:
                                    self.driver.execute_script("arguments[0].click();", link)
                                except:
                                    # Если JavaScript клик не работает, используем обычный клик
                                    link.click()
                            except Exception as click_error:
                                self.log(f"❌ Не удалось кликнуть на ссылку: {click_error}")
                                return False
                        
                        return True
                    else:
                        self.log("❌ Не удалось найти ссылку для перехода к карточке")
                        return False
                except Exception as e:
                    self.log(f"❌ Не удалось кликнуть на ссылку: {e}")
                    import traceback
                    self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
                    return False
                    
            else:
                self.log(f"⚠️ Найдено {len(selected_cards)} карточек в {priority_name}")
                # Передаем свежие карточки в метод выбора
                fresh_cards_for_selection = [info['card'] for info in selected_cards]
                return self._show_cards_for_selection(
                    fresh_cards_for_selection,
                    family_number,
                    mother_fio,
                    filtered=True
                )
                
        except Exception as e:
            self.log(f"❌ Ошибка анализа результатов поиска: {e}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _show_cards_for_selection(self, cards, family_number, mother_fio, filtered=False):
        """Показ карточек пользователю для выбора"""
        try:
            card_info_list = []
            
            # Получаем свежие карточки для отображения информации
            for i, card in enumerate(cards):
                try:
                    fio_element = card.find_element(By.CSS_SELECTOR, ".fio")
                    fio = fio_element.text if fio_element else f"Карточка {i+1}"
                    
                    address = ""
                    try:
                        details_table = card.find_element(By.CSS_SELECTOR, "table.tbl-details")
                        rows = details_table.find_elements(By.TAG_NAME, "tr")
                        
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2 and "Проживает:" in cells[0].text:
                                address = cells[1].text
                                break
                    except:
                        pass
                    
                    # Определяем приоритет района для отображения
                    address_lower = address.lower()
                    priority = ""
                    if "вышневолоцкий городской округ" in address_lower:
                        priority = " (Вышневолоцкий ГО)"
                    elif "вышневолоцкий" in address_lower:
                        priority = " (Вышневолоцкий)"
                    elif "вышний волочек" in address_lower:
                        priority = " (Вышний Волочек)"
                    
                    card_info_list.append({
                        'index': i,
                        'fio': fio,
                        'address': address[:100] + "..." if len(address) > 100 else address,
                        'priority': priority
                    })
                except:
                    card_info_list.append({
                        'index': i,
                        'fio': f"Карточка {i+1}",
                        'address': "Информация недоступна",
                        'priority': ""
                    })
            
            dialog_text = f"Семья {family_number}: {mother_fio}\n\n"
            
            if filtered:
                dialog_text += "Найдено несколько карточек в приоритетных районах (Вышневолоцкий городской округ -> Вышневолоцкий -> Вышний Волочек):\n\n"
            else:
                dialog_text += "Найдено несколько карточек. Выберите нужную:\n\n"
            
            for i, info in enumerate(card_info_list):
                dialog_text += f"{i+1}. {info['fio']}{info.get('priority', '')}\n"
                dialog_text += f"   Адрес: {info['address']}\n\n"
            
            dialog_text += "Введите номер карточки (1, 2, 3...):"
            
            choice_dialog = ctk.CTkInputDialog(
                text=dialog_text,
                title="Выбор карточки"
            )
            
            choice = choice_dialog.get_input()
            
            if not choice:
                self.log("❌ Пользователь не сделал выбор")
                return False
                
            try:
                choice_num = int(choice) - 1
                if 0 <= choice_num < len(cards):
                    # Вместо использования старой карточки, находим свежую по индексу
                    fresh_cards = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers")
                    if choice_num < len(fresh_cards):
                        selected_card = fresh_cards[choice_num]
                        # Ищем ссылку с атрибутом title='Переход в просмотр ПКУ'
                        links = selected_card.find_elements(By.CSS_SELECTOR, "a[title='Переход в просмотр ПКУ']")
                        if len(links) > 0:
                            link = links[0]
                            # Получаем ID ссылки для использования в случае stale element reference
                            link_id = link.get_attribute("id")
                            
                            if link_id:
                                # Используем ID для получения свежего элемента перед кликом
                                try:
                                    fresh_link = WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable((By.ID, link_id))
                                    )
                                    # Прокручиваем к элементу перед кликом
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", fresh_link)
                                    time.sleep(0.5)  # Небольшая задержка для завершения прокрутки
                                    
                                    # Используем JavaScript для клика, чтобы избежать stale element reference
                                    try:
                                        self.driver.execute_script("arguments[0].click();", fresh_link)
                                    except:
                                        # Если JavaScript клик не работает, используем обычный клик
                                        fresh_link.click()
                                except:
                                    # Если не удается найти элемент по ID, используем JavaScript напрямую
                                    link_script = f"document.querySelector('a[title=\"Переход в просмотр ПКУ\"][id=\"{link_id}\"]')"
                                    try:
                                        self.driver.execute_script(f"({link_script}).click();")
                                    except Exception as js_error:
                                        self.log(f"❌ Не удалось кликнуть через JavaScript по ID: {js_error}")
                                        # Попробуем универсальный селектор
                                        try:
                                            self.driver.execute_script("document.querySelector('a[title=\"Переход в просмотр ПКУ\"]').click();")
                                        except Exception as universal_error:
                                            self.log(f"❌ Не удалось кликнуть через универсальный селектор: {universal_error}")
                                            return False
                            else:
                                # Если у ссылки нет ID, используем общий селектор
                                try:
                                    # Прокручиваем к элементу перед кликом
                                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", link)
                                    time.sleep(0.5)  # Небольшая задержка для завершения прокрутки
                                    
                                    # Используем JavaScript для клика, чтобы избежать stale element reference
                                    try:
                                        self.driver.execute_script("arguments[0].click();", link)
                                    except:
                                        # Если JavaScript клик не работает, используем обычный клик
                                        link.click()
                                except Exception as click_error:
                                    self.log(f"❌ Не удалось кликнуть на ссылку: {click_error}")
                                    return False
                            
                            time.sleep(0.8)  # Уменьшено с 2 до 0.8 секунды
                            self.log(f"✅ Выбрана карточка {choice_num + 1}")
                            return True
                        else:
                            self.log(f"❌ Не удалось найти ссылку для карточки {choice_num + 1}")
                            return False
                    else:
                        self.log(f"❌ Карточка с индексом {choice_num} не найдена в свежем списке")
                        return False
                else:
                    self.log(f"❌ Некорректный номер карточки: {choice}")
                    return False
            except ValueError:
                self.log(f"❌ Некорректный ввод: {choice}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка при выборе карточки: {e}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _setup_driver(self):
        """Настройка драйвера"""
        try:
            self.log("🔧 Настройка драйвера...")
            
            # Импортируем chrome_driver_helper
            from chrome_driver_helper import setup_chrome_driver
            
            # Используем улучшенный метод настройки ChromeDriver
            self.driver = setup_chrome_driver()
            if self.driver is None:
                self.log("❌ Не удалось настроить ChromeDriver")
                messagebox.showerror("Ошибка", "Не удалось настроить ChromeDriver")
                return False
            
            self.wait = WebDriverWait(self.driver, 10)
            self.driver.maximize_window()
            
            if not self._login():
                return False
                
            self.log("✅ Драйвер настроен и выполнен вход")
            return True
            
        except ImportError:
            # Если не удается импортировать chrome_driver_helper, используем старую логику
            self.log("⚠️ chrome_driver_helper не найден, используем старую логику...")
            return self._setup_driver_legacy()
        except Exception as e:
            self.log(f"❌ Ошибка настройки драйвера: {e}")
            return False
    
    def _setup_driver_legacy(self):
        """Старая логика настройки драйвера (резервный вариант)"""
        try:
            self.log("🔧 Настройка драйвера (старый метод)...")
            
            browser = self._detect_browser()
            if not browser:
                self.log("❌ Не найден Chrome, Yandex или Chromium")
                messagebox.showerror("Ошибка", "Не найден браузер Chrome, Yandex или Chromium")
                return False
                
            try:
                driver_path = ChromeDriverManager(chrome_type=browser['type']).install()
            except Exception as e:
                self.log(f"❌ Не удалось установить драйвер: {e}")
                messagebox.showerror("Ошибка", f"Не удалось установить драйвер браузера: {e}")
                return False
                
            service = webdriver.chrome.service.Service(driver_path)
            
            options = webdriver.ChromeOptions()
            if platform.system().lower() in ["linux", "redos"]:
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
            
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--start-maximized')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            try:
                self.driver = webdriver.Chrome(service=service, options=options)
                self.wait = WebDriverWait(self.driver, 10)
                
                self.driver.maximize_window()
                
                if not self._login():
                    return False
                    
                self.log("✅ Драйвер настроен и выполнен вход")
                return True
                
            except Exception as e:
                self.log(f"❌ Не удалось запустить драйвер: {e}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка настройки драйвера: {e}")
            return False
    
    def _detect_browser(self):
        """Определение доступного браузера"""
        system = platform.system().lower()
        
        if system == "windows":
            try:
                import winreg
                browsers = [
                    (r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe', 'Chrome', ChromeType.GOOGLE),
                    (r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\browser.exe', 'Yandex', ChromeType.YANDEX),
                ]
                
                for path, name, btype in browsers:
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                            browser_path = winreg.QueryValue(key, None)
                            if os.path.exists(browser_path):
                                self.log(f"✅ Найден браузер: {name}")
                                return {'name': name, 'type': btype}
                    except Exception:
                        continue
                        
            except ImportError:
                self.log("⚠️ Модуль winreg недоступен, пробуем стандартный Chrome")
                return {'name': 'Chrome', 'type': ChromeType.GOOGLE}
                
        elif system in ["linux", "redos"]:
            for path in ['/usr/bin/chromium-browser', '/usr/bin/chromium', '/usr/bin/google-chrome']:
                if os.path.exists(path):
                    self.log(f"✅ Найден браузер: {os.path.basename(path)}")
                    return {'name': 'Chromium', 'type': ChromeType.CHROMIUM}
        
        self.log("⚠️ Браузер не найден, пробуем Chrome")
        return {'name': 'Chrome', 'type': ChromeType.GOOGLE}
    
    def _login(self):
        """Вход в систему"""
        try:
            self.log("🔐 Выполняем вход...")
            
            self.driver.get("http://localhost:8080/aspnetkp/Common/FindInfo.aspx")
            time.sleep(1)
            
            username_field = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "tbUserName"))
            )
            username_field.clear()
            username_field.send_keys("СРЦ_Вол")
            
            password_field = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "tbPassword"))
            )
            password_field.clear()
            password_field.send_keys("СРЦ_Вол1", Keys.ENTER)
            
            time.sleep(1)
            self.log("✅ Вход выполнен")
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка входа: {e}")
            messagebox.showerror("Ошибка входа", f"Не удалось выполнить вход: {e}")
            return False
    
    def _fast_search_mother(self, mother_fio):
        """Быстрый поиск по ФИО матери"""
        max_attempts = 3  # Увеличиваем число попыток
        for attempt in range(max_attempts):
            try:
                # Ждем, что поле поиска будет доступно и пустое
                search_field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "ctl00$cph$ctrlFastFind$tbFind"))
                )
                
                # Получаем атрибуты элемента перед возможной устаревшей ссылкой
                search_field_id = search_field.get_attribute("id")
                search_field_name = search_field.get_attribute("name")
                
                # Очищаем поле и вводим новое значение
                search_field.clear()
                time.sleep(0.2)  # Небольшая задержка для завершения очистки
                search_field.send_keys(mother_fio)
                search_field.send_keys(Keys.ENTER)
                
                # Ждем появления результатов поиска
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers"))
                )
                
                self.log(f"✅ Поиск выполнен успешно (попытка {attempt + 1})")
                return True
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"⚠️ Попытка {attempt + 1} поиска не удалась: {e}")
                    # Если возникла ошибка stale element reference, пробуем использовать JavaScript
                    if "stale element reference" in str(e).lower():
                        try:
                            # Используем JavaScript для ввода данных в поле поиска
                            js_script = f"""
                            var searchField = document.querySelector('[name="ctl00$cph$ctrlFastFind$tbFind"]');
                            if (searchField) {{
                                searchField.value = '{mother_fio}';
                                searchField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                searchField.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                                return true;
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                # Ждем появления результатов поиска
                                WebDriverWait(self.driver, 10).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_cph_dTabsContainer .pers"))
                                )
                                self.log(f"✅ Поиск выполнен успешно через JavaScript (попытка {attempt + 1})")
                                return True
                        except Exception as js_error:
                            self.log(f"⚠️ Не удалось выполнить поиск через JavaScript: {js_error}")
                    
                    # Дополнительно убедимся, что мы на странице поиска
                    try:
                        self.driver.refresh()
                        time.sleep(1)
                        # Повторно дожидаемся загрузки страницы
                        WebDriverWait(self.driver, 10).until(
                            lambda driver: driver.execute_script("return document.readyState") == "complete"
                        )
                    except:
                        pass
                    time.sleep(0.5)
                else:
                    self.log(f"❌ Ошибка поиска после {max_attempts} попыток: {e}")
                    return False
        return False
    
    def _check_additional_info_empty(self):
        """Проверка пустого поля дополнительной информации"""
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                if not self._click_element_with_retry(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL", max_attempts=2):
                    self.log(f"⚠️ Не удалось кликнуть вкладку дополнительной информации, попытка {attempt + 1}")
                    if attempt < max_attempts - 1:
                        # Возвращаемся на страницу поиска и снова ищем семью
                        self._return_to_search_page()
                        # Здесь потребуется повторный поиск семьи, что может быть сложно
                        # Поэтому просто продолжаем попытки клика
                        time.sleep(1)
                        continue
                    else:
                        return False
                        
                # Ждем появления элемента с информацией
                try:
                    info_element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, "ctl00_cph_lblAddInfo2"))
                    )
                    info_text = info_element.text.strip()
                except:
                    # Если элемент не найден, проверяем наличие других элементов
                    info_text = ""
                
                result = info_text == "Информация отсутствует" or not info_text
                self.log(f"📊 Проверка дополнительной информации: {'пусто' if result else 'есть данные'}")
                return result
                
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"⚠️ Попытка {attempt + 1} проверки поля не удалась: {e}")
                    time.sleep(0.5)
                else:
                    self.log(f"⚠️ Ошибка проверки поля: {e}")
                    return True
        return True
    
    def _warn_existing_data(self):
        """Предупреждение о существующих данных"""
        return messagebox.askyesno("Предупреждение", 
                                  "В разделе уже есть данные! Они будут УДАЛЕНЫ.\nПродолжить?")
                                  
    def _navigate_to_additional_info(self):
        """Навигация к форме дополнительной информации"""
        try:
            # Клик по вкладке "Доп. информация"
            self.log("🔄 Переход на вкладку дополнительной информации...")
            
            # Проверяем, что мы действительно на странице карточки перед переходом к доп. информации
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: "CardInfo.aspx" in driver.current_url or "ПКУ" in driver.title
                )
            except:
                self.log("⚠️ Мы не на странице карточки семьи")
                return False
            
            if not self._click_element_with_retry(By.ID, "ctl00_cph_rptAllTabs_ctl10_tdTabL"):
                self.log("❌ Не удалось кликнуть вкладку дополнительной информации")
                return False
            
            # Небольшая задержка для загрузки вкладки
            time.sleep(0.5)
            
            # Ожидаем появление кнопки редактирования с дополнительной проверкой
            try:
                edit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_cph_lbtnEditAddInfo"))
                )
                self.log("✅ Кнопка редактирования найдена")
            except:
                self.log("❌ Кнопка редактирования не найдена")
                return False
                
            if not self._click_element_with_retry(By.ID, "ctl00_cph_lbtnEditAddInfo"):
                self.log("❌ Не удалось кликнуть кнопку редактирования")
                return False
            
            # Небольшая задержка после клика по кнопке редактирования
            time.sleep(0.5)
            
            # Ожидаем появление кнопки добавления с дополнительной проверкой
            try:
                add_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "ctl00_cph_ctrlDopFields_lbtnAdd"))
                )
                self.log("✅ Кнопка добавления найдена")
            except:
                self.log("❌ Кнопка добавления не найдена")
                return False
                
            if not self._click_element_with_retry(By.ID, "ctl00_cph_ctrlDopFields_lbtnAdd"):
                self.log("❌ Не удалось кликнуть кнопку добавления")
                return False
            
            # Небольшая задержка после клика по кнопке добавления
            time.sleep(1)
            
            # Ждем загрузки формы с дополнительной проверкой
            try:
                form_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "ctl00$cph$tbAddInfo"))
                )
                self.log("✅ Форма дополнительной информации загружена")
            except:
                self.log("❌ Форма дополнительной информации не загружена")
                return False
                
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка навигации: {e}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _format_family_data(self, family_data):
        """Форматирование данных семьи с доходами"""
        try:
            lines = []
            
            # Мать
            mother_line = f"Мать: {family_data.get('mother_fio', '')} {family_data.get('mother_birth', '')}"
            lines.extend([mother_line, f"Работает: {family_data.get('mother_work', '')}"])
            
            # Отец
            if family_data.get('father_fio'):
                lines.extend([
                    f"Отец: {family_data['father_fio']} {family_data.get('father_birth', '')}",
                    f"Работает: {family_data.get('father_work', '')}"
                ])
            
            # Дети
            if family_data.get('children'):
                lines.append("Дети:")
                for child in family_data['children']:
                    edu = f" - {child.get('education', '')}" if child.get('education') else ""
                    lines.append(f"    {child.get('fio', '')} {child.get('birth', '')}{edu}")
            
            # Доходы - ВКЛЮЧАЕМ ДОХОДЫ ИЗ JSON
            incomes = family_data.get('incomes', {})
            if incomes:
                lines.append("\nДоходы семьи:")
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
                    if key in income_labels and value:
                        try:
                            clean_value = ''.join(filter(str.isdigit, str(value)))
                            if clean_value:
                                float_value = float(clean_value)
                                formatted_value = f"{float_value:,.0f} руб.".replace(",", " ")
                            else:
                                formatted_value = value
                        except:
                            formatted_value = value
                        lines.append(f"{income_labels[key]}: {formatted_value}")
                
                try:
                    total_income = 0
                    for value in incomes.values():
                        clean_value = ''.join(filter(str.isdigit, str(value)))
                        if clean_value:
                            total_income += float(clean_value)
                    if total_income > 0:
                        lines.append(f"\nОбщий доход: {total_income:,.0f} руб.".replace(",", " "))
                except:
                    pass
            
            # Категория семьи
            category = "полная, многодетная" if family_data.get('father_fio') else "неполная, многодетная"
            
            add_info_text = "\n".join(lines)
            
            # Жилищные условия - ВКЛЮЧАЕМ СОБСТВЕННОСТЬ
            rooms = family_data.get('rooms', '')
            square = family_data.get('square', '')
            amenities = family_data.get('amenities', 'со всеми удобствами')
            ownership = family_data.get('ownership', '')
            
            housing_parts = []
            if rooms:
                housing_parts.append(f"{rooms} комнат")
            if square:
                housing_parts.append(f"{square} кв.м.")
            if amenities:
                housing_parts.append(f"{amenities}")
            if ownership:
                housing_parts.append(f"{ownership}")
            
            housing_info = ", ".join(housing_parts)
            
            adpi_data = {
                'has_adpi': 'д' if family_data.get('adpi') == 'да' else 'н',
                'install_date': family_data.get('install_date'),
                'check_date': family_data.get('check_date')
            }
            
            return add_info_text, category, housing_info, adpi_data
            
        except Exception as e:
            self.log(f"❌ Ошибка форматирования данных: {e}")
            return "", "", "", {'has_adpi': 'н', 'install_date': '', 'check_date': ''}
    
    def _fill_form(self, add_info_text, category, housing_info, adpi_data):
        """Заполнение формы с динамическим определением индексов"""
        try:
            # Определяем, есть ли АДПИ
            has_adpi = adpi_data['has_adpi'] == 'д'
            
            # Отмечаем чекбоксы
            checkbox_ids = [8, 12, 13, 14, 17, 18]
            if has_adpi:
                checkbox_ids.extend([15, 16])
            
            self.log(f"🔄 Отмечаем чекбоксы: {checkbox_ids}")
            
            # Проверяем каждый чекбокс перед установкой
            for checkbox_id in checkbox_ids:
                try:
                    checkbox_element_id = f"ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_{checkbox_id}"
                    checkbox = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, checkbox_element_id))
                    )
                    
                    # Прокручиваем к чекбоксу
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", checkbox)
                    time.sleep(0.2)
                    
                    # Проверяем, установлен ли чекбокс уже
                    is_selected = checkbox.is_selected()
                    if not is_selected:
                        # Попробуем кликнуть напрямую
                        try:
                            checkbox.click()
                            time.sleep(0.1)  # Небольшая задержка для обновления состояния
                        except:
                            # Если клик не удался, используем JavaScript
                            try:
                                self.driver.execute_script("arguments[0].click();", checkbox)
                            except:
                                self.log(f"⚠️ Не удалось отметить чекбокс {checkbox_id} через клик")
                                continue
                        
                        # Проверяем, что чекбокс действительно установлен
                        is_selected_after = checkbox.is_selected()
                        if is_selected_after:
                            self.log(f"✅ Чекбокс {checkbox_id} отмечен")
                        else:
                            self.log(f"⚠️ Не удалось отметить чекбокс {checkbox_id}")
                    else:
                        self.log(f"ℹ️ Чекбокс {checkbox_id} уже отмечен")
                except Exception as e:
                    self.log(f"⚠️ Не удалось отметить чекбокс {checkbox_id}: {e}")
                    
            # Альтернативный метод через JavaScript для уверенности
            js_script = """
            var ids = arguments[0];
            for (var i = 0; i < ids.length; i++) {
                var checkboxId = 'ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_divContent_AJ_' + ids[i];
                var checkbox = document.getElementById(checkboxId);
                if (checkbox && !checkbox.checked) {
                    checkbox.checked = true;
                    checkbox.dispatchEvent(new Event('click', { bubbles: true }));
                }
            }
            """
            
            try:
                self.driver.execute_script(js_script, checkbox_ids)
                self.log("✅ Чекбоксы дополнительно обработаны через JavaScript")
            except Exception as e:
                self.log(f"⚠️ Не удалось обработать чекбоксы через JavaScript: {e}")
            
            # Клик по кнопке подтверждения чекбоксов с улучшенной обработкой
            ok_button_id = "ctl00_cph_ctrlDopFields_AJSpr1_PopupDiv_ctl06_AJOk"
            if not self._click_element_with_retry(By.ID, ok_button_id):
                self.log("⚠️ Не удалось кликнуть кнопку подтверждения чекбоксов")
                # Попробуем альтернативный способ
                try:
                    ok_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, ok_button_id))
                    )
                    self.driver.execute_script("arguments[0].click();", ok_button)
                    self.log("✅ Кнопка подтверждения чекбоксов нажата через JavaScript")
                except:
                    self.log("❌ Не удалось нажать кнопку подтверждения чекбоксов")
                    return False
                
            # Заполняем основное текстовое поле
            if not self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True):
                self.log("⚠️ Не удалось заполнить текстовую область")
                self._fill_textarea("ctl00$cph$tbAddInfo", add_info_text, resize=True)
            
            # Заполняем АДПИ радио-кнопку
            self.log("🔄 Заполняем данные АДПИ...")
            if not self._fill_adpi_radio_button(adpi_data):
                self.log("⚠️ Не удалось заполнить АДПИ")
            
            # Динамически определяем индексы полей
            field_indices = self._get_field_indices()
            
            if not field_indices:
                self.log("❌ Не удалось определить индексы полей")
                return False
            
            # Заполняем поля по найденным индексам
            if 'phone' in field_indices:
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["phone"]}$tb',
                    self.phone or ''
                ):
                    self.log("⚠️ Не удалось заполнить телефон")
            else:
                self.log("⚠️ Поле телефона не найдено в таблице")
            
            if 'category' in field_indices:
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["category"]}$tb',
                    category
                ):
                    self.log("⚠️ Не удалось заполнить категорию семьи")
            else:
                self.log("⚠️ Поле категории семьи не найдено в таблице")
            
            if 'address' in field_indices:
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["address"]}$tb',
                    self.address
                ):
                    self.log("⚠️ Не удалось заполнить адрес")
            else:
                self.log("⚠️ Поле адреса не найдено в таблице")
            
            if 'housing' in field_indices:
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["housing"]}$tb',
                    housing_info
                ):
                    self.log("⚠️ Не удалось заполнить жилищные условия")
            else:
                self.log("⚠️ Поле жилищных условий не найдено в таблице")
            
            if 'living' in field_indices:
                living_conditions_text = "Санитарные условия удовлетворительные, для детей имеется отдельное спальное место, место для занятий и отдыха. Продукты питания в достаточном количестве."
                if not self._fill_field_with_retry(
                    'name',
                    f'ctl00$cph$ctrlDopFields$gv$ctl{field_indices["living"]}$tb',
                    living_conditions_text
                ):
                    self.log("⚠️ Не удалось заполнить бытовые условия")
            else:
                self.log("⚠️ Поле бытовых условий не найдено в таблице")
            
            # Заполняем даты АДПИ если есть
            if has_adpi:
                self._fill_adpi_dates_with_indices(adpi_data, field_indices)
                
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка заполнения формы: {e}")
            import traceback
            self.log(f"📋 Трассировка:\n{traceback.format_exc()}")
            return False
    
    def _get_field_indices(self):
        """Динамическое определение индексов полей по их названиям"""
        field_indices = {}
        
        try:
            # Ждем загрузки таблицы
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_cph_ctrlDopFields_gv"))
            )
            
            # Прокручиваем немного вниз, чтобы таблица была видна
            self.driver.execute_script("window.scrollBy(0, 300);")
            # Убрали задержку, так как используем ожидание элементов
            
            # Пробуем найти все строки с полями
            rows = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_cph_ctrlDopFields_gv tr:not(:first-child)")
            
            if not rows:
                self.log("⚠️ Не найдены строки в таблице, использую стандартные индексы")
                return self._get_fallback_indices()
            
            self.log(f"📊 Найдено строк в таблице: {len(rows)}")
            
            # Проходим по всем строкам и ищем нужные поля
            for i, row in enumerate(rows, start=2):  # начинаем с 2
                try:
                    # Формируем индекс для поиска элемента
                    index_str = f"{i:02d}"
                    
                    # Пробуем найти элемент с названием поля
                    try:
                        field_name_elem = row.find_element(By.ID, f"ctl00_cph_ctrlDopFields_gv_ctl{index_str}_lbName")
                        field_name = field_name_elem.text.strip()
                        
                        self.log(f"  Строка {index_str}: {field_name}")
                        
                        # Сопоставляем название поля с нашими ключами
                        if "Номер телефона" in field_name:
                            field_indices['phone'] = index_str
                        elif "Категория семьи" in field_name:
                            field_indices['category'] = index_str
                        elif "Фактический адрес проживания семьи" in field_name or "адрес" in field_name.lower():
                            field_indices['address'] = index_str
                        elif "Жилищные условия" in field_name or "жилищ" in field_name.lower():
                            field_indices['housing'] = index_str
                        elif "Бытовые условия" in field_name or "бытов" in field_name.lower():
                            field_indices['living'] = index_str
                        elif "Дата установки АДПИ" in field_name or "установки" in field_name.lower():
                            field_indices['install_date'] = index_str
                        elif "Дата последней проверки АДПИ" in field_name or "проверки" in field_name.lower():
                            field_indices['check_date'] = index_str
                        
                    except:
                        # Пробуем альтернативный способ поиска
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                field_name = cells[1].text.strip()
                                if field_name:
                                    self.log(f"  Строка {index_str}: {field_name}")
                                    
                                    if "Номер телефона" in field_name:
                                        field_indices['phone'] = index_str
                                    elif "Категория семьи" in field_name:
                                        field_indices['category'] = index_str
                                    elif "Фактический адрес проживания семьи" in field_name or "адрес" in field_name.lower():
                                        field_indices['address'] = index_str
                                    elif "Жилищные условия" in field_name or "жилищ" in field_name.lower():
                                        field_indices['housing'] = index_str
                                    elif "Бытовые условия" in field_name or "бытов" in field_name.lower():
                                        field_indices['living'] = index_str
                                    elif "Дата установки АДПИ" in field_name or "установки" in field_name.lower():
                                        field_indices['install_date'] = index_str
                                    elif "Дата последней проверки АДПИ" in field_name or "проверки" in field_name.lower():
                                        field_indices['check_date'] = index_str
                        except:
                            continue
                            
                except Exception as e:
                    self.log(f"    ⚠️ Ошибка анализа строки {i}: {e}")
                    continue
            
            self.log(f"✅ Определены индексы полей: {field_indices}")
            
            # Если не нашли все нужные поля, используем запасной вариант
            required_fields = ['phone', 'category', 'address', 'housing', 'living']
            missing_fields = [field for field in required_fields if field not in field_indices]
            
            if missing_fields:
                self.log(f"⚠️ Не найдены поля: {missing_fields}, использую стандартные индексы")
                fallback_indices = self._get_fallback_indices()
                # Объединяем найденные индексы со стандартными
                for field in missing_fields:
                    if field in fallback_indices:
                        field_indices[field] = fallback_indices[field]
            
            return field_indices
            
        except Exception as e:
            self.log(f"❌ Ошибка определения индексов полей: {e}")
            return self._get_fallback_indices()
    
    def _get_fallback_indices(self):
        """Запасной вариант определения индексов"""
        # Проверяем, есть ли АДПИ (ищем радио-кнопку "Да" для АДПИ)
        try:
            adpi_yes = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0"))
            )
            has_adpi = True
        except:
            has_adpi = False
        
        if has_adpi:
            return {
                'phone': '02',
                'category': '06',
                'address': '07',
                'housing': '08',
                'living': '09',
                'install_date': '04',
                'check_date': '05'
            }
        else:
            return {
                'phone': '02',
                'category': '04',
                'address': '05',
                'housing': '06',
                'living': '07'
            }
    
    def _fill_field_with_retry(self, by, selector, text, max_attempts=3):
        """Улучшенный метод заполнения поля с повторными попытками"""
        for attempt in range(max_attempts):
            try:
                self.log(f"🔄 Попытка {attempt + 1} заполнения поля {selector}")
                
                # Ждем и получаем элемент заново каждый раз
                field = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((by, selector))
                )
                
                # Прокручиваем к элементу
                self.driver.execute_script("arguments[0].scrollIntoView(true);", field)
                # Убрали задержку, т.к. используем ожидания
                
                # Получаем атрибуты элемента перед возможной устаревшей ссылкой
                field_id = field.get_attribute("id")
                field_name = field.get_attribute("name")
                
                # Очищаем поле
                field.clear()
                # Убрали задержку
                
                # Вводим текст
                if text:
                    field.send_keys(text)
                    # Убрали задержку
                    
                    # Проверяем, что текст введен
                    try:
                        value = field.get_attribute('value')
                        if value and value.strip():
                            self.log(f"✅ Заполнено поле: {selector}")
                            return True
                    except:
                        # Для textarea проверяем свойство value
                        try:
                            value = field.get_property('value')
                            if value and value.strip():
                                self.log(f"✅ Заполнено поле: {selector}")
                                return True
                        except:
                            # Если не удалось проверить, считаем успешным
                            self.log(f"✅ Заполнено поле: {selector} (не удалось проверить)")
                            return True
            
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"⚠️ Попытка {attempt + 1} заполнения поля {selector} не удалась: {e}")
                    # Если возникла ошибка stale element reference, пробуем использовать JavaScript
                    if "stale element reference" in str(e).lower():
                        try:
                            # Используем JavaScript для заполнения поля
                            if by == By.ID:
                                js_script = f"""
                                var element = document.getElementById('{selector}');
                                if (element) {{
                                    element.value = '{text}';
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    return true;
                                }}
                                return false;
                                """
                                result = self.driver.execute_script(js_script)
                                if result:
                                    self.log(f"✅ Заполнено поле через JavaScript: {selector}")
                                    return True
                            elif by == By.NAME:
                                js_script = f"""
                                var elements = document.getElementsByName('{selector}');
                                if (elements.length > 0) {{
                                    var element = elements[0];
                                    element.value = '{text}';
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    return true;
                                }}
                                return false;
                                """
                                result = self.driver.execute_script(js_script)
                                if result:
                                    self.log(f"✅ Заполнено поле через JavaScript: {selector}")
                                    return True
                            elif by == By.CSS_SELECTOR:
                                js_script = f"""
                                var element = document.querySelector('{selector}');
                                if (element) {{
                                    element.value = '{text}';
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    return true;
                                }}
                                return false;
                                """
                                result = self.driver.execute_script(js_script)
                                if result:
                                    self.log(f"✅ Заполнено поле через JavaScript: {selector}")
                                    return True
                        except Exception as js_error:
                            self.log(f"⚠️ Не удалось заполнить поле через JavaScript: {js_error}")
                    time.sleep(0.2)  # Уменьшили задержку с 0.5 до 0.2 секунды
                else:
                    self.log(f"❌ Не удалось заполнить поле {selector}: {e}")
                    # Если все попытки не удались, используем JavaScript как финальную попытку
                    try:
                        # Используем JavaScript для заполнения поля как последнюю меру
                        if by == By.ID:
                            js_script = f"""
                            var element = document.getElementById('{selector}');
                            if (element) {{
                                element.value = '{text}';
                                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return true;
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                self.log(f"✅ Заполнено поле через JavaScript как последняя мера: {selector}")
                                return True
                        elif by == By.NAME:
                            js_script = f"""
                            var elements = document.getElementsByName('{selector}');
                            if (elements.length > 0) {{
                                var element = elements[0];
                                element.value = '{text}';
                                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return true;
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                self.log(f"✅ Заполнено поле через JavaScript как последняя мера: {selector}")
                                return True
                        elif by == By.CSS_SELECTOR:
                            js_script = f"""
                            var element = document.querySelector('{selector}');
                            if (element) {{
                                element.value = '{text}';
                                element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return true;
                            }}
                            return false;
                            """
                            result = self.driver.execute_script(js_script)
                            if result:
                                self.log(f"✅ Заполнено поле через JavaScript как последняя мера: {selector}")
                                return True
                    except Exception as final_js_error:
                        self.log(f"⚠️ Не удалось заполнить поле через JavaScript как последнюю меру: {final_js_error}")
        
        return False
    
    def _fill_adpi_dates_with_indices(self, adpi_data, field_indices):
        """Заполнение дат АДПИ с использованием найденных индексов"""
        try:
            if adpi_data.get('install_date') and 'install_date' in field_indices:
                install_idx = field_indices['install_date']
                if not self._fill_date_field(f"igtxtctl00_cph_ctrlDopFields_gv_ctl{install_idx}_wdte", adpi_data['install_date']):
                    self.log("⚠️ Не удалось заполнить дату установки АДПИ")
                    return False
            
            if adpi_data.get('check_date') and 'check_date' in field_indices:
                check_idx = field_indices['check_date']
                if not self._fill_date_field(f"igtxtctl00_cph_ctrlDopFields_gv_ctl{check_idx}_wdte", adpi_data['check_date']):
                    self.log("⚠️ Не удалось заполнить дату проверки АДПИ")
                    return False
            
            self.log("✅ Даты АДПИ заполнены")
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка заполнения дат АДПИ: {e}")
            return False

    def _fill_date_field(self, field_id, date_text):
        """Заполнение поля даты"""
        try:
            # Ищем поле даты
            field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, field_id))
            )
            
            # Получаем атрибуты элемента перед возможной устаревшей ссылкой
            element_id = field.get_attribute("id")
            element_name = field.get_attribute("name")
            
            # Прокручиваем к элементу
            self.driver.execute_script("arguments[0].scrollIntoView(true);", field)
            # Убрали задержку, т.к. используем ожидания
            
            # Кликаем на поле
            field.click()
            # Убрали задержку
            
            # Очищаем поле
            field.send_keys(Keys.CONTROL + "a")
            field.send_keys(Keys.DELETE)
            # Убрали задержку
            
            # Вводим дату
            field.send_keys(date_text)
            # Убрали посимвольный ввод и задержки
            
            # Нажимаем Enter для подтверждения
            field.send_keys(Keys.ENTER)
            # Убрали задержку, т.к. следующее действие будет ждать элемент
            
            self.log(f"✅ Дата заполнена: {date_text}")
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка заполнения даты: {e}")
            # Если возникла ошибка stale element reference, пробуем использовать JavaScript
            if "stale element reference" in str(e).lower():
                try:
                    # Используем JavaScript для заполнения поля даты
                    js_script = f"""
                    var dateField = document.getElementById('{field_id}');
                    if (dateField) {{
                        dateField.value = '{date_text}';
                        dateField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        dateField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                    """
                    result = self.driver.execute_script(js_script)
                    if result:
                        self.log(f"✅ Дата заполнена через JavaScript: {date_text}")
                        return True
                except Exception as js_error:
                    self.log(f"⚠️ Не удалось заполнить дату через JavaScript: {js_error}")
                    # Попробуем альтернативный метод с использованием общего селектора
                    try:
                        js_script_alt = f"""
                        var dateField = document.querySelector('#{field_id}');
                        if (dateField) {{
                            dateField.value = '{date_text}';
                            dateField.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            dateField.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                        return false;
                        """
                        result_alt = self.driver.execute_script(js_script_alt)
                        if result_alt:
                            self.log(f"✅ Дата заполнена через альтернативный JavaScript: {date_text}")
                            return True
                    except Exception as alt_error:
                        self.log(f"⚠️ Не удалось заполнить дату через альтернативный JavaScript: {alt_error}")
            # Если все методы не сработали, возвращаем False
            return False
            
    def _final_verification(self, family_data):
        """Финальная проверка"""
        try:
            mother_fio = family_data.get('mother_fio', 'неизвестно')
            return messagebox.askyesno("Финальная проверка", 
                                      f"Семья: {mother_fio}\n\n"
                                      "Проверьте все введенные данные на странице.\n\n"
                                      "Продолжить сохранение?")
        except:
            return False
            
    def _save_and_exit(self):
        """Сохранение данных"""
        try:
            self.log("💾 Сохраняем данные...")
            
            save_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl00_cph_lbtnExitSave"))
            )
            save_button.click()
            
            # Убрали задержку, т.к. следующее действие будет ожидать элемент
            self.log("✅ Данные сохранены")
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка сохранения: {e}")
            return False
            
    def _take_screenshot(self, formatted_data, family_number, family_data):
        """Создание скриншота"""
        try:
            add_info_text, _, _, _ = formatted_data
            lines = add_info_text.split('\n')
            
            mother_name = ""
            for line in lines:
                if line.startswith('Мать: '):
                    mother_info = line[6:]
                    if '(' in mother_info:
                        mother_name = mother_info[:mother_info.index('(')].strip()
                    else:
                        mother_name = mother_info.strip()
                    break
            
            if not mother_name:
                mother_name = f"семья_{family_number}"
            
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', mother_name)
            safe_name = safe_name[:50]
            
            if not self.screenshot_dir:
                self.screenshot_dir = self.gui.screenshots_dir
                
            if not os.path.exists(self.screenshot_dir):
                try:
                    os.makedirs(self.screenshot_dir)
                except Exception as e:
                    self.log(f"⚠️ Не удалось создать папку для скриншотов: {e}")
                    return
            
            file_path = os.path.join(self.screenshot_dir, f"{family_number:03d}_{safe_name}.png")
            
            for attempt in range(3):
                try:
                    self.driver.save_screenshot(file_path)
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        self.log(f"📸 Скриншот сохранен: {file_path}")
                        return
                except Exception as e:
                    if attempt < 2:
                        time.sleep(0.5)
                    else:
                        self.log(f"⚠️ Ошибка скриншота: {e}")
            
        except Exception as e:
            self.log(f"⚠️ Ошибка создания скриншота: {e}")
            
    def _click_element_with_retry(self, by, selector, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                self.log(f"🔄 Попытка {attempt + 1} клика на элемент {selector}")
                
                # First, wait for element to be present
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                
                # Wait a bit for the element to be fully rendered
                time.sleep(0.2)
                
                # Check if element is clickable now
                element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                
                # Wait for any animations to complete
                time.sleep(0.3)
                
                # Get element attributes before potential stale reference
                element_id = element.get_attribute("id")
                element_name = element.get_attribute("name")
                
                # Try to click the element
                try:
                    element.click()
                    self.log(f"✅ Успешно кликнут элемент: {selector}")
                    return True
                except Exception as click_error:
                    # If direct click fails, try different approaches
                    try:
                        # Try clicking via JavaScript using fresh element reference
                        if element_id:
                            # Use the ID to get a fresh reference to the element
                            fresh_element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.ID, element_id))
                            )
                            self.driver.execute_script("arguments[0].click();", fresh_element)
                        elif element_name:
                            # Use the name to get a fresh reference to the element
                            fresh_element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.NAME, element_name))
                            )
                            self.driver.execute_script("arguments[0].click();", fresh_element)
                        else:
                            # Use the original selector to get a fresh reference
                            fresh_element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            self.driver.execute_script("arguments[0].click();", fresh_element)
                        self.log(f"✅ Успешно кликнут элемент через JavaScript: {selector}")
                        return True
                    except Exception as js_error:
                        # Try sending a click event with fresh element
                        try:
                            if element_id:
                                fresh_element = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.ID, element_id))
                                )
                                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", fresh_element)
                            elif element_name:
                                fresh_element = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.NAME, element_name))
                                )
                                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", fresh_element)
                            else:
                                fresh_element = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((by, selector))
                                )
                                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", fresh_element)
                            self.log(f"✅ Успешно кликнут элемент через MouseEvent: {selector}")
                            return True
                        except Exception as event_error:
                            self.log(f"⚠️ Все методы клика не удались: {click_error}, {event_error}")
                            # If all methods fail, try a more general approach
                            try:
                                # Execute JavaScript to click the element directly
                                script = f"document.querySelector('{selector.replace(By.ID, '#').replace(By.NAME, '[name]').replace(By.CLASS_NAME, '.')}').click();"
                                if by == By.ID:
                                    script = f"document.getElementById('{selector}').click();"
                                elif by == By.NAME:
                                    script = f"document.querySelector('[name=\"{selector}\"]').click();"
                                elif by == By.CLASS_NAME:
                                    script = f"document.querySelector('.{selector}').click();"
                                elif by == By.CSS_SELECTOR:
                                    script = f"document.querySelector('{selector}').click();"
                                elif by == By.XPATH:
                                    script = f"document.evaluate('{selector}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click();"
                                
                                self.driver.execute_script(script)
                                self.log(f"✅ Успешно кликнут элемент через общий JavaScript: {selector}")
                                return True
                            except Exception as general_error:
                                self.log(f"⚠️ Общий метод клика не сработал: {general_error}")
                                # Last resort: try to find the element again and use a more robust approach
                                try:
                                    # Find the element again using its attributes
                                    if element_id:
                                        self.driver.execute_script(f"document.getElementById('{element_id}').click();")
                                        self.log(f"✅ Успешно кликнут элемент через ID JavaScript: {element_id}")
                                        return True
                                    elif element_name:
                                        self.driver.execute_script(f"document.querySelector('[name=\"{element_name}\"]').click();")
                                        self.log(f"✅ Успешно кликнут элемент через Name JavaScript: {element_name}")
                                        return True
                                    else:
                                        continue
                                except Exception as last_resort_error:
                                    self.log(f"⚠️ Последняя попытка клика не удалась: {last_resort_error}")
                                    continue
            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"⚠️ Попытка {attempt + 1} клика на элемент {selector} не удалась: {str(e)}")
                    # If we encounter a stale element reference, wait a bit more before retrying
                    if "stale element reference" in str(e).lower():
                        time.sleep(1)  # Wait longer when dealing with stale element references
                    else:
                        time.sleep(0.5)  # Wait a bit longer between attempts
                else:
                    self.log(f"❌ Не удалось кликнуть элемент {selector} после {max_attempts} попыток: {str(e)}")
                    return False
        return False
        
    def _fill_textarea(self, field_name, text, resize=False):
        try:
            # First, wait for the element to be present
            field = self.wait.until(EC.presence_of_element_located((By.NAME, field_name)))
            
            # Wait a bit more for the element to be fully loaded
            time.sleep(0.3)
            
            # Now wait for it to be clickable
            field = self.wait.until(EC.element_to_be_clickable((By.NAME, field_name)))
            
            # Get field attributes before potential stale reference
            field_id = field.get_attribute("id")
            field_name_attr = field.get_attribute("name")
            
            # Scroll to the element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", field)
            time.sleep(0.3)
            
            # Clear the field using JavaScript to ensure it's completely cleared
            self.driver.execute_script("arguments[0].value = '';", field)
            
            # Click on the field to focus it
            field.click()
            
            # Fill the field using multiple methods to ensure success
            try:
                # Method 1: Direct send_keys
                field.send_keys(Keys.CONTROL + "a")  # Select all
                field.send_keys(Keys.DELETE)  # Delete selected
                field.send_keys(text)  # Send the new text
            except Exception as direct_error:
                # Method 2: Using JavaScript if direct method fails
                try:
                    # Use fresh reference to the element to avoid stale element reference
                    if field_id:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, field_id))
                        )
                        self.driver.execute_script("arguments[0].value = arguments[1];", fresh_field, text)
                    else:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.NAME, field_name_attr))
                        )
                        self.driver.execute_script("arguments[0].value = arguments[1];", fresh_field, text)
                    # Trigger input event so the page recognizes the change
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", fresh_field)
                except:
                    # If stale element reference occurs, use direct JavaScript method
                    result = self._fill_textarea_directly_by_name(field_name, text)
                    if result:
                        self.log(f"✅ Текстовая область заполнена через JavaScript")
                        if resize:
                            script = f"var el = document.getElementsByName('{field_name}')[0]; if(el) {{ el.style.height = '352px'; el.style.width = '1151px'; }}"
                            self.driver.execute_script(script)
                        return True
                    else:
                        raise direct_error  # Re-raise the original error
            
            # Verify the text was set correctly
            actual_value = field.get_attribute("value") or field.get_property("value")
            if actual_value != text:
                # If the value doesn't match, try JavaScript method
                try:
                    # Use fresh reference to the element to avoid stale element reference
                    if field_id:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, field_id))
                        )
                        self.driver.execute_script("arguments[0].value = arguments[1];", fresh_field, text)
                    else:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.NAME, field_name_attr))
                        )
                        self.driver.execute_script("arguments[0].value = arguments[1];", fresh_field, text)
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", fresh_field)
                except:
                    # If stale element reference occurs, use direct JavaScript method
                    result = self._fill_textarea_directly_by_name(field_name, text)
                    if not result:
                        self.log("⚠️ Не удалось заполнить текстовую область")
                        return False
            
            if resize:
                try:
                    # Use fresh reference to the element to avoid stale element reference
                    if field_id:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, field_id))
                        )
                        self.driver.execute_script("arguments[0].style.height = '352px'; arguments[0].style.width = '1151px';", fresh_field)
                    else:
                        fresh_field = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.NAME, field_name_attr))
                        )
                        self.driver.execute_script("arguments[0].style.height = '352px'; arguments[0].style.width = '1151px';", fresh_field)
                except:
                    # If stale element reference occurs, use direct JavaScript method for resize
                    resize_script = f"var el = document.getElementsByName('{field_name}')[0]; if(el) {{ el.style.height = '352px'; el.style.width = '1151px'; }}"
                    self.driver.execute_script(resize_script)
            
            self.log(f"✅ Текстовая область заполнена ({len(text)} символов)")
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка текстовой области: {e}")
            # Try the direct JavaScript method as a fallback
            try:
                result = self._fill_textarea_directly_by_name(field_name, text)
                if result:
                    self.log(f"✅ Текстовая область заполнена через JavaScript")
                    if resize:
                        script = f"var el = document.getElementsByName('{field_name}')[0]; if(el) {{ el.style.height = '352px'; el.style.width = '1151px'; }}"
                        self.driver.execute_script(script)
                    return True
            except Exception as js_error:
                self.log(f"⚠️ Ошибка при заполнении текстовой области через JavaScript: {js_error}")
                # Final fallback: use direct JavaScript with more robust error handling
                try:
                    # Use more robust JavaScript approach to fill the textarea
                    escaped_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
                    js_script = f"""
                    var elements = document.getElementsByName('{field_name}');
                    if (elements.length > 0) {{
                        var textarea = elements[0];
                        textarea.value = '{escaped_text}';
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                    """
                    result = self.driver.execute_script(js_script)
                    if result:
                        self.log(f"✅ Текстовая область заполнена через прямой JavaScript")
                        if resize:
                            resize_script = f"var el = document.getElementsByName('{field_name}')[0]; if(el) {{ el.style.height = '352px'; el.style.width = '1151px'; }}"
                            self.driver.execute_script(resize_script)
                        return True
                except Exception as final_error:
                    self.log(f"❌ Не удалось заполнить текстовую область даже через прямой JavaScript: {final_error}")
            return False
    
    def _fill_textarea_directly_by_name(self, field_name, text):
        """Прямое заполнение textarea по NAME через JavaScript"""
        try:
            # Escape backticks in the text to prevent breaking the JavaScript template literal
            escaped_text = text.replace('`', '\\`')
            script = f"""
            var elements = document.getElementsByName('{field_name}');
            if (elements.length > 0) {{
                var textarea = elements[0];
                textarea.value = `{escaped_text}`;
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                return true;
            }}
            return false;
            """
            result = self.driver.execute_script(script)
            return result
        except Exception as e:
            self.log(f"⚠️ Не удалось заполнить через JavaScript по NAME: {e}")
            return False
            
    def _fill_textarea_directly(self, element_id, text):
        """Прямое заполнение textarea по ID через JavaScript"""
        try:
            # Escape backticks in the text to prevent breaking the JavaScript template literal
            escaped_text = text.replace('`', '\\`')
            script = f"""
            var textarea = document.getElementById('{element_id}');
            if (textarea) {{
                textarea.value = `{escaped_text}`;
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                return true;
            }}
            return false;
            """
            result = self.driver.execute_script(script)
            if result:
                self.log(f"✅ Текстовая область заполнена через JavaScript")
                return True
        except Exception as e:
            self.log(f"⚠️ Не удалось заполнить через JavaScript: {e}")
        return False
            
    def _click_element(self, by, selector):
        try:
            element = self.wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            return True
        except Exception as e:
            self.log(f"⚠️ Ошибка клика: {e}")
            return False
            
    def _get_element_text(self, element_id, default=""):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, element_id))
            )
            return element.text
        except Exception as e:
            self.log(f"⚠️ Ошибка получения текста элемента {element_id}: {e}")
            return default
    
    def _fill_adpi_radio_button(self, adpi_data):
        try:
            # Determine which radio button to select
            if adpi_data['has_adpi'] == 'д':
                radio_button_id = "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_0"
                self.log("🔄 Устанавливаем 'Да' для АДПИ")
            else:
                radio_button_id = "ctl00_cph_ctrlDopFields_gv_ctl03_rbl_1"
                self.log("🔄 Устанавливаем 'Нет' для АДПИ")
            
            # Wait for the radio button to be present
            try:
                radio_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, radio_button_id))
                )
                
                # Get attributes before potential stale reference
                element_id = radio_button.get_attribute("id")
                element_name = radio_button.get_attribute("name")
                
                # Check if it's already selected
                is_selected = radio_button.is_selected()
                if is_selected:
                    self.log("ℹ️ Радио-кнопка АДПИ уже выбрана")
                    return True
                
                # Try clicking the radio button
                success = self._click_element_with_retry(By.ID, radio_button_id)
                if success:
                    self.log("✅ Радио-кнопка АДПИ успешно установлена")
                    return True
                else:
                    self.log("⚠️ Не удалось кликнуть радио-кнопку АДПИ через метод _click_element_with_retry")
                    
                    # Try alternative method using JavaScript with fresh reference
                    try:
                        # Use fresh reference to avoid stale element reference
                        fresh_radio_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.ID, element_id))
                        )
                        self.driver.execute_script("arguments[0].click();", fresh_radio_button)
                        self.log("✅ Радио-кнопка АДПИ установлена через JavaScript")
                        return True
                    except Exception as js_error:
                        self.log(f"⚠️ Не удалось установить радио-кнопку АДПИ через JavaScript: {js_error}")
                        
                        # Final attempt: click via dispatchEvent with fresh reference
                        try:
                            fresh_radio_button = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.ID, element_id))
                            )
                            self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", fresh_radio_button)
                            self.log("✅ Радио-кнопка АДПИ установлена через MouseEvent")
                            return True
                        except Exception as event_error:
                            self.log(f"❌ Не удалось установить радио-кнопку АДПИ через MouseEvent: {event_error}")
                            # Final fallback using direct JavaScript
                            try:
                                js_script = f"""
                                var radioBtn = document.getElementById('{element_id}');
                                if (radioBtn && !radioBtn.checked) {{
                                    radioBtn.checked = true;
                                    radioBtn.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    radioBtn.dispatchEvent(new Event('click', {{ bubbles: true }}));
                                    return true;
                                }}
                                return false;
                                """
                                result = self.driver.execute_script(js_script)
                                if result:
                                    self.log("✅ Радио-кнопка АДПИ установлена через прямой JavaScript")
                                    return True
                                else:
                                    self.log("❌ Не удалось установить радио-кнопку АДПИ через прямой JavaScript")
                                    return False
                            except Exception as final_error:
                                self.log(f"❌ Окончательная ошибка установки радио-кнопки АДПИ: {final_error}")
                                return False
            except Exception as wait_error:
                self.log(f"❌ Ошибка ожидания радио-кнопки АДПИ: {wait_error}")
                return False
                
        except Exception as e:
            self.log(f"⚠️ Ошибка заполнения АДПИ: {e}")
            return False