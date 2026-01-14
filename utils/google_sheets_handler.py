#!/usr/bin/env python3
"""Модуль для работы с Google Sheets API для закрашивания выполненных семей"""

import json
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import openpyxl
from typing import List, Dict, Optional


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
            range_name = f"{sheet_name}!A:Z"  # Предполагаем, что данные находятся в пределах A-Z
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
            for i, row in enumerate(values):
                for family in families:
                    mother_fio = family.get('mother_fio', '').strip().lower()
                    father_fio = family.get('father_fio', '').strip().lower()
                    
                    # Проверяем, есть ли ФИО в строке
                    row_text = ' '.join(row).lower() if row else ""  # Объединяем все ячейки строки
                    
                    if mother_fio and mother_fio in row_text:
                        found_families.append({
                            'family': family,
                            'row_index': i + 1,  # Индекс строки (начинается с 1)
                            'found_by': 'mother',
                            'coordinates': [i + 1, self._find_name_column_index(row, mother_fio)]
                        })
                    elif father_fio and father_fio in row_text:
                        found_families.append({
                            'family': family,
                            'row_index': i + 1,
                            'found_by': 'father',
                            'coordinates': [i + 1, self._find_name_column_index(row, father_fio)]
                        })
        
            print(f"🔍 Найдено {len(found_families)} семей из {len(families)} запрошенных")
            return found_families
            
        except Exception as e:
            print(f"❌ Ошибка поиска семей в таблице: {e}")
            return []
    
    def _find_name_column_index(self, row: List[str], name: str) -> int:
        """Находит приблизительный индекс столбца, где находится имя"""
        for j, cell in enumerate(row):
            if name in cell.lower():
                return j + 1  # Индекс столбца (начинается с 1)
        return 1  # По умолчанию первый столбец
    
    def highlight_completed_families(self, spreadsheet_id: str, found_families: List[Dict], 
                                   color_rgba: Dict = None) -> bool:
        """
        Закрашивает ячейки для выполненных семей зеленым цветом
        
        Args:
            spreadsheet_id: ID электронной таблицы
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
                # Предполагаем, что нужно закрасить несколько столбцов (например, A-E)
                end_column = 'E'  # Можно изменить в зависимости от структуры таблицы
                
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": 0,  # По умолчанию первый лист
                            "startRowIndex": row_idx - 1,
                            "endRowIndex": row_idx,
                            "startColumnIndex": 0,
                            "endColumnIndex": 5  # A до E (5 столбцов)
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
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            return spreadsheet
        except Exception as e:
            print(f"❌ Ошибка получения информации о таблице: {e}")
            return {}

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
            range_name = f"{sheet_name}!A:Z"
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
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": 0,  # ID листа (по умолчанию первый)
                            "startRowIndex": row_idx - 1,
                            "endRowIndex": row_idx,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(values[0]) if values and len(values[0]) > 0 else 26  # Количество столбцов в таблице
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
        
        print(f"✅ Загружено {len(families)} выполненных семей из {json_file_path}")
        return families
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
        
        # Поиск семей в таблице
        found_families = handler.find_families_in_sheet(
            spreadsheet_id, 
            sheet_name, 
            completed_families
        )
        
        if not found_families:
            print("⚠️ Ни одна из выполненных семей не найдена в таблице")
            return False
        
        # Закрашивание найденных семей
        success = handler.highlight_completed_families(spreadsheet_id, found_families)
        
        if success:
            print(f"✅ Успешно закрашено {len(found_families)} выполненных семей")
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка закрашивания выполненных семей: {e}")
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