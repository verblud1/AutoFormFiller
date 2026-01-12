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
        """Заполнение формы данными из реестра с обработкой возраста"""
        mother = None
        father = None
        children = []
        potential_fathers = []
        potential_children = []
        
        main_person = register_data['main_person']
        
        # Проверка года рождения основного лица
        if main_person['birth_date']:
            try:
                birth_dt = datetime.strptime(main_person['birth_date'], '%d.%m.%Y')
                # НОВОЕ: родитель не может родиться после 2003
                if birth_dt.year > 2003:
                    # Это может быть ребенок старше 18 лет
                    if birth_dt.year >= 2000:  # Родился после 2000
                        potential_children.append(main_person)
                    else:
                        # Родился до 2000 - это родитель
                        if main_person['patronymic'].endswith(('на', 'вна', 'ична')):
                            mother = main_person
                        else:
                            potential_fathers.append(main_person)
                else:
                    # Родился до или в 2003 - это родитель
                    if main_person['patronymic'].endswith(('на', 'вна', 'ична')):
                        mother = main_person
                    else:
                        potential_fathers.append(main_person)
            except:
                # Если дата некорректна, определяем по отчеству
                if main_person['patronymic'].endswith(('на', 'вна', 'ична')):
                    mother = main_person
                else:
                    potential_fathers.append(main_person)
        
        # Анализируем членов семьи
        for member in register_data['family_members']:
            if member['birth_date']:
                try:
                    birth_dt = datetime.strptime(member['birth_date'], '%d.%m.%Y')
                    
                    # НОВОЕ: ребенок не может родиться до 2000
                    if birth_dt.year < 2000:
                        # Родился до 2000 - это родитель
                        if member['patronymic'].endswith(('на', 'вна', 'ична')):
                            if not mother:
                                mother = member
                        else:
                            potential_fathers.append(member)
                        continue
                    
                    # Родитель не может родиться после 2003
                    if birth_dt.year > 2003:
                        # Это ребенок
                        potential_children.append(member)
                        continue
                    
                    # Для 2000-2003 определяем по отчеству
                    if member['patronymic'].endswith(('на', 'вна', 'ична')):
                        # Женский пол
                        if not mother:
                            mother = member
                        elif not father and birth_dt.year <= 2003:
                            # Если отчества нет, но год подходит для отца
                            potential_fathers.append(member)
                        else:
                            potential_children.append(member)
                    elif member['patronymic'].endswith(('ич', 'вич', 'ыч')):
                        # Мужской пол
                        if birth_dt.year <= 2003:  # Может быть отцом
                            if not father and birth_dt.year >= 1980:  # Разумный возраст для отца
                                potential_fathers.append(member)
                            else:
                                potential_children.append(member)
                        else:
                            potential_children.append(member)
                    else:
                        # Неопределенное отчество
                        if birth_dt.year <= 2003 and not mother:
                            mother = member
                        else:
                            potential_children.append(member)
                            
                except:
                    # Если дата некорректна, определяем по отчеству
                    if member['patronymic'].endswith(('на', 'вна', 'ична')):
                        if not mother:
                            mother = member
                        else:
                            potential_children.append(member)
                    elif member['patronymic'].endswith(('ич', 'вич', 'ыч')):
                        potential_fathers.append(member)
                    else:
                        potential_children.append(member)
        
        # Выбираем отца из потенциальных кандидатов
        if potential_fathers:
            # Ищем наиболее подходящего (старше, но не слишком)
            potential_fathers.sort(key=lambda x: datetime.strptime(x['birth_date'], '%d.%m.%Y') if x['birth_date'] else datetime(1900, 1, 1))
            father = potential_fathers[0]
        
        # Все остальные - дети
        children = potential_children
        
        # НОВОЕ: проверяем, не попал ли ребенок старше 2010 года в отцы
        if father:
            try:
                birth_dt = datetime.strptime(father['birth_date'], '%d.%m.%Y')
                if birth_dt.year > 2010:
                    # Это слишком молодой для отца - перемещаем в дети
                    children.append(father)
                    father = None
            except:
                pass
        
        # Возвращаем заполненные данные для формы
        filled_data = {
            'mother_fio': f"{mother['surname']} {mother['name']} {mother['patronymic']}" if mother else "",
            'mother_birth': mother['birth_date'] if mother else "",
            'father_fio': f"{father['surname']} {father['name']} {father['patronymic']}" if father else "",
            'father_birth': father['birth_date'] if father else "",
            'children': [],
            'phone_number': register_data['main_person']['phone'],
            'address': self._build_address(register_data['address'])
        }
        
        # Заполняем детей
        for child in children:
            child_data = {
                'fio': f"{child['surname']} {child['name']} {child['patronymic']}",
                'birth': child['birth_date'],
                'education': ""  # Education нужно заполнять отдельно
            }
            filled_data['children'].append(child_data)
        
        # НОВОЕ: Устанавливаем пособие по многодетности по умолчанию 1900
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
        
        # Ищем все совпадения
        exact_matches = []
        similar_matches = []
        
        for fio_key in self.register_data.keys():
            if normalize_fio(search_fio) == normalize_fio(fio_key):
                exact_matches.append((fio_key, self.register_data[fio_key]))
            elif is_fio_similar(search_fio, fio_key):
                similar_matches.append((fio_key, self.register_data[fio_key]))
        
        # Обработка случая, когда найдено несколько семей
        if len(exact_matches) > 1:
            return None, f"Найдено {len(exact_matches)} семей с одинаковыми ФИО"
        elif len(exact_matches) == 1:
            found_data = exact_matches[0][1]
            found_fio = exact_matches[0][0]
        elif similar_matches:
            if len(similar_matches) > 1:
                # Если много похожих, возвращаем первый вариант
                found_data = similar_matches[0][1]
                found_fio = similar_matches[0][0]
            else:
                found_data = similar_matches[0][1]
                found_fio = similar_matches[0][0]
        else:
            return None, f"Семья с ФИО '{search_fio}' не найдена в реестре"
        
        # Заполняем данные из реестра
        filled_data = self.fill_from_register_data(found_data, found_fio)
        return filled_data, "Семья успешно автоопределена"
    
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