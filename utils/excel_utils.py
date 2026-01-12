"""Утилиты для работы с Excel файлами"""

import re
import pandas as pd
import os
from datetime import datetime
from utils.data_processing import clean_string, clean_fio, clean_date, clean_phone, clean_address, parse_date


def load_register_file(file_path):
    """Загрузка реестра многодетных из xls/xlsx файла"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.xls':
            df = pd.read_excel(file_path, header=None, engine='xlrd')
        else:
            df = pd.read_excel(file_path, header=None)
        
        register_data = {}
        i = 1
        while i < len(df):
            try:
                row = df.iloc[i]
                if row.isnull().all():
                    i += 1
                    continue
                
                if not pd.isna(row[0]) and str(row[0]).strip() and re.match(r'^\d+$', str(row[0]).strip()):
                    phone_raw = str(row[10]) if len(row) > 10 and not pd.isna(row[10]) else ""
                    phone = clean_phone(phone_raw)
                    
                    main_person = {
                        'surname': clean_string(str(row[1]).strip()) if not pd.isna(row[1]) else "",
                        'name': clean_string(str(row[2]).strip()) if not pd.isna(row[2]) else "",
                        'patronymic': clean_string(str(row[3]).strip()) if not pd.isna(row[3]) else "",
                        'birth_date': parse_date(str(row[4])) if not pd.isna(row[4]) else "",
                        'phone': phone
                    }
                    
                    fio_parts = [main_person['surname'], main_person['name'], main_person['patronymic']]
                    fio_full = ' '.join([p for p in fio_parts if p])
                    if not fio_full:
                        i += 1
                        continue
                    
                    address_info = {
                        'region': clean_string(str(row[5]).strip()) if len(row) > 5 and not pd.isna(row[5]) else "",
                        'index': clean_string(str(row[6]).strip()) if len(row) > 6 and not pd.isna(row[6]) else "",
                        'city': clean_string(str(row[7]).strip()) if len(row) > 7 and not pd.isna(row[7]) else "",
                        'street': clean_string(str(row[8]).strip()) if len(row) > 8 and not pd.isna(row[8]) else "",
                        'house': clean_string(str(row[9]).strip()) if len(row) > 9 and not pd.isna(row[9]) else ""
                    }
                    
                    family_members = []
                    
                    if len(row) > 11 and not pd.isna(row[11]) and str(row[11]).strip():
                        family_members.append({
                            'surname': clean_string(str(row[11]).strip()),
                            'name': clean_string(str(row[12]).strip()) if len(row) > 12 and not pd.isna(row[12]) else "",
                            'patronymic': clean_string(str(row[13]).strip()) if len(row) > 13 and not pd.isna(row[13]) else "",
                            'birth_date': parse_date(str(row[14])) if len(row) > 14 and not pd.isna(row[14]) else "",
                            'fio_full': clean_fio(f"{str(row[11]).strip()} {str(row[12]).strip() if len(row) > 12 and not pd.isna(row[12]) else ''} {str(row[13]).strip() if len(row) > 13 and not pd.isna(row[13]) else ''}".strip())
                        })
                    
                    j = i + 1
                    while j < len(df):
                        next_row = df.iloc[j]
                        if (pd.isna(next_row[0]) or str(next_row[0]).strip() == "") and \
                        len(next_row) > 11 and not pd.isna(next_row[11]) and str(next_row[11]).strip():
                            family_members.append({
                                'surname': clean_string(str(next_row[11]).strip()),
                                'name': clean_string(str(next_row[12]).strip()) if len(next_row) > 12 and not pd.isna(next_row[12]) else "",
                                'patronymic': clean_string(str(next_row[13]).strip()) if len(next_row) > 13 and not pd.isna(next_row[13]) else "",
                                'birth_date': parse_date(str(next_row[14])) if len(next_row) > 14 and not pd.isna(row[14]) else "",
                                'fio_full': clean_fio(f"{str(next_row[11]).strip()} {str(next_row[12]).strip() if len(next_row) > 12 and not pd.isna(next_row[12]) else ''} {str(next_row[13]).strip() if len(next_row) > 13 and not pd.isna(next_row[13]) else ''}".strip())
                            })
                            j += 1
                        else:
                            break
                    
                    register_data[fio_full] = {
                        'main_person': main_person,
                        'family_members': family_members,
                        'address': address_info,
                        'row_index': i
                    }
                    
                    i = j
                else:
                    i += 1
            except Exception as e:
                print(f"Ошибка обработки строки {i}: {e}")
                import traceback
                traceback.print_exc()
                i += 1
                continue
        
        return register_data
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Ошибка загрузки реестра: {error_details}")
        return {}


def load_adpi_file(file_path):
    """Загрузка данных АДПИ из xlsx файла"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.ods':
            df = pd.read_excel(file_path, header=None, engine='odf')
        else:
            df = pd.read_excel(file_path, header=None)
        
        adpi_data = {}
        
        for index, row in df.iterrows():
            try:
                if row.isnull().all():
                    continue
                
                fio_cell = str(row[1]).strip() if len(row) > 1 and not pd.isna(row[1]) else ""
                if not fio_cell or fio_cell.lower() in ['nan', 'none', '']:
                    continue
                
                address_cell = str(row[3]).strip() if len(row) > 3 and not pd.isna(row[3]) else ""
                
                install_date_raw = ""
                if len(row) > 6:
                    install_cell = row[6]
                    if not pd.isna(install_cell):
                        install_date_raw = str(install_cell).strip()
                
                check_dates_raw = ""
                if len(row) > 7:
                    check_cell = row[7]
                    if not pd.isna(check_cell):
                        check_dates_raw = str(check_cell).strip()
                
                # Обработка двух дат (берем последнюю)
                install_date = parse_adpi_date(install_date_raw)
                check_date = parse_adpi_date(check_dates_raw)
                
                fio_normalized = clean_fio(fio_cell)
                address_cell = clean_address(address_cell)
                
                adpi_data[fio_normalized] = {
                    'address': address_cell,
                    'install_date': install_date,
                    'check_date': check_date
                }
            except Exception as e:
                print(f"Ошибка обработки строки {index}: {e}")
                continue
        
        return adpi_data
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Ошибка загрузки файла АДПИ: {error_details}")
        return {}


