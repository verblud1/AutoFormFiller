"""Утилиты для валидации данных"""

from datetime import datetime


def validate_date(date_string):
    """Проверка корректности даты"""
    try:
        from utils.data_processing import clean_date
        date_string = clean_date(date_string)
        dt = datetime.strptime(date_string, '%d.%m.%Y')
        current_year = datetime.now().year
        if dt.year < 1900 or dt.year > current_year + 1:
            return False
        if dt.month < 1 or dt.month > 12:
            return False
        if dt.day < 1 or dt.day > 31:
            return False
        return True
    except ValueError:
        return False


def validate_number(value):
    """Проверка корректности числа"""
    try:
        if not value:
            return True
        from utils.data_processing import clean_numeric_field
        value = clean_numeric_field(value)
        float(value)
        return True
    except ValueError:
        return False


def validate_phone(phone):
    """Проверка корректности телефона"""
    if not phone:
        return True
    from utils.data_processing import clean_phone
    phone = clean_phone(phone)
    if len(phone) != 11:
        return False
    if not phone.startswith('7'):
        return False
    if not phone.isdigit():
        return False
    return True


def validate_family_data(family_data):
    """Проверка данных семьи"""
    errors = []
    
    mother_fio = family_data.get('mother_fio', '').strip()
    from utils.data_processing import clean_fio
    mother_fio = clean_fio(mother_fio)
    
    # Проверяем, что хотя бы одно из полей (мать или отец) заполнено
    father_fio = family_data.get('father_fio', '').strip()
    father_fio = clean_fio(father_fio)
    if not mother_fio and not father_fio:
        errors.append("Должно быть указано ФИО матери или отца")
    
    mother_birth = family_data.get('mother_birth', '').strip()
    from utils.data_processing import clean_date
    mother_birth = clean_date(mother_birth)
    if mother_birth:
        try:
            birth_dt = datetime.strptime(mother_birth, '%d.%m.%Y')
            if birth_dt.year > 2003:
                errors.append(f"Мать не может родиться после 2003 года (указан {birth_dt.year})")
            elif birth_dt.year > 2000:
                # Вместо показа диалога, просто добавляем предупреждение
                errors.append(f"Год рождения матери {birth_dt.year} > 2000 - это редко для родителя")
        except:
            errors.append("Неверный формат даты рождения матери")
    
    father_fio = family_data.get('father_fio', '').strip()
    father_fio = clean_fio(father_fio)
    father_birth = family_data.get('father_birth', '').strip()
    father_birth = clean_date(father_birth)
    if father_fio and father_birth:
        try:
            birth_dt = datetime.strptime(father_birth, '%d.%m.%Y')
            if birth_dt.year > 2003:
                errors.append(f"Отец не может родиться после 2003 года (указан {birth_dt.year})")
            elif birth_dt.year > 2000:
                # Вместо показа диалога, просто добавляем предупреждение
                errors.append(f"Год рождения отца {birth_dt.year} > 2000 - это редко для родителя")
        except:
            errors.append("Неверный формат даты рождения отца")
    
    children = family_data.get('children', [])
    for i, child in enumerate(children):
        child_fio = child.get('fio', '').strip()
        child_fio = clean_fio(child_fio)
        child_birth = child.get('birth', '').strip()
        child_birth = clean_date(child_birth)
        if child_fio and child_birth:
            try:
                birth_dt = datetime.strptime(child_birth, '%d.%m.%Y')
                # НОВОЕ: Ребенок не может родиться до 2000 года
                if birth_dt.year < 2000:
                    errors.append(f"Ребенок {i+1} не может родиться до 2000 года (указан {birth_dt.year})")
            except:
                errors.append(f"Неверный формат даты рождения ребенка {i+1}")
    
    rooms = family_data.get('rooms', '').strip()
    from utils.data_processing import clean_numeric_field
    rooms = clean_numeric_field(rooms)
    if rooms and not validate_number(rooms):
        errors.append("Количество комнат должно быть числом")
    
    square = family_data.get('square', '').strip()
    square = clean_numeric_field(square)
    if square and not validate_number(square):
        errors.append("Площадь должна быть числом")
    
    install_date = family_data.get('install_date', '').strip()
    install_date = clean_date(install_date)
    if install_date and not validate_date(install_date):
        errors.append("Неверный формат даты установки АДПИ")
    
    check_date = family_data.get('check_date', '').strip()
    check_date = clean_date(check_date)
    if check_date and not validate_date(check_date):
        errors.append("Неверный формат даты проверки АДПИ")
    
    incomes = family_data.get('incomes', {})
    for key, value in incomes.items():
        value_str = str(value).strip()
        value_str = clean_numeric_field(value_str)
        if value_str and not validate_number(value_str):
            errors.append(f"Доход '{key}' должен быть числом")
    
    unified_benefit = family_data.get('unified_benefit', '').strip()
    unified_benefit = clean_numeric_field(unified_benefit)
    if unified_benefit and not validate_number(unified_benefit):
        errors.append("Единое пособие должно быть числом")
    
    large_family_benefit = family_data.get('large_family_benefit', '').strip()
    large_family_benefit = clean_numeric_field(large_family_benefit)
    if large_family_benefit and not validate_number(large_family_benefit):
        errors.append("Пособие по многодетности должно быть числом")
    
    phone = family_data.get('phone_number', '').strip()
    phone = clean_phone(phone)
    if phone and not validate_phone(phone):
        errors.append("Неверный формат телефона. Должен быть в формате 7XXXXXXXXXX")
    
    return errors