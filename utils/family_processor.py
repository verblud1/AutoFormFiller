"""Класс для обработки данных семей"""

from utils.data_processing import clean_family_data, clean_fio, clean_date, clean_string
from utils.validation import validate_family_data
from utils.excel_utils import load_register_file, load_adpi_file, parse_adpi_date, parse_single_date, normalize_fio, is_fio_similar
from datetime import datetime
import json


class FamilyDataProcessor:
    """Класс для обработки данных семей"""

    def __init__(self):
        self.families = []
        self.current_family_index = 0
        self.current_file_path = None
        self.adpi_data = {}
        self.register_data = {}
        self.processed_families = set()

        # Константа для единого пособия
        self.BASE_UNIFIED_BENEFIT = 17000

    def collect_family_data(self, form_data):
        """Сбор данных из формы в словарь"""
        family_data = {}

        family_data['mother_fio'] = clean_fio(form_data.get('mother_fio', '').strip())
        family_data['mother_birth'] = clean_date(form_data.get('mother_birth', '').strip())
        family_data['mother_work'] = clean_string(form_data.get('mother_work', '').strip())

        family_data['mother_disability_care'] = form_data.get('mother_disability_care', False)

        # Сохраняем информацию о том, что мать не работает
        family_data['mother_not_working'] = form_data.get('mother_not_working', False)

        father_fio = clean_fio(form_data.get('father_fio', '').strip())
        if father_fio:
            family_data['father_fio'] = father_fio
            family_data['father_birth'] = clean_date(form_data.get('father_birth', '').strip())
            family_data['father_work'] = clean_string(form_data.get('father_work', '').strip())

            # Сохраняем информацию о том, что отец не работает
            family_data['father_not_working'] = form_data.get('father_not_working', False)

        children = []
        for child in form_data.get('children', []):
            child_fio = clean_fio(child.get('fio', '').strip())
            if child_fio:
                child_data = {
                    'fio': child_fio,
                    'birth': clean_date(child.get('birth', '').strip()),
                    'education': clean_string(child.get('education', '').strip())
                }
                # Добавляем информацию о домашнем ребенке, если чекбокс установлен
                if child.get('home_education', False):
                    child_data['home_education'] = True
                children.append(child_data)
        if children:
            family_data['children'] = children

        phone = clean_string(form_data.get('phone_number', '').strip())
        if phone:
            family_data['phone_number'] = phone

        address = clean_address(form_data.get('address', '').strip())
        if address:
            family_data['address'] = address

        rooms = clean_string(form_data.get('rooms', '').strip())
        if rooms:
            family_data['rooms'] = rooms

        square = clean_string(form_data.get('square', '').strip())
        if square:
            family_data['square'] = square

        family_data['amenities'] = form_data.get('amenities', 'со всеми удобствами')

        ownership = clean_string(form_data.get('ownership', '').strip())
        if ownership:
            family_data['ownership'] = ownership

        # Обработка долевой собственности
        ownership_text = form_data.get('ownership', '').strip()
        if form_data.get('shared_ownership', False):
            # Если отмечен чекбокс "Долевая собственность", добавляем это в поле собственности
            if "долевая" not in ownership_text.lower():
                if ownership_text:
                    ownership_text += ", долевая"
                else:
                    ownership_text = "долевая"
        family_data['ownership'] = clean_string(ownership_text)

        family_data['adpi'] = form_data.get('adpi', 'нет')

        install_date = clean_date(form_data.get('install_date', '').strip())
        if install_date:
            family_data['install_date'] = install_date

        check_date = clean_date(form_data.get('check_date', '').strip())
        if check_date:
            family_data['check_date'] = check_date

        incomes = {}

        # Сохраняем рассчитанное единое пособие, а не проценты
        unified_benefit = clean_string(form_data.get('unified_benefit', '').strip())
        if unified_benefit:
            incomes['unified_benefit'] = unified_benefit

        large_family_benefit = clean_string(form_data.get('large_family_benefit', '').strip())
        if large_family_benefit:
            incomes['large_family_benefit'] = large_family_benefit

        # Добавляем все доходы из формы
        income_fields = [
            'mother_salary', 'father_salary', 'mother_pension', 'father_pension',
            'survivor_pension', 'alimony', 'disability_pension',
            'child_disability_care', 'child_disability_pension', 'general_income'
        ]

        for key in income_fields:
            value = clean_string(form_data.get(key, '').strip())
            if value:
                incomes[key] = value

        if incomes:
            family_data.update(incomes)

        children_count = clean_string(form_data.get('unified_children_count', '').strip())
        if children_count:
            family_data['unified_children_count'] = children_count

        percentage = form_data.get('unified_percentage', '')
        family_data['unified_percentage'] = percentage

        other_incomes = clean_string(form_data.get('other_incomes', '').strip())
        if other_incomes:
            family_data['other_incomes'] = other_incomes

        family_data = clean_family_data(family_data)
        return family_data

    def validate_family(self, family_data):
        """Проверка данных семьи"""
        return validate_family_data(family_data)

    def calculate_unified_benefit(self, children_count, percentage_str):
        """Расчет единого пособия"""
        try:
            children_count = int(children_count)
            if children_count <= 0:
                return None

            percentage = float(percentage_str.replace('%', '')) / 100

            benefit_per_child = self.BASE_UNIFIED_BENEFIT * percentage
            total_benefit = benefit_per_child * children_count

            total_benefit = round(total_benefit)

            return total_benefit
        except ValueError:
            return None

    def fill_from_register_data(self, register_data, fio):
        """Заполнение формы данными из реестра"""
        main_person = register_data['main_person']
        family_members = register_data['family_members']

        # Функция для определения пола по отчеству (без учета регистра)
        def get_gender(patronymic):
            if not patronymic:
                return 'unknown'
            p = patronymic.lower()
            if p.endswith(('на', 'вна', 'ична')):
                return 'female'
            elif p.endswith(('ич', 'вич', 'ыч')):
                return 'male'
            return 'unknown'

        # Функция для получения года рождения
        def get_birth_year(birth_date):
            if not birth_date:
                return None
            try:
                return datetime.strptime(birth_date, '%d.%m.%Y').year
            except:
                return None

        # Собираем всех лиц с их данными, помечая основное лицо
        all_persons = []

        # Добавляем основное лицо (главный заявитель) с флагом is_main=True
        all_persons.append({
            'person': main_person,
            'birth_year': get_birth_year(main_person['birth_date']),
            'gender': get_gender(main_person['patronymic']),
            'is_main': True
        })

        # Добавляем членов семьи с флагом is_main=False
        for member in family_members:
            all_persons.append({
                'person': member,
                'birth_year': get_birth_year(member['birth_date']),
                'gender': get_gender(member['patronymic']),
                'is_main': False
            })

        # Функция для сортировки кандидатов в родители
        def parent_sort_key(person_data):
            """
            Приоритет сортировки:
            - Группа 0: известный год рождения в диапазоне 1920-2000 (явные родители)
            - Группа 1: неизвестный год рождения (могут быть родителями)
            - Группа 2: известный год рождения вне диапазона (скорее всего дети)
            """
            by = person_data['birth_year']
            if by and 1920 <= by <= 2000:
                return (0, by)  # Сначала родители с известным возрастом
            elif by is None:
                return (1, 9999)  # Вторые - с неизвестным возрастом
            else:
                return (2, by)  # Последние - с возрастом вне диапазона (дети)

        # Выбираем мать: самая старшая женщина (с минимальным годом рождения)
        mother = None
        females = [p for p in all_persons if p['gender'] == 'female' and not p['is_main']]
        if females:
            # Сортируем с приоритетом: родители с известным возрастом, затем с неизвестным, затем дети
            females.sort(key=parent_sort_key)
            for female in females:
                by = female['birth_year']
                # Проверяем, что год рождения в разумных пределах (1920-2000)
                if by and 1920 <= by <= 2000:
                    mother = female['person']
                    break
            # Fallback: берем первую, только если это не явный ребенок (год > 2000)
            if not mother and females:
                first = females[0]
                if first['birth_year'] is None or first['birth_year'] <= 2000:
                    mother = first['person']

        # Выбираем отца: самый старый мужчина (с минимальным годом рождения)
        father = None
        males = [p for p in all_persons if p['gender'] == 'male' and not p['is_main']]
        if males:
            males.sort(key=parent_sort_key)
            for male in males:
                by = male['birth_year']
                if by and 1920 <= by <= 2000:
                    father = male['person']
                    break
            # Fallback: берем первого, только если это не явный ребенок (год > 2000)
            if not father and males:
                first = males[0]
                if first['birth_year'] is None or first['birth_year'] <= 2000:
                    father = first['person']

        # Дети - это все, кто не является матерью, отцом И не основное лицо (главный заявитель)
        children = []
        for p in all_persons:
            person = p['person']
            # Проверяем, не является ли это человек основным лицом (главным заявителем)
            # Сравниваем по ФИО и дате рождения, так как объекты могут быть разными
            is_main_person = (
                p['is_main'] or
                (main_person['surname'] == person['surname'] and
                 main_person['name'] == person['name'] and
                 main_person['patronymic'] == person['patronymic'] and
                 main_person['birth_date'] == person['birth_date'])
            )
            # Пропускаем мать, отца и основное лицо
            if (mother and person['surname'] == mother['surname'] and
                person['name'] == mother['name'] and
                person['patronymic'] == mother['patronymic'] and
                person['birth_date'] == mother['birth_date']) or \
               (father and person['surname'] == father['surname'] and
                person['name'] == father['name'] and
                person['patronymic'] == father['patronymic'] and
                person['birth_date'] == father['birth_date']) or \
               is_main_person:
                continue
            children.append(person)

        # Формируем результат
        filled_data = {
            'mother_fio': f"{mother['surname']} {mother['name']} {mother['patronymic']}" if mother else "",
            'mother_birth': mother['birth_date'] if mother else "",
            'father_fio': f"{father['surname']} {father['name']} {father['patronymic']}" if father else "",
            'father_birth': father['birth_date'] if father else "",
            'children': [],
            'phone_number': main_person['phone'],
            'address': self._build_address(register_data['address'])
        }

        # Заполняем детей
        for child in children:
            child_data = {
                'fio': f"{child['surname']} {child['name']} {child['patronymic']}",
                'birth': child['birth_date'],
                'education': ""
            }
            filled_data['children'].append(child_data)

        # Устанавливаем пособие по многодетности по умолчанию 1900
        filled_data['large_family_benefit'] = "1900"

        return filled_data

    def _build_address(self, address_info):
        """Создание строки адреса из частей"""
        address_parts = []
        if address_info.get('city'):
            address_parts.append(f"г. {address_info['city']}")
        if address_info.get('street'):
            address_parts.append(f"ул. {address_info['street']}")
        if address_info.get('house'):
            address_parts.append(f"д. {address_info['house']}")
        return ', '.join(address_parts)

    def is_adult(self, birth_date):
        """Проверка, является ли человек взрослым"""
        try:
            if not birth_date:
                return False
            dt = datetime.strptime(birth_date, '%d.%m.%Y')
            today = datetime.now()
            age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
            return 16 <= age <= 65
        except:
            return False

    def is_child(self, birth_date):
        """Проверка, является ли человек ребенком"""
        try:
            if not birth_date:
                return False
            dt = datetime.strptime(birth_date, '%d.%m.%Y')
            today = datetime.now()
            age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
            return age < 25
        except:
            return False

    def auto_detect_family_from_register(self, search_fio, mother_fio="", father_fio=""):
        """Автоматическое определение семьи из реестра с обработкой дубликатов"""
        if not self.register_data:
            return None, "Сначала загрузите реестр многодетных"

        search_fio = clean_fio(search_fio)
        if not search_fio:
            search_fio = mother_fio or father_fio

        if not search_fio:
            return None, "Введите ФИО матери или отца в форме или в поле поиска"

        normalized_search = normalize_fio(search_fio)

        # Сначала ищем точное совпадение по основному лицу
        for fio_key, family_data in self.register_data.items():
            if normalize_fio(fio_key) == normalized_search:
                return self.fill_from_register_data(family_data, fio_key), "Семья успешно автоопределена"

        # Затем ищем среди всех членов семей
        for fio_key, family_data in self.register_data.items():
            # Проверяем основное лицо
            main_person = family_data['main_person']
            main_fio = f"{main_person['surname']} {main_person['name']} {main_person['patronymic']}"
            if normalize_fio(main_fio) == normalized_search:
                return self.fill_from_register_data(family_data, fio_key), "Семья успешно автоопределена"

            # Проверяем всех членов семьи
            for member in family_data['family_members']:
                member_fio = f"{member['surname']} {member['name']} {member['patronymic']}"
                if normalize_fio(member_fio) == normalized_search:
                    return self.fill_from_register_data(family_data, fio_key), "Семья успешно автоопределена"

        # Если не нашли точное, ищем похожие
        similar_matches = []
        for fio_key, family_data in self.register_data.items():
            # Проверяем основное лицо
            main_person = family_data['main_person']
            main_fio = f"{main_person['surname']} {main_person['name']} {main_person['patronymic']}"
            if is_fio_similar(search_fio, main_fio):
                similar_matches.append((fio_key, family_data, main_fio))
                continue

            # Проверяем членов семьи
            for member in family_data['family_members']:
                member_fio = f"{member['surname']} {member['name']} {member['patronymic']}"
                if is_fio_similar(search_fio, member_fio):
                    similar_matches.append((fio_key, family_data, member_fio))
                    break

        if similar_matches:
            # Возвращаем первое похожее совпадение
            fio_key, family_data, matched_fio = similar_matches[0]
            return self.fill_from_register_data(family_data, fio_key), f"Найдено похожее совпадение: {matched_fio}"

        return None, f"Семья с ФИО '{search_fio}' не найдена в реестре"

    def fill_adpi_from_loaded_data(self, mother_fio="", father_fio=""):
        """Заполнение данных АДПИ из загруженного файла по ФИО"""
        if not self.adpi_data:
            return None, "Сначала загрузите файл АДПИ"

        mother_fio = clean_fio(mother_fio)
        father_fio = clean_fio(father_fio)

        found_data = None
        found_for = ""

        for fio in [mother_fio, father_fio]:
            if fio and fio in self.adpi_data:
                found_data = self.adpi_data[fio]
                found_for = fio
                break

        if not found_data:
            for fio_key in self.adpi_data.keys():
                for search_fio in [mother_fio, father_fio]:
                    if search_fio and is_fio_similar(search_fio, fio_key):
                        found_data = self.adpi_data[fio_key]
                        found_for = fio_key
                        break
                if found_data:
                    break

        if found_data:
            filled_data = {
                'address': found_data['address'],
                'adpi': 'да' if found_data['install_date'] or found_data['check_date'] else 'нет',
                'install_date': found_data['install_date'],
                'check_date': found_data['check_date']
            }
            return filled_data, f"Данные АДПИ и адрес заполнены для: {found_for}"
        else:
            return None, f"Не найдены данные АДПИ для:\nМать: {mother_fio}\nОтец: {father_fio}"
