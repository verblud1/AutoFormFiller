"""Утилиты для обработки данных семей"""

import re
import pandas as pd
from datetime import datetime
from dateutil import parser


def clean_string(text):
    """Очистка строки от специальных символов и нормализация пробелов"""
    if not isinstance(text, str):
        return text
    text = re.sub(r'[\t\n\r\x0b\x0c]+', ' ', text)
    text = ' '.join(text.split())
    text = re.sub(r'[;.]+$', '', text)
    text = re.sub(r'\.\.+', '.', text)
    text = re.sub(r',,+', ',', text)
    text = re.sub(r'\s+([.,;])', r'\1', text)
    text = re.sub(r',\s*,', ',', text)
    return text.strip()


def clean_fio(fio):
    """Очистка и нормализация ФИО"""
    if not isinstance(fio, str):
        return fio
    fio = clean_string(fio)
    parts = fio.split()
    if len(parts) == 3:
        parts = [part.capitalize() for part in parts]
        return ' '.join(parts)
    return fio


def clean_address(address):
    """Очистка и нормализация адреса"""
    if not isinstance(address, str):
        return address
    address = clean_string(address)
    address = re.sub(r'г\.\s*,', 'г. ', address)
    address = re.sub(r'ул\.\s*,', 'ул. ', address)
    address = re.sub(r'д\.\s*,', 'д. ', address)
    address = re.sub(r'кв\.\s*,', 'кв. ', address)
    address = re.sub(r'\.(\s*\.)+', '.', address)
    address = re.sub(r'д\.\s*д\.', 'д.', address)
    address = re.sub(r',\s*(\d+[а-я]*)', r', \1', address)
    return address


def clean_date(date_str):
    """Очистка и валидация даты"""
    if not isinstance(date_str, str):
        return date_str
    
    date_str = clean_string(date_str)
    
    # Обработка ошибки с датой в формате 28.12.202026 (оставляем первые 4 числа года)
    # Находим паттерн DD.MM.YYYY где YYYY содержит больше 4 цифр
    pattern = r'(\d{1,2}\.\d{1,2}\.)(\d{4})\d+'
    match = re.match(pattern, date_str)
    if match:
        day_month = match.group(1)
        year = match.group(2)
        corrected_date = day_month + year
        return corrected_date
    
    # Обработка формата MM/DD/YYYY или M/D/YYYY
    if '/' in date_str:
        parts = date_str.split('/')
        if len(parts) == 3:
            try:
                month, day, year = map(int, parts)
                # Проверяем валидность
                if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= datetime.now().year:
                    # Преобразуем в DD.MM.YYYY
                    return f"{day:02d}.{month:02d}.{year}"
            except:
                pass
    
    # Обработка формата DD.MM.YYYY
    if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', date_str):
        try:
            day, month, year = map(int, date_str.split('.'))
            if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= datetime.now().year:
                return f"{day:02d}.{month:02d}.{year}"
        except:
            pass
    
    # Обработка двух дат в одной строке (например: 28.01.2024.21.05.2025)
    if date_str.count('.') >= 5:
        parts = date_str.split('.')
        if len(parts) >= 6:
            try:
                # Пробуем получить две даты
                date1_str = f"{parts[0]}.{parts[1]}.{parts[2]}"
                date2_str = f"{parts[3]}.{parts[4]}.{parts[5]}"
                
                date1 = datetime.strptime(date1_str, '%d.%m.%Y')
                date2 = datetime.strptime(date2_str, '%d.%m.%Y')
                
                # Берем более позднюю дату
                if date1 > date2:
                    return date1_str
                else:
                    return date2_str
            except:
                pass
    
    # Убираем все лишние символы, кроме цифр и точек и слэшей
    date_str = re.sub(r'[^\d./]+', '', date_str)
    
    return date_str


