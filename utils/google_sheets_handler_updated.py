#!/usr/bin/env python3
"""Модуль для работы с Google Sheets API для закрашивания выполненных семей"""

import json
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import openpyxl
from typing import List, Dict, Optional
import urllib.parse
import sys

try:
    try:
        try:
            from .config_manager import get_default_config_manager, ConfigManager
        except ImportError:
            # Если импорт не удался, возможно, скрипт запускается напрямую
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from config_manager import get_default_config_manager, ConfigManager
    except ImportError:
        # Если импорт не удался, возможно, скрипт запускается напрямую
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from config_manager import get_default_config_manager, ConfigManager
except ImportError:
    # Если импорт не удался, возможно, скрипт запускается напрямую
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config_manager import get_default_config_manager, ConfigManager


class GoogleSheetsHandler:
    def __init__(self, credentials_file: str):
        """
        Инициализация обработчика Google Sheets
        
        Args:
            credentials_file: Путь к файлу учетных данных JSON
        """
        self.credentials_file = credentials_file
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets']
        self.service = None
        self._authenticate()
        # Кэш для хранения информации о таблицах
        self._spreadsheet_cache = {}
    
    def _clear_cache(self):
        """Очистка кэша информации о таблицах"""
        self._spreadsheet_cache.clear()
    
    def _get_or_fetch_spreadsheet_info(self, spreadsheet_id: str):
        """
        Получение информации о таблице из кэша или запрос из API при необходимости
        
        Args:
            spreadsheet_id: ID электронной таблицы
            
        Returns:
            Информация о таблице
        """
        if spreadsheet_id not in self._spreadsheet_cache:
            spreadsheet_info = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            self._spreadsheet_cache[spreadsheet_id] = spreadsheet_info
        return self._spreadsheet_cache[spreadsheet_id]
    
    def _authenticate(self):
        """Аутентификация с помощью файла учетных данных"""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.scopes
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            print("✅ Успешно подключено к Google Sheets API")
        except Exception as e:
            print(f"❌ Ошибка аутентификации: {e}")
            raise
    
    def _normalize_sheet_name(self, sheet_name: str) -> str:
        """
        Нормализует имя листа для использования в Google Sheets API
        
        Args:
            sheet_name: Оригинальное имя листа
            
        Returns:
            Нормализованное имя листа
        """
        # Заменяем кавычки на апострофы и экранируем специальные символы
        # Google Sheets API требует заключать имена листов с пробелами и специальными символами в апострофы
        normalized = sheet_name.replace("'", "''")  # Экранируем одинарные кавычки
        return f"'{normalized}'"
    
    def find_families_in_sheet(self, spreadsheet_id: str, sheet_name: str, families: List[Dict]) -> List[Dict]:
        """
        Поиск семей в Google Sheets по ФИО
        
        Args:
            spreadsheet_id: ID электронной таблицы
            sheet_name: Название листа
            families: Список словарей с информацией о семьях
            
        Returns:
            Список найденных семей с координатами в таблице
        """
        try:
            # Получаем все значения из таблицы
            # Используем нормализованное имя листа для правильной обработки кириллицы
            normalized_sheet_name = self._normalize_sheet_name(sheet_name)
            # Получаем ID листа для дальнейшей обработки
            sheet_id = self._get_sheet_id_by_name(spreadsheet_id, sheet_name)
            if sheet_id is None:
                print(f"⚠️ Не удалось получить ID листа {sheet_name}")
                return []
            
            # Используем нормализованное имя листа для получения значений
            range_name = f"{normalized_sheet_name}!A:Z"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                print("⚠️ Таблица пуста")
                return []
            
            found_families = []
            
            # Ищем семьи по ФИО матери или отца
            for family in families:
                mother_fio = family.get('mother_fio', '').strip().lower()
                father_fio = family.get('father_fio', '').strip().lower()
                
                best_match = None
                best_score = 0
                
                # Проходим по каждой строке таблицы для поиска лучшего совпадения для текущей семьи
                for i, row in enumerate(values):
                    if not row:  # Пропускаем пустые строки
                        continue
                        
                    row_text = ' '.join(str(cell) for cell in row if cell).lower()
                    
                    # Проверяем соответствие для матери
                    if mother_fio:
                        score = self._calculate_match_score(row_text, mother_fio)
                        if score > best_score:
                            best_score = score
                            best_match = {
                                'family': family,
                                'row_index': i + 1,  # Индекс строки (начинается с 1)
                                'found_by': 'mother',
                                'coordinates': [i + 1, self._find_name_column_index(row, mother_fio)]
                            }
                    
                    # Проверяем соответствие для отца
                    if father_fio:
                        score = self._calculate_match_score(row_text, father_fio)
                        if score > best_score:
                            best_score = score
                            best_match = {
                                'family': family,
                                'row_index': i + 1,
                                'found_by': 'father',
                                'coordinates': [i + 1, self._find_name_column_index(row, father_fio)]
                            }
                
                # Если нашли хорошее совпадение (с порогом), добавляем в результат
                if best_match and best_score > 0.3:  # Порог для сопоставления
                    found_families.append(best_match)
        
            print(f"🔍 Найдено {len(found_families)} семей из {len(families)} запрошенных")
            return found_families
            
        except Exception as e:
            print(f"❌ Ошибка поиска семей в таблице: {e}")
            return []
    
    def _calculate_match_score(self, row_text: str, name: str) -> float:
        """
        Рассчитывает степень совпадения между текстом строки и именем
        
        Args:
            row_text: Текст строки таблицы
            name: Имя для сравнения
            
        Returns:
            Оценка совпадения от 0 до 1
        """
        if not name or not row_text:
            return 0.0
        
        name_parts = [part for part in name.split() if len(part) > 2]  # Убираем короткие слова
        if not name_parts:
            return 0.0
        
        matches = 0
        for part in name_parts:
            if part in row_text:
                matches += 1
        
        # Коэффициент совпадения: сколько частей имени найдено относительно общего количества
        score = matches / len(name_parts)
        
        # Повышаем оценку, если найдено больше половины частей имени
        if matches == len(name_parts):
            score *= 1.2  # Бонус за полное совпадение
        
        return min(score, 1.0)  # Не больше 1.0
    
    def _find_name_column_index(self, row: List[str], name: str) -> int:
        """Находит приблизительный индекс столбца, где находится имя"""
        name_parts = name.lower().split()
        
        # Сначала ищем полное совпадение
        for j, cell in enumerate(row):
            cell_lower = cell.lower()
            if name.lower() in cell_lower:
                # Проверяем, что это полноценное ФИО, а не просто совпадение по части слова
                if len(name_parts) > 1:  # Если в имени несколько частей (ФИО)
                    for part in name_parts:
                        if len(part) > 2 and part in cell_lower:  # Убедимся, что части имени действительно есть в ячейке
                            return j + 1
                else:
                    return j + 1
        
        # Если полное совпадение не найдено, ищем частичное совпадение по нескольким частям
        for j, cell in enumerate(row):
            cell_lower = cell.lower()
            matches = 0
            for part in name_parts:
                if len(part) > 2 and part in cell_lower:
                    matches += 1
            # Если нашли хотя бы 2 совпадения (например, фамилия и имя), считаем это правильным столбцом
            if matches >= 2:
                return j + 1
        
        # В крайнем случае, ищем хотя бы одно совпадение
        for j, cell in enumerate(row):
            cell_lower = cell.lower()
            for part in name_parts:
                if len(part) > 2 and part in cell_lower:
                    return j + 1
        
        return 1  # По умолчанию первый столбец
    
    def _get_sheet_id_by_name(self, spreadsheet_id: str, sheet_name: str) -> Optional[int]:
        """
        Получение ID листа по его имени
        
        Args:
            spreadsheet_id: ID электронной таблицы
            sheet_name: Название листа
            
        Returns:
            ID листа или None, если лист не найден
        """
        try:
            # Получаем информацию о таблице из кэша или запрашиваем, если нет в кэше
            if spreadsheet_id not in self._spreadsheet_cache:
                spreadsheet_info = self.service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id
                ).execute()
                self._spreadsheet_cache[spreadsheet_id] = spreadsheet_info
            else:
                spreadsheet_info = self._spreadsheet_cache[spreadsheet_id]
            
            # Сначала попробуем точное совпадение
            for sheet in spreadsheet_info.get('sheets', []):
                title = sheet.get('properties', {}).get('title', '')
                if title == sheet_name:
                    return sheet['properties']['sheetId']
            
            # Если точное совпадение не найдено, используем нормализованные строки
            for sheet in spreadsheet_info.get('sheets', []):
                title = sheet.get('properties', {}).get('title', '')
                if title.strip() == sheet_name.strip():
                    return sheet['properties']['sheetId']
            
            # Если всё ещё не найдено, попробуем частичное совпадение
            for sheet in spreadsheet_info.get('sheets', []):
                title = sheet.get('properties', {}).get('title', '')
                if sheet_name in title or title in sheet_name:
                    print(f"⚠️ Найдено частичное совпадение для '{sheet_name}': '{title}'")
                    return sheet['properties']['sheetId']
            
            print(f"⚠️ Лист с названием '{sheet_name}' не найден")
            # Выведем список всех доступных листов для отладки
            available_sheets = [sheet.get('properties', {}).get('title', '') for sheet in spreadsheet_info.get('sheets', [])]
            print(f"📋 Доступные листы: {available_sheets}")
            return None
        except Exception as e:
            print(f"❌ Ошибка получения ID листа: {e}")
            return None
     
    def _get_normalized_sheet_range(self, spreadsheet_id: str, sheet_name: str, range_suffix: str = "A:Z") -> Optional[str]:
        """
        Получает корректно сформированный диапазон для использования в API,
        обходя проблему с кириллическими символами
        
        Args:
            spreadsheet_id: ID электронной таблицы
            sheet_name: Название листа
            range_suffix: Суффикс диапазона (по умолчанию "A:Z")
            
        Returns:
            Корректно сформированный диапазон или None в случае ошибки
        """
        # Используем имя листа с апострофами для обозначения кириллических символов
        try:
            normalized_sheet_name = self._normalize_sheet_name(sheet_name)
            range_name = f"{normalized_sheet_name}!{range_suffix}"
            return range_name
        except Exception as e:
            print(f"❌ Ошибка нормализации имени листа: {e}")
            return None
      
    def _get_sheet_properties_by_name(self, spreadsheet_id: str, sheet_name: str) -> Optional[Dict]:
        """
        Получение свойств листа по его имени
        
        Args:
            spreadsheet_id: ID электронной таблицы
            sheet_name: Название листа
            
        Returns:
            Словарь с информацией о листе или None, если лист не найден
        """
        try:
            # Получаем информацию о таблице из кэша или запрашиваем, если нет в кэше
            if spreadsheet_id not in self._spreadsheet_cache:
                spreadsheet_info = self.service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id
                ).execute()
                self._spreadsheet_cache[spreadsheet_id] = spreadsheet_info
            else:
                spreadsheet_info = self._spreadsheet_cache[spreadsheet_id]
            
            # Сначала попробуем точное совпадение
            for sheet in spreadsheet_info.get('sheets', []):
                title = sheet.get('properties', {}).get('title', '')
                if title == sheet_name:
                    return sheet['properties']
            
            # Если точное совпадение не найдено, используем нормализованные строки
            for sheet in spreadsheet_info.get('sheets', []):
                title = sheet.get('properties', {}).get('title', '')
                if title.strip() == sheet_name.strip():
                    return sheet['properties']
            
            # Если всё ещё не найдено, попробуем частичное совпадение
            for sheet in spreadsheet_info.get('sheets', []):
                title = sheet.get('properties', {}).get('title', '')
                if sheet_name in title or title in sheet_name:
                    print(f"⚠️ Найдено частичное совпадение для '{sheet_name}': '{title}'")
                    return sheet['properties']
            
            print(f"⚠️ Лист с названием '{sheet_name}' не найден")
            # Выведем список всех доступных листов для отладки
            available_sheets = [sheet.get('properties', {}).get('title', '') for sheet in spreadsheet_info.get('sheets', [])]
            print(f"📋 Доступные листы: {available_sheets}")
            return None
        except Exception as e:
            print(f"❌ Ошибка получения свойств листа: {e}")
            return None
     
    def highlight_completed_families(self, spreadsheet_id: str, sheet_name: str, found_families: List[Dict],
                                   color_rgba: Dict = None) -> bool:
        """
        Закрашивает ячейки для выполненных семей зеленым цветом
        
        Args:
            spreadsheet_id: ID электронной таблицы
            sheet_name: Название листа
            found_families: Список найденных семей с координатами
            color_rgba: Цвет в формате RGBA (по умолчанию зеленый)
        
        Returns:
            Успешность операции
        """
        if color_rgba is None:
            # Зеленый цвет по умолчанию
            color_rgba = {
                'red': 0.0,
                'green': 1.0,
                'blue': 0.0,
                'alpha': 0.3  # Прозрачность
            }
        
        try:
            requests = []
            
            for family_info in found_families:
                row_idx = family_info['coordinates'][0]
                
                # Закрашиваем всю строку, связанную с семьей
                # Получаем количество столбцов в таблице для правильного диапазона
                # Используем максимальное количество столбцов для покрытия всей строки
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": self._get_sheet_id_by_name(spreadsheet_id, sheet_name),
                            "startRowIndex": row_idx - 1,
                            "endRowIndex": row_idx,
                            "startColumnIndex": 0,
                            "endColumnIndex": 26  # Закрашиваем всю строку (до 26 столбцов: A-Z)
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": color_rgba
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                })
            
            if requests:
                body = {
                    'requests': requests
                }
                
                response = self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=body
                ).execute()
                
                print(f"✅ Успешно закрашено {len(requests)} строк для выполненных семей")
                return True
            else:
                print("⚠️ Нет семей для закрашивания")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка закрашивания семей: {e}")
            return False
     
    def get_spreadsheet_info(self, spreadsheet_id: str) -> Dict:
        """Получение информации о таблице"""
        try:
            # Используем кэшированную информацию, если доступна
            spreadsheet = self._get_or_fetch_spreadsheet_info(spreadsheet_id)
            return spreadsheet
        except Exception as e:
            print(f"❌ Ошибка получения информации о таблице: {e}")
            return {}
    
    def get_cells_formatting(self, spreadsheet_id: str, sheet_name: str, range_suffix: str = "A:Z") -> Dict:
        """
        Получение форматирования ячеек (включая цвета) из Google Sheets
        
        Args:
            spreadsheet_id: ID электронной таблицы
            sheet_name: Название листа
            range_suffix: Суффикс диапазона (по умолчанию "A:Z")
            
        Returns:
            Словарь с информацией о форматировании ячеек
        """
        try:
            # Используем нормализованное имя листа
            normalized_sheet_name = self._normalize_sheet_name(sheet_name)
            range_name = f"{normalized_sheet_name}!{range_suffix}"
            
            # Запрашиваем информацию о форматировании ячеек
            result = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                ranges=[range_name],
                includeGridData=True
            ).execute()
            
            return result
        except Exception as e:
            print(f"❌ Ошибка получения форматирования ячеек: {e}")
            return {}
    
    def get_cell_background_color(self, spreadsheet_id: str, sheet_name: str, row: int, col: int) -> Dict:
        """
        Получение цвета фона конкретной ячейки
        
        Args:
            spreadsheet_id: ID электронной таблицы
            sheet_name: Название листа
            row: Номер строки (начиная с 1)
            col: Номер столбца (начиная с 1)
            
        Returns:
            Словарь с RGBA значениями цвета или None если цвет не установлен
        """
        try:
            # Получаем ID листа
            sheet_id = self._get_sheet_id_by_name(spreadsheet_id, sheet_name)
            if sheet_id is None:
                print(f"⚠️ Не удалось получить ID листа {sheet_name}")
                return None
            
            # Запрашиваем информацию о конкретной ячейке
            result = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                ranges=[f"{self._normalize_sheet_name(sheet_name)}!{chr(64+col)}{row}:{chr(64+col)}{row}"],
                includeGridData=True
            ).execute()
            
            # Извлекаем информацию о форматировании ячейки
            if 'sheets' in result:
                for sheet in result['sheets']:
                    if sheet.get('properties', {}).get('sheetId') == sheet_id:
                        if 'data' in sheet:
                            for grid_data in sheet['data']:
                                if 'rowData' in grid_data:
                                    row_data = grid_data['rowData']
                                    if row - 1 < len(row_data):
                                        row_content = row_data[row - 1]
                                        if 'values' in row_content:
                                            values = row_content['values']
                                            if col - 1 < len(values):
                                                cell_data = values[col - 1]
                                                if 'userEnteredFormat' in cell_data:
                                                    format_data = cell_data['userEnteredFormat']
                                                    if 'backgroundColor' in format_data:
                                                        return format_data['backgroundColor']
                                                if 'effectiveFormat' in cell_data:
                                                    format_data = cell_data['effectiveFormat']
                                                    if 'backgroundColor' in format_data:
                                                        return format_data['backgroundColor']
                                                # Если нет цвета фона, возвращаем None
                                                return None
            
            return None
        except Exception as e:
            print(f"❌ Ошибка получения цвета ячейки ({row}, {col}): {e}")
            return None
     
    def check_cell_has_specific_color(self, color_data: Dict, target_color: str = "green") -> bool:
        """
        Проверяет, соответствует ли цвет ячейки заданному цвету
        
        Args:
            color_data: Словарь с RGBA значениями цвета
            target_color: Цель для сравнения ('green', 'yellow', 'red', 'any')
            
        Returns:
            True если цвет соответствует, иначе False
        """
        if color_data is None:
            return False
        
        # Нормализуем значения RGBA
        red = color_data.get('red', 0)
        green = color_data.get('green', 0)
        blue = color_data.get('blue', 0)
        alpha = color_data.get('alpha', 1)
        
        # Проверяем различные цвета в зависимости от параметра
        if target_color == "green":
            # Зеленый: высокое значение green, низкие red и blue
            # Также проверяем, что это не белый цвет (где все компоненты близки к 1.0)
            return green > 0.5 and red < 0.6 and blue < 0.6 and not (red > 0.9 and green > 0.9 and blue > 0.9)
        elif target_color == "yellow":
            # Желтый: высокие red и green, низкое blue
            # Также проверяем, что это не белый цвет
            return red > 0.7 and green > 0.7 and blue < 0.5 and not (red > 0.9 and green > 0.9 and blue > 0.9)
        elif target_color == "red":
            # Красный: высокое значение red, низкие green и blue
            return red > 0.7 and green < 0.5 and blue < 0.5
        elif target_color == "any":
            # Любые отличные от стандартного белого цвета
            # Белый цвет обычно имеет значения близкие к 1.0 для всех компонентов
            return not (red > 0.95 and green > 0.95 and blue > 0.95)
        else:
            return False
 
    def highlight_family_in_sheet(self, spreadsheet_id: str, sheet_name: str, mother_fio: str, father_fio: str) -> bool:
        """
        Находит семью по ФИО родителей и закрашивает все строки, связанные с этой семьей, зеленым цветом
        
        Args:
            spreadsheet_id: ID электронной таблицы
            sheet_name: Название листа
            mother_fio: ФИО матери
            father_fio: ФИО отца
            
        Returns:
            Успешность операции
        """
        try:
            # Получаем все значения из таблицы
            # Используем нормализованное имя листа для правильной обработки кириллицы
            normalized_sheet_name = self._normalize_sheet_name(sheet_name)
            # Получаем ID листа для дальнейшей обработки
            sheet_id = self._get_sheet_id_by_name(spreadsheet_id, sheet_name)
            if sheet_id is None:
                print(f"⚠️ Не удалось получить ID листа {sheet_name}")
                return False
            
            # Используем нормализованное имя листа для получения значений
            range_name = f"{normalized_sheet_name}!A:Z"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                print("⚠️ Таблица пуста")
                return False
            
            # Ищем строки, содержащие ФИО матери или отца
            target_rows = []
            mother_parts = mother_fio.split() if mother_fio else []
            father_parts = father_fio.split() if father_fio else []
            
            # Создаем списки возможных комбинаций для поиска
            search_terms = []
            if mother_parts:
                # Добавляем полное ФИО матери и его части
                search_terms.extend([mother_fio.lower()] + [part.lower() for part in mother_parts])
            if father_parts:
                # Добавляем полное ФИО отца и его части
                search_terms.extend([father_fio.lower()] + [part.lower() for part in father_parts])
            
            for i, row in enumerate(values):
                # Объединяем все значения в строке для поиска
                row_text = ' '.join(str(cell) for cell in row if cell).lower()
                
                # Проверяем, содержит ли строка хотя бы одну часть ФИО
                # Требуем как минимум 2 совпадения для уверенности в нахождении правильной семьи
                matches = 0
                for term in search_terms:
                    if len(term) > 2 and term in row_text:  # Игнорируем короткие слова
                        matches += 1
                
                # Если нашли достаточно совпадений (как минимум 2), считаем, что нашли нужную семью
                if matches >= 2:
                    target_rows.append(i + 1)  # Индекс строки (начинается с 1)
                    
                    # Также добавляем соседние строки, которые могут принадлежать той же семье
                    # (обычно дети и другая информация о семье находятся в соседних строках)
                    # Проверяем строки выше и ниже текущей
                    for offset in [-1, 1]:  # Проверяем строку выше и ниже
                        neighbor_row_idx = i + offset
                        if 0 <= neighbor_row_idx < len(values):
                            neighbor_row = values[neighbor_row_idx]
                            neighbor_row_text = ' '.join(str(cell) for cell in neighbor_row if cell).lower()
                            
                            # Если соседняя строка также содержит какие-либо части ФИО, добавляем её
                            neighbor_matches = 0
                            for term in search_terms:
                                if len(term) > 2 and term in neighbor_row_text:
                                    neighbor_matches += 1
                            
                            if neighbor_matches >= 1 and (neighbor_row_idx + 1) not in target_rows:
                                target_rows.append(neighbor_row_idx + 1)
            
            if not target_rows:
                print(f"🔍 Семья не найдена: {mother_fio or father_fio}")
                return False
            
            # Закрашиваем все найденные строки зеленым цветом
            requests = []
            for row_idx in target_rows:
                # Закрашиваем всю строку (все столбцы от A до Z)
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": self._get_sheet_id_by_name(spreadsheet_id, sheet_name),
                            "startRowIndex": row_idx - 1,
                            "endRowIndex": row_idx,
                            "startColumnIndex": 0,
                            "endColumnIndex": 26  # Закрашиваем всю строку (до 26 столбцов: A-Z)
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    'red': 0.0,
                                    'green': 1.0,
                                    'blue': 0.0,
                                    'alpha': 0.3  # Прозрачность
                                }
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor"
                    }
                })
            
            if requests:
                body = {
                    'requests': requests
                }
                
                response = self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=body
                ).execute()
                
                print(f"✅ Успешно закрашено {len(requests)} строк для семьи: {mother_fio or father_fio}")
                return True
            else:
                print("⚠️ Нет строк для закрашивания")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка закрашивания семьи в таблице: {e}")
            return False