def parse_adpi_date(date_string):
    """Парсинг даты из АДПИ файла с обработкой двух дат"""
    if not date_string:
        return ""
    
    # Обработка случая с двумя датами (например: 28.01.2024.21.05.2025)
    if '.' in date_string:
        parts = date_string.split('.')
        if len(parts) >= 6:  # Есть две полные даты
            try:
                # Пробуем получить две даты
                date1_str = '.'.join(parts[:3])
                date2_str = '.'.join(parts[3:6])
                
                # Парсим даты
                date1 = parse_single_date(date1_str)
                date2 = parse_single_date(date2_str)
                
                # Если обе даты валидны, берем более позднюю
                if date1 and date2:
                    try:
                        dt1 = datetime.strptime(date1, '%d.%m.%Y')
                        dt2 = datetime.strptime(date2, '%d.%m.%Y')
                        return date1 if dt1 > dt2 else date2
                    except:
                        return date1  # Если не удалось сравнить, возвращаем первую
                elif date1:
                    return date1
                elif date2:
                    return date2
            except:
                pass
    
    # Обычная обработка одной даты
    return parse_single_date(date_string)


def parse_single_date(date_string):
    """Парсинг одной даты"""
    try:
        # Пробуем разные форматы
        formats = [
            '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y',
            '%Y.%m.%d', '%Y/%m/%d', '%Y-%m-%d',
            '%d.%m.%y', '%d/%m/%y', '%d-%m-%y',
            '%m/%d/%Y', '%m/%d/%y'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                if 1900 <= dt.year <= datetime.now().year:
                    return dt.strftime('%d.%m.%Y')
            except:
                continue
        
        # Пробуем с dateutil
        from dateutil import parser
        dt = parser.parse(date_string, dayfirst=True, yearfirst=False, fuzzy=True)
        if 1900 <= dt.year <= datetime.now().year:
            return dt.strftime('%d.%m.%Y')
    except:
        pass
    
    return clean_date(date_string)


def normalize_fio(fio):
    """Нормализация ФИО для сравнения"""
    fio = clean_fio(fio)
    return ' '.join(fio.lower().split())


def is_fio_similar(search_fio, target_fio):
    """Проверка похожести ФИО"""
    search_fio = clean_fio(search_fio)
    target_fio = clean_fio(target_fio)
    
    search_parts = normalize_fio(search_fio).split()
    target_parts = normalize_fio(target_fio).split()
    
    if not search_parts or not target_parts:
        return False
    
    if search_parts[0] != target_parts[0]:
        return False
    
    if len(search_parts) > 1:
        for part in search_parts[1:]:
            if part in target_parts:
                return True
        return False
    return True