def clean_phone(phone):
    """Очистка и форматирование телефона"""
    if not isinstance(phone, str):
        return phone
    digits = re.sub(r'\D', '', phone)
    if not digits:
        return ""
    if digits.startswith('9') and len(digits) == 10:
        return '7' + digits
    elif digits.startswith('8') and len(digits) == 11:
        return '7' + digits[1:]
    elif digits.startswith('7') and len(digits) == 11:
        return digits
    elif len(digits) == 10:
        return '7' + digits
    else:
        return digits


def clean_numeric_field(value):
    """Очистка числовых полей"""
    if not isinstance(value, str):
        return value
    cleaned = re.sub(r'[^\d.,]', '', value)
    cleaned = cleaned.replace(',', '.')
    parts = cleaned.split('.')
    if len(parts) > 1:
        cleaned = parts[0] + '.' + ''.join(parts[1:])
    return cleaned if cleaned else value


def clean_family_data(family_data):
    """Очистка всех данных семьи"""
    if not isinstance(family_data, dict):
        return family_data
    cleaned_data = {}
    for key, value in family_data.items():
        if isinstance(value, str):
            if 'fio' in key.lower():
                cleaned_data[key] = clean_fio(value)
            elif 'address' in key.lower():
                cleaned_data[key] = clean_address(value)
            elif 'birth' in key.lower():
                cleaned_data[key] = clean_date(value)
            elif 'phone' in key.lower() or 'tel' in key.lower():
                cleaned_data[key] = clean_phone(value)
            elif 'date' in key.lower():
                cleaned_data[key] = clean_date(value)
            elif any(x in key.lower() for x in ['salary', 'benefit', 'pension', 'alimony', 'rooms', 'square']):
                cleaned_data[key] = clean_numeric_field(value)
            elif 'education' in key.lower() or 'work' in key.lower() or 'amenities' in key.lower() or 'ownership' in key.lower():
                cleaned_data[key] = clean_string(value)
            else:
                cleaned_data[key] = clean_string(value)
        elif isinstance(value, list) and key == 'children':
            cleaned_children = []
            for child in value:
                if isinstance(child, dict):
                    cleaned_child = {}
                    for child_key, child_value in child.items():
                        if isinstance(child_value, str):
                            if 'fio' in child_key.lower():
                                cleaned_child[child_key] = clean_fio(child_value)
                            elif 'birth' in child_key.lower():
                                cleaned_child[child_key] = clean_date(child_value)
                            elif 'education' in child_key.lower():
                                cleaned_child[child_key] = clean_string(child_value)
                            else:
                                cleaned_child[child_key] = clean_string(child_value)
                        else:
                            cleaned_child[child_key] = child_value
                    cleaned_children.append(cleaned_child)
            cleaned_data[key] = cleaned_children
        else:
            cleaned_data[key] = value
    return cleaned_data


def parse_date(date_string):
    """Парсинг даты из различных форматов"""
    if not date_string or pd.isna(date_string) or str(date_string).lower() in ['nan', 'nat', 'none', '']:
        return ""
    try:
        date_string = str(date_string).strip()
        if isinstance(date_string, (datetime, pd.Timestamp)):
            return date_string.strftime('%d.%m.%Y')
        
        formats = [
            '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y',
            '%Y.%m.%d', '%Y/%m/%d', '%Y-%m-%d',
            '%d.%m.%y', '%d/%m/%y', '%d-%m-%y',
            '%m/%d/%Y', '%m/%d/%y'  # Добавлен формат MM/DD/YYYY
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                if 1900 <= dt.year <= datetime.now().year:
                    return dt.strftime('%d.%m.%Y')
            except:
                continue
        
        dt = parser.parse(date_string, dayfirst=True, yearfirst=False, fuzzy=True)
        if 1900 <= dt.year <= datetime.now().year:
            return dt.strftime('%d.%m.%Y')
    except:
        pass
    return clean_date(date_string)


def format_phone(phone_string):
    """Форматирование телефона в формат 7XXXXXXXXXX"""
    return clean_phone(phone_string)