#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Экспорт ФИО матерей из JSON файлов в текстовый файл
"""

import os
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
import re


def extract_mothers_from_week_folder(week_folder_path):
    """
    Извлекает ФИО матерей из всех JSON файлов в папке недели
    
    Args:
        week_folder_path (str): Путь к папке недели (например, 'files/for/fill/queue/completed/2026-W03')
    
    Returns:
        tuple: (list of mothers_fio, total_families_count)
    """
    mothers_fio = []
    total_families_count = 0
    
    # Найти все JSON файлы в папке недели
    for filename in os.listdir(week_folder_path):
        if filename.endswith('_completed_families.json'):
            json_file_path = os.path.join(week_folder_path, filename)
            
            # Загрузить JSON файл
            with open(json_file_path, 'r', encoding='utf-8') as f:
                families_data = json.load(f)
                
            # Извлечь ФИО матерей
            for family in families_data:
                mother_fio = family.get('mother_fio', '').strip()
                if mother_fio:
                    mothers_fio.append(mother_fio)
                    
            total_families_count += len(families_data)
    
    return mothers_fio, total_families_count


def export_mothers_to_txt(mothers_fio, output_folder, week_name, total_families_count):
    """
    Экспортирует ФИО матерей в текстовый файл
    
    Args:
        mothers_fio (list): Список ФИО матерей
        output_folder (str): Папка для сохранения файла
        week_name (str): Название недели (например, '2026-W03')
        total_families_count (int): Общее количество семей
    """
    # Получить дату из названия недели для имени файла
    # Преобразовать '2026-W03' в формат даты
    year, week_num = week_name.split('-W')
    week_num = int(week_num)
    
    # Вычислить дату первого дня недели
    date_obj = datetime.strptime(f'{year}-{week_num}-1', '%Y-%U-%w')
    date_str = date_obj.strftime('%d.%m.%Y')
    
    # Сформировать имя файла
    filename = f"{date_str}_exported_mothers.txt"
    filepath = os.path.join(output_folder, filename)
    
    # Записать ФИО матерей в файл
    with open(filepath, 'a', encoding='utf-8') as f:
        for mother_fio in mothers_fio:
            f.write(mother_fio + '\n')
        
        # Добавить информацию о количестве заполненных семей в конце файла
        f.write(f"\nЗаполнено: {total_families_count}\n")
    
    return filepath


def select_and_export_mothers():
    """
    Основная функция для выбора папки недели и экспорта ФИО матерей
    """
    # Создать главное окно
    root = ctk.CTk()
    root.withdraw()  # Скрыть главное окно
    
    # Запросить у пользователя выбор папки недели
    week_folder = filedialog.askdirectory(
        title="Выберите папку с неделями",
        initialdir=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "files for fill queue", "completed")
    )
    
    if not week_folder:
        messagebox.showinfo("Информация", "Не выбрана папка.")
        return
    
    # Проверить, что это действительно папка недели (содержит 'W' в названии)
    week_folder_name = os.path.basename(week_folder)
    if not re.match(r'\d{4}-W\d{2}', week_folder_name):
        messagebox.showerror("Ошибка", "Выбранная папка не соответствует формату недели (например, 2026-W03)")
        return
    
    try:
        # Извлечь ФИО матерей
        mothers_fio, total_families_count = extract_mothers_from_week_folder(week_folder)
        
        if not mothers_fio:
            messagebox.showinfo("Информация", "В выбранных файлах не найдено ФИО матерей.")
            return
        
        # Запросить папку для сохранения файла
        output_folder = filedialog.askdirectory(
            title="Выберите папку для сохранения текстового файла",
            initialdir=os.path.dirname(week_folder)
        )
        
        if not output_folder:
            messagebox.showinfo("Информация", "Не выбрана папка для сохранения.")
            return
        
        # Экспортировать ФИО матерей в текстовый файл
        output_filepath = export_mothers_to_txt(mothers_fio, output_folder, week_folder_name, total_families_count)
        
        # Показать сообщение об успешном экспорте
        messagebox.showinfo(
            "Успех", 
            f"ФИО матерей успешно экспортированы!\n"
            f"Файл сохранен: {output_filepath}\n"
            f"Найдено ФИО матерей: {len(mothers_fio)}\n"
            f"Всего семей: {total_families_count}"
        )
        
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при экспорте:\n{str(e)}")
    
    finally:
        root.destroy()


if __name__ == "__main__":
    select_and_export_mothers()