def load_completed_families_from_json(json_file_path: str) -> List[Dict]:
    """
    Загрузка выполненных семей из JSON файла

    Args:
        json_file_path: Путь к JSON файлу с выполненными семьями
        
    Returns:
        Список словарей с информацией о семьях
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            families = data
        elif isinstance(data, dict) and 'families' in data:
            families = data['families']
        else:
            families = [data] if isinstance(data, dict) else []
        
        # Фильтруем только семьи со статусом "успешно"
        successful_families = []
        for family in families:
            if family.get('status') == 'успешно':
                successful_families.append(family)
        
        print(f"✅ Загружено {len(families)} выполненных семей из {json_file_path}")
        print(f"✅ Из них со статусом 'успешно': {len(successful_families)}")
        return successful_families
    except Exception as e:
        print(f"❌ Ошибка загрузки выполненных семей из JSON: {e}")
        return []


def highlight_completed_families_in_google_sheets(credentials_file: str, spreadsheet_id: str,
                                                 json_file_path: str, sheet_name: str = "АСП_Многодетные") -> bool:
    """
    Закрашивает выполненные семьи в Google Sheets зеленым цветом

    Args:
        credentials_file: Путь к файлу учетных данных Google
        spreadsheet_id: ID электронной таблицы
        json_file_path: Путь к JSON файлу с выполненными семьями
        sheet_name: Название листа в таблице
        
    Returns:
        Успешность операции
    """
    try:
        # Инициализация обработчика
        handler = GoogleSheetsHandler(credentials_file)
        
        # Загрузка выполненных семей из JSON
        completed_families = load_completed_families_from_json(json_file_path)
        
        if not completed_families:
            print("⚠️ Нет выполненных семей для закрашивания")
            return False
        
        # Отфильтровываем семьи, которые уже были отмечены как окрашенные
        unpainted_families = []
        painted_families = []
        
        for family in completed_families:
            # Проверяем сначала новое поле isPainted, затем старое isColored для обратной совместимости
            if family.get('isPainted', family.get('isColored', False)):
                painted_families.append(family)
            else:
                unpainted_families.append(family)
        
        print(f"📊 Найдено {len(completed_families)} всего семей")
        print(f"📊 Уже закрашенных: {len(painted_families)}")
        print(f"📊 Осталось закрасить: {len(unpainted_families)}")
        
        if not unpainted_families:
            print("✅ Все семьи уже отмечены как закрашенные")
            return True
        
        # Поиск семей в таблице
        found_families = handler.find_families_in_sheet(
            spreadsheet_id,
            sheet_name,
            unpainted_families
        )
        
        if not found_families:
            print("⚠️ Ни одна из незакрашенных семей не найдена в таблице")
            return False
        
        # Закрашивание найденных семей
        success = handler.highlight_completed_families(spreadsheet_id, sheet_name, found_families)
        
        if success:
            print(f"✅ Успешно закрашено {len(found_families)} выполненных семей")
            
            # Обновляем статус закрашивания в JSON файле
            update_families_paint_status(json_file_path, found_families, True)
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка закрашивания выполненных семей: {e}")
        return False


def update_families_paint_status(json_file_path: str, found_families: List[Dict], is_painted: bool):
    """
    Обновляет статус закрашивания для семей в JSON файле
    
    Args:
        json_file_path: Путь к JSON файлу с семьями
        found_families: Список найденных семей с координатами
        is_painted: Статус закрашивания (True - закрашено, False - не закрашено)
    """
    try:
        # Загружаем текущие данные
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Определяем, является ли данные списком или одним объектом
        if isinstance(data, list):
            families = data
        elif isinstance(data, dict) and 'families' in data:
            families = data['families']
        else:
            families = [data] if isinstance(data, dict) else []
        
        # Обновляем статус для найденных семей
        updated_count = 0
        for found_family in found_families:
            family_to_update = found_family['family']
            mother_fio = family_to_update.get('mother_fio', '')
            father_fio = family_to_update.get('father_fio', '')
            
            # Ищем соответствующую семью в оригинальном списке
            for family in families:
                if (family.get('mother_fio', '') == mother_fio and
                    family.get('father_fio', '') == father_fio):
                    family['isPainted'] = is_painted
                    # Удаляем старое поле isColored для чистоты данных
                    if 'isColored' in family:
                        del family['isColored']
                    updated_count += 1
                    break
        
        # Сохраняем обновленные данные
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(families, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Обновлен статус закрашивания для {updated_count} семей")
        
    except Exception as e:
        print(f"❌ Ошибка обновления статуса закрашивания: {e}")


def check_existing_colors_and_highlight(credentials_file: str, spreadsheet_id: str,
                                       json_file_path: str, sheet_name: str = "АСП_Многодетные") -> bool:
    """
    Проверяет существующие цвета в таблице и закрашивает семьи в Google Sheets зеленым цветом
    
    Args:
        credentials_file: Путь к файлу учетных данных Google
        spreadsheet_id: ID электронной таблицы
        json_file_path: Путь к JSON файлу с выполненными семьями
        sheet_name: Название листа в таблице
        
    Returns:
        Успешность операции
    """
    try:
        # Инициализация обработчика
        handler = GoogleSheetsHandler(credentials_file)
        
        # Загрузка выполненных семей из JSON
        completed_families = load_completed_families_from_json(json_file_path)
        
        if not completed_families:
            print("⚠️ Нет выполненных семей для закрашивания")
            return False
        
        # Отфильтровываем семьи, которые уже были отмечены как закрашенные
        unpainted_families = []
        pre_painted_families = []
        
        for family in completed_families:
            # Проверяем сначала новое поле isPainted, затем старое isColored для обратной совместимости
            if family.get('isPainted', family.get('isColored', False)):
                pre_painted_families.append(family)
            else:
                unpainted_families.append(family)
        
        print(f"📊 Найдено {len(completed_families)} всего семей")
        print(f"📊 Уже помеченных как закрашенные: {len(pre_painted_families)}")
        print(f"📊 Осталось проверить и закрасить: {len(unpainted_families)}")
        
        # Поиск семей в таблице
        all_found_families = handler.find_families_in_sheet(
            spreadsheet_id,
            sheet_name,
            unpainted_families
        )
        
        if not all_found_families:
            print("⚠️ Ни одна из незакрашенных семей не найдена в таблице")
            # Обновляем статус всех ненайденных семей как закрашенных
            update_families_paint_status(json_file_path, [], True)
            return False
        
        # Проверяем цвета для найденных семей
        families_with_colors = []
        families_without_colors = []
        
        for found_family in all_found_families:
            row_idx = found_family['coordinates'][0]
            col_idx = found_family['coordinates'][1]
            
            # Получаем цвет ячейки
            color_data = handler.get_cell_background_color(
                spreadsheet_id,
                sheet_name,
                row_idx,
                col_idx
            )
            
            # Проверяем, есть ли зеленый или желтый цвет в ячейке
            has_green = handler.check_cell_has_specific_color(color_data, "green")
            has_yellow = handler.check_cell_has_specific_color(color_data, "yellow")
            
            if has_green or has_yellow:
                families_with_colors.append(found_family)
                # Обновляем статус в JSON как закрашенный
                update_single_family_paint_status(json_file_path, found_family['family'], True)
                print(f"🟡 Семья '{found_family['family'].get('mother_fio', '')}' уже имеет цвет в таблице")
            else:
                families_without_colors.append(found_family)
        
        print(f"📊 Найдено {len(families_with_colors)} семей уже с цветом")
        print(f"📊 Нужно закрасить {len(families_without_colors)} семей")
        
        if families_with_colors:
            family_names = [f['family'].get('mother_fio', f['family'].get('father_fio', 'Unknown')) for f in families_with_colors]
            print(f"📝 Семьи с уже установленными цветами: {', '.join(family_names)}")
        
        if not families_without_colors:
            print("✅ Все семьи уже имеют цвет в таблице")
            return True
        
        # Закрашивание только тех семей, которые не имеют цвета
        success = handler.highlight_completed_families(spreadsheet_id, sheet_name, families_without_colors)
        
        if success:
            print(f"✅ Успешно закрашено {len(families_without_colors)} семей")
            
            # Обновляем статус закрашивания в JSON файле для закрашенных семей
            update_families_paint_status(json_file_path, families_without_colors, True)
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка проверки существующих цветов и закрашивания: {e}")
        return False


def update_single_family_paint_status(json_file_path: str, family: Dict, is_painted: bool):
    """
    Обновляет статус закрашивания для одной семьи в JSON файле
    
    Args:
        json_file_path: Путь к JSON файлу с семьями
        family: Словарь с информацией о семье
        is_painted: Статус закрашивания (True - закрашено, False - не закрашено)
    """
    try:
        # Загружаем текущие данные
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Определяем, является ли данные списком или одним объектом
        if isinstance(data, list):
            families = data
        elif isinstance(data, dict) and 'families' in data:
            families = data['families']
        else:
            families = [data] if isinstance(data, dict) else []
        
        # Обновляем статус для указанной семьи
        updated = False
        for fam in families:
            if (fam.get('mother_fio', '') == family.get('mother_fio', '') and
                fam.get('father_fio', '') == family.get('father_fio', '')):
                fam['isPainted'] = is_painted
                # Удаляем старое поле isColored для чистоты данных
                if 'isColored' in fam:
                    del fam['isColored']
                updated = True
                break
        
        if updated:
            # Сохраняем обновленные данные
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(families, f, ensure_ascii=False, indent=2)
    
    except Exception as e:
        print(f"❌ Ошибка обновления статуса закрашивания для одной семьи: {e}")


def interactive_check_existing_colors_and_highlight(credentials_file: str, spreadsheet_id: str,
                                                   json_file_path: str, sheet_name: str = "АСП_Многодетные") -> bool:
    """
    Интерактивная проверка существующих цветов в таблице и закрашивание семей в Google Sheets зеленым цветом
    
    Args:
        credentials_file: Путь к файлу учетных данных Google
        spreadsheet_id: ID электронной таблицы
        json_file_path: Путь к JSON файлу с выполненными семьями
        sheet_name: Название листа в таблице
        
    Returns:
        Успешность операции
    """
    try:
        # Инициализация обработчика
        handler = GoogleSheetsHandler(credentials_file)
        
        # Загрузка выполненных семей из JSON
        completed_families = load_completed_families_from_json(json_file_path)
        
        if not completed_families:
            print("⚠️ Нет выполненных семей для закрашивания")
            return False
        
        # Отфильтровываем семьи, которые уже были отмечены как закрашенные
        unpainted_families = []
        pre_painted_families = []
        
        for family in completed_families:
            # Проверяем сначала новое поле isPainted, затем старое isColored для обратной совместимости
            if family.get('isPainted', family.get('isColored', False)):
                pre_painted_families.append(family)
            else:
                unpainted_families.append(family)
        
        print(f"📊 Найдено {len(completed_families)} всего семей")
        print(f"📊 Уже помеченных как закрашенные: {len(pre_painted_families)}")
        print(f"📊 Осталось проверить и закрасить: {len(unpainted_families)}")
        
        # Поиск семей в таблице
        all_found_families = handler.find_families_in_sheet(
            spreadsheet_id,
            sheet_name,
            unpainted_families
        )
        
        if not all_found_families:
            print("⚠️ Ни одна из незакрашенных семей не найдена в таблице")
            return False
        
        # Проверяем цвета для найденных семей
        families_with_colors = []
        families_without_colors = []
        
        for found_family in all_found_families:
            row_idx = found_family['coordinates'][0]
            col_idx = found_family['coordinates'][1]
            
            # Получаем цвет ячейки
            color_data = handler.get_cell_background_color(
                spreadsheet_id,
                sheet_name,
                row_idx,
                col_idx
            )
            
            # Проверяем, есть ли зеленый или желтый цвет в ячейке
            has_green = handler.check_cell_has_specific_color(color_data, "green")
            has_yellow = handler.check_cell_has_specific_color(color_data, "yellow")
            
            if has_green or has_yellow:
                families_with_colors.append(found_family)
            else:
                families_without_colors.append(found_family)
        
        print(f"📊 Найдено {len(families_with_colors)} семей уже с цветом")
        print(f"📊 Нужно закрасить {len(families_without_colors)} семей")
        
        if families_with_colors:
            family_names = [f['family'].get('mother_fio', f['family'].get('father_fio', 'Unknown')) for f in families_with_colors]
            print(f"📝 Семьи с уже установленными цветами: {', '.join(family_names)}")
            
            # Запрашиваем у пользователя действие
            print("\n❓ Проверьте вручную следующие семьи в реестре:", ', '.join(family_names))
            choice = input("Отметить принудительно? (да/нет/выбрать): ").strip().lower()
            
            if choice == 'да':
                # Отмечаем все эти семьи принудительно
                success = handler.highlight_completed_families(spreadsheet_id, sheet_name, families_with_colors)
                
                if success:
                    print(f"✅ Принудительно закрашено {len(families_with_colors)} семей")
                    # Обновляем статус закрашивания в JSON файле
                    update_families_paint_status(json_file_path, families_with_colors, True)
                    
                    # Также закрашиваем оставшиеся семьи
                    if families_without_colors:
                        additional_success = handler.highlight_completed_families(spreadsheet_id, sheet_name, families_without_colors)
                        if additional_success:
                            print(f"✅ Закрашено дополнительно {len(families_without_colors)} семей")
                            update_families_paint_status(json_file_path, families_without_colors, True)
                        return additional_success
                    return success
                    
            elif choice == 'нет':
                # Для семей с цветами устанавливаем isPainted = False, для остальных закрашиваем
                for found_family in families_with_colors:
                    update_single_family_paint_status(json_file_path, found_family['family'], False)
                
                # Закрашиваем только семьи без цвета
                if families_without_colors:
                    success = handler.highlight_completed_families(spreadsheet_id, sheet_name, families_without_colors)
                    
                    if success:
                        print(f"✅ Закрашено {len(families_without_colors)} семей")
                        update_families_paint_status(json_file_path, families_without_colors, True)
                    
                    return success
                else:
                    print("✅ Нет семей для закрашивания")
                    return True
                    
            elif choice == 'выбрать':
                # Предлагаем пользователю выбрать конкретные семьи
                print("\nВыберите семьи для принудительного закрашивания:")
                for i, family in enumerate(families_with_colors):
                    name = family['family'].get('mother_fio', family['family'].get('father_fio', 'Unknown'))
                    print(f"{i+1}. {name}")
                
                try:
                    selected_indices = input("Введите номера семей через запятую (например: 1,3,5): ")
                    selected_indices = [int(x.strip()) - 1 for x in selected_indices.split(',')]
                    
                    selected_families = []
                    unselected_families = []
                    
                    for i, family in enumerate(families_with_colors):
                        if i in selected_indices:
                            selected_families.append(family)
                        else:
                            unselected_families.append(family)
                    
                    # Устанавливаем статус для нeвыбранных семей
                    for family in unselected_families:
                        update_single_family_paint_status(json_file_path, family['family'], False)
                    
                    # Закрашиваем выбранные семьи
                    if selected_families:
                        success = handler.highlight_completed_families(spreadsheet_id, sheet_name, selected_families)
                        
                        if success:
                            print(f"✅ Закрашено {len(selected_families)} выбранных семей")
                            update_families_paint_status(json_file_path, selected_families, True)
                    
                    # Закрашиваем семьи без цвета
                    if families_without_colors:
                        additional_success = handler.highlight_completed_families(spreadsheet_id, sheet_name, families_without_colors)
                        if additional_success:
                            print(f"✅ Закрашено {len(families_without_colors)} семей без цвета")
                            update_families_paint_status(json_file_path, families_without_colors, True)
                        
                        # Возвращаем общий успех
                        return success if selected_families else additional_success
                    else:
                        return True
                        
                except ValueError:
                    print("❌ Неверный формат ввода")
                    return False
            else:
                print("❌ Неверный выбор")
                return False
        else:
            # Нет семей с цветом, просто закрашиваем те, что без цвета
            if families_without_colors:
                success = handler.highlight_completed_families(spreadsheet_id, sheet_name, families_without_colors)
                
                if success:
                    print(f"✅ Закрашено {len(families_without_colors)} семей")
                    update_families_paint_status(json_file_path, families_without_colors, True)
                
                return success
            else:
                print("✅ Нет семей для закрашивания")
                return True
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интерактивной проверки существующих цветов и закрашивания: {e}")
        return False


def get_sheet_name_with_auto_save(original_sheet_name: str = "АСП_Многодетные", config_manager: ConfigManager = None) -> str:
    """
    Получение названия листа с автоматическим сохранением при необходимости
    
    Args:
        original_sheet_name: Оригинальное название листа
        config_manager: Экземпляр менеджера конфигурации
        
    Returns:
        Название листа
    """
    if config_manager is None:
        config_manager = get_default_config_manager()
    
    # Попробовать получить название листа из конфигурации
    sheet_name = config_manager.get_sheet_name(original_sheet_name)
    
    if sheet_name != original_sheet_name:
        print(f"✅ Найдено сохраненное название листа для '{original_sheet_name}': {sheet_name}")
        return sheet_name
    else:
        # Запросить у пользователя название листа
        print(f"ℹ️ Название листа для '{original_sheet_name}' не найдено в конфигурации")
        new_sheet_name = input(f"Пожалуйста, введите название листа для '{original_sheet_name}' (или нажмите Enter для '{original_sheet_name}'): ").strip()
        
        # Если пользователь ничего не ввел, используем оригинальное название
        if not new_sheet_name:
            new_sheet_name = original_sheet_name
        
        # Сохранить название листа в конфигурации
        config_manager.set_sheet_name(original_sheet_name, new_sheet_name)
        print(f"✅ Название листа для '{original_sheet_name}' сохранено в конфигурации: {new_sheet_name}")
        
        return new_sheet_name


def get_spreadsheet_id_with_auto_save(sheet_name: str = "АСП_Многодетные", config_manager: ConfigManager = None) -> str:
    """
    Получение ID таблицы с автоматическим сохранением при необходимости
    
    Args:
        sheet_name: Название листа
        config_manager: Экземпляр менеджера конфигурации
        
    Returns:
        ID электронной таблицы
    """
    if config_manager is None:
        config_manager = get_default_config_manager()
    
    # Попробовать получить ID из конфигурации
    spreadsheet_id = config_manager.get_spreadsheet_id(sheet_name)
    
    if spreadsheet_id:
        print(f"✅ Найден сохраненный ID таблицы для '{sheet_name}': {spreadsheet_id}")
        return spreadsheet_id
    else:
        # Запросить у пользователя ID таблицы
        print(f"ℹ️ ID таблицы для '{sheet_name}' не найден в конфигурации")
        spreadsheet_id = input(f"Пожалуйста, введите ID таблицы для '{sheet_name}': ").strip()
        
        # Сохранить ID в конфигурации
        config_manager.set_spreadsheet_id(sheet_name, spreadsheet_id)
        print(f"✅ ID таблицы для '{sheet_name}' сохранен в конфигурации: {spreadsheet_id}")
        
        return spreadsheet_id


def get_both_ids_with_confirmation(original_sheet_name: str = "АСП_Многодетные", config_manager: ConfigManager = None) -> tuple:
    """
    Получение ID таблицы и названия листа с возможностью проверки и корректировки пользователем
    
    Args:
        original_sheet_name: Оригинальное название листа
        config_manager: Экземпляр менеджера конфигурации
        
    Returns:
        Кортеж (spreadsheet_id, actual_sheet_name)
    """
    if config_manager is None:
        config_manager = get_default_config_manager()
    
    # Получить сохраненные значения
    spreadsheet_id = config_manager.get_spreadsheet_id(original_sheet_name)
    saved_sheet_name = config_manager.get_sheet_name(original_sheet_name)
    
    # Если значения не найдены, получить их с помощью отдельных функций
    if not spreadsheet_id:
        spreadsheet_id = get_spreadsheet_id_with_auto_save(original_sheet_name, config_manager)
    
    if saved_sheet_name == original_sheet_name:
        saved_sheet_name = get_sheet_name_with_auto_save(original_sheet_name, config_manager)
    
    # Показать пользователю текущие значения и спросить, нужно ли их изменить
    print(f"\n📋 Текущие данные:")
    print(f"   ID таблицы: {spreadsheet_id}")
    print(f"   Название листа: {saved_sheet_name}")
    
    confirm = input("\nℹ️ Использовать эти данные? (y/n): ").strip().lower()
    
    if confirm in ['y', 'yes', 'да', 'д']:
        print("✅ Данные подтверждены пользователем")
        return spreadsheet_id, saved_sheet_name
    else:
        # Пользователь хочет изменить данные
        new_spreadsheet_id = input(f"Введите новый ID таблицы (текущий: {spreadsheet_id}): ").strip()
        if not new_spreadsheet_id:
            new_spreadsheet_id = spreadsheet_id  # Оставить текущее значение
        
        new_sheet_name = input(f"Введите новое название листа (текущий: {saved_sheet_name}): ").strip()
        if not new_sheet_name:
            new_sheet_name = saved_sheet_name  # Оставить текущее значение
        
        # Сохранить новые значения
        config_manager.set_spreadsheet_id(original_sheet_name, new_spreadsheet_id)
        config_manager.set_sheet_name(original_sheet_name, new_sheet_name)
        
        print(f"✅ Новые данные сохранены:")
        print(f"   ID таблицы: {new_spreadsheet_id}")
        print(f"   Название листа: {new_sheet_name}")
        
        return new_spreadsheet_id, new_sheet_name


def interactive_check_existing_colors_and_highlight_with_auto_config(credentials_file: str, json_file_path: str, sheet_name: str = "АСП_Многодетные") -> bool:
    """
    Интерактивная проверка существующих цветов в таблице и закрашивание семей в Google Sheets зеленым цветом
    с автоматическим использованием сохраненного ID таблицы и названия листа с подтверждением пользователя
    
    Args:
        credentials_file: Путь к файлу учетных данных Google
        json_file_path: Путь к JSON файлу с выполненными семьями
        sheet_name: Название листа в таблице
        
    Returns:
        Успешность операции
    """
    try:
        # Использовать менеджер конфигурации для получения ID таблицы и названия листа с подтверждением
        config_manager = get_default_config_manager()
        spreadsheet_id, actual_sheet_name = get_both_ids_with_confirmation(sheet_name, config_manager)
        
        # Инициализация обработчика
        handler = GoogleSheetsHandler(credentials_file)
        
        # Загрузка выполненных семей из JSON
        completed_families = load_completed_families_from_json(json_file_path)
        
        if not completed_families:
            print("⚠️ Нет выполненных семей для закрашивания")
            return False
        
        # Отфильтровываем семьи, которые уже были отмечены как закрашенные
        unpainted_families = []
        pre_painted_families = []
        
        for family in completed_families:
            # Проверяем сначала новое поле isPainted, затем старое isColored для обратной совместимости
            if family.get('isPainted', family.get('isColored', False)):
                pre_painted_families.append(family)
            else:
                unpainted_families.append(family)
        
        print(f"📊 Найдено {len(completed_families)} всего семей")
        print(f"📊 Уже помеченных как закрашенные: {len(pre_painted_families)}")
        print(f"📊 Осталось проверить и закрасить: {len(unpainted_families)}")
        
        # Поиск семей в таблице
        all_found_families = handler.find_families_in_sheet(
            spreadsheet_id,
            actual_sheet_name,  # Используем подтвержденное название листа
            unpainted_families
        )
        
        if not all_found_families:
            print("⚠️ Ни одна из незакрашенных семей не найдена в таблице")
            return False
        
        # Проверяем цвета для найденных семей
        families_with_colors = []
        families_without_colors = []
        
        for found_family in all_found_families:
            row_idx = found_family['coordinates'][0]
            col_idx = found_family['coordinates'][1]
            
            # Получаем цвет ячейки
            color_data = handler.get_cell_background_color(
                spreadsheet_id,
                actual_sheet_name,  # Используем подтвержденное название листа
                row_idx,
                col_idx
            )
            
            # Проверяем, есть ли зеленый или желтый цвет в ячейке
            has_green = handler.check_cell_has_specific_color(color_data, "green")
            has_yellow = handler.check_cell_has_specific_color(color_data, "yellow")
            
            if has_green or has_yellow:
                families_with_colors.append(found_family)
            else:
                families_without_colors.append(found_family)
        
        print(f"📊 Найдено {len(families_with_colors)} семей уже с цветом")
        print(f"📊 Нужно закрасить {len(families_without_colors)} семей")
        
        if families_with_colors:
            family_names = [f['family'].get('mother_fio', f['family'].get('father_fio', 'Unknown')) for f in families_with_colors]
            print(f"📝 Семьи с уже установленными цветами: {', '.join(family_names)}")
            
            # Запрашиваем у пользователя действие
            print("\n❓ Проверьте вручную следующие семьи в реестре:", ', '.join(family_names))
            choice = input("Отметить принудительно? (да/нет/выбрать): ").strip().lower()
            
            if choice == 'да':
                # Отмечаем все эти семьи принудительно
                success = handler.highlight_completed_families(spreadsheet_id, actual_sheet_name, families_with_colors)
                
                if success:
                    print(f"✅ Принудительно закрашено {len(families_with_colors)} семей")
                    # Обновляем статус закрашивания в JSON файле
                    update_families_paint_status(json_file_path, families_with_colors, True)
                    
                    # Также закрашиваем оставшиеся семьи
                    if families_without_colors:
                        additional_success = handler.highlight_completed_families(spreadsheet_id, actual_sheet_name, families_without_colors)
                        if additional_success:
                            print(f"✅ Закрашено дополнительно {len(families_without_colors)} семей")
                            update_families_paint_status(json_file_path, families_without_colors, True)
                        return additional_success
                    return success
                    
            elif choice == 'нет':
                # Для семей с цветами устанавливаем isPainted = False, для остальных закрашиваем
                for found_family in families_with_colors:
                    update_single_family_paint_status(json_file_path, found_family['family'], False)
                
                # Закрашиваем только семьи без цвета
                if families_without_colors:
                    success = handler.highlight_completed_families(spreadsheet_id, actual_sheet_name, families_without_colors)
                    
                    if success:
                        print(f"✅ Закрашено {len(families_without_colors)} семей")
                        update_families_paint_status(json_file_path, families_without_colors, True)
                    
                    return success
                else:
                    print("✅ Нет семей для закрашивания")
                    return True
                    
            elif choice == 'выбрать':
                # Предлагаем пользователю выбрать конкретные семьи
                print("\nВыберите семьи для принудительного закрашивания:")
                for i, family in enumerate(families_with_colors):
                    name = family['family'].get('mother_fio', family['family'].get('father_fio', 'Unknown'))
                    print(f"{i+1}. {name}")
                
                try:
                    selected_indices = input("Введите номера семей через запятую (например: 1,3,5): ")
                    selected_indices = [int(x.strip()) - 1 for x in selected_indices.split(',')]
                    
                    selected_families = []
                    unselected_families = []
                    
                    for i, family in enumerate(families_with_colors):
                        if i in selected_indices:
                            selected_families.append(family)
                        else:
                            unselected_families.append(family)
                    
                    # Устанавливаем статус для нeвыбранных семей
                    for family in unselected_families:
                        update_single_family_paint_status(json_file_path, family['family'], False)
                    
                    # Закрашиваем выбранные семьи
                    if selected_families:
                        success = handler.highlight_completed_families(spreadsheet_id, actual_sheet_name, selected_families)
                        
                        if success:
                            print(f"✅ Закрашено {len(selected_families)} выбранных семей")
                            update_families_paint_status(json_file_path, selected_families, True)
                    
                    # Закрашиваем семьи без цвета
                    if families_without_colors:
                        additional_success = handler.highlight_completed_families(spreadsheet_id, actual_sheet_name, families_without_colors)
                        if additional_success:
                            print(f"✅ Закрашено {len(families_without_colors)} семей без цвета")
                            update_families_paint_status(json_file_path, families_without_colors, True)
                        
                        # Возвращаем общий успех
                        return success if selected_families else additional_success
                    else:
                        return True
                        
                except ValueError:
                    print("❌ Неверный формат ввода")
                    return False
            else:
                print("❌ Неверный выбор")
                return False
        else:
            # Нет семей с цветом, просто закрашиваем те, что без цвета
            if families_without_colors:
                success = handler.highlight_completed_families(spreadsheet_id, actual_sheet_name, families_without_colors)
                
                if success:
                    print(f"✅ Закрашено {len(families_without_colors)} семей")
                    update_families_paint_status(json_file_path, families_without_colors, True)
                
                return success
            else:
                print("✅ Нет семей для закрашивания")
                return True
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интерактивной проверки существующих цветов и закрашивания: {e}")
        return False


if __name__ == "__main__":
    # Пример использования
    # credentials_file = "path/to/your/service-account-key.json"
    # spreadsheet_id = "your_spreadsheet_id"
    # json_file_path = "completed_families.json"
    #
    # success = highlight_completed_families_in_google_sheets(
    #     credentials_file=credentials_file,
    #     spreadsheet_id=spreadsheet_id,
    #     json_file_path=json_file_path
    # )
    #
    # if success:
    #     print("✅ Закрашивание выполненных семей завершено успешно")
    # else:
    #     print("❌ Ошибка при закрашивании выполненных семей")
    pass