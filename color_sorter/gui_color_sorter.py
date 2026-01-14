#!/usr/bin/env python3
"""GUI интерфейс для сортировки семей в Excel файле по цветам заливки"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import customtkinter as ctk
import threading
import os
import sys
from pathlib import Path

# Добавляем путь к текущей директории для импорта
sys.path.insert(0, str(Path(__file__).parent))

from sort_families_by_colors import group_families_by_color, create_sorted_excel, print_color_statistics


class ColorSorterGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Сортировка семей по цветам заливки")
        self.geometry("800x700")
        
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(4, weight=1)
        
        # Переменные
        self.input_file_path = tk.StringVar()
        self.families_by_color = None
        
        # Создание интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Заголовок
        title_label = ctk.CTkLabel(
            self, 
            text="Сортировка семей по цветам заливки", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # Выбор файла
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew", columnspan=2)
        file_frame.grid_columnconfigure(1, weight=1)
        
        file_label = ctk.CTkLabel(file_frame, text="Файл Excel:", font=ctk.CTkFont(size=14))
        file_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        file_entry = ctk.CTkEntry(file_frame, textvariable=self.input_file_path, width=500)
        file_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        browse_button = ctk.CTkButton(
            file_frame, 
            text="Выбрать файл", 
            command=self.browse_file,
            width=100
        )
        browse_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Кнопка анализа
        self.analyze_button = ctk.CTkButton(
            self, 
            text="Анализ", 
            command=self.analyze_file,
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.analyze_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew", columnspan=2)
        
        # Консоль для вывода
        console_label = ctk.CTkLabel(self, text="Статистика:", font=ctk.CTkFont(size=14))
        console_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.console = scrolledtext.ScrolledText(
            self, 
            wrap=tk.WORD, 
            width=70, 
            height=15,
            font=("Consolas", 10)
        )
        self.console.grid(row=4, column=0, padx=20, pady=10, sticky="nsew", columnspan=2)
        
        # Кнопка сохранения
        self.save_button = ctk.CTkButton(
            self, 
            text="Сохранить отсортированный файл", 
            command=self.save_sorted_file,
            font=ctk.CTkFont(size=14),
            height=40,
            state=tk.DISABLED
        )
        self.save_button.grid(row=5, column=0, padx=20, pady=20, sticky="ew", columnspan=2)
        
    def browse_file(self):
        """Выбор файла Excel"""
        file_path = filedialog.askopenfilename(
            title="Выберите Excel файл",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.input_file_path.set(file_path)
            
    def analyze_file(self):
        """Анализ файла в отдельном потоке"""
        if not self.input_file_path.get():
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите файл Excel")
            return
            
        if not os.path.exists(self.input_file_path.get()):
            messagebox.showerror("Ошибка", "Файл не найден")
            return
            
        # Отключаем кнопки на время анализа
        self.analyze_button.configure(state=tk.DISABLED)
        self.save_button.configure(state=tk.DISABLED)
        
        # Очищаем консоль
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "Начинаем анализ файла...\n")
        self.console.see(tk.END)
        
        # Запускаем анализ в отдельном потоке
        thread = threading.Thread(target=self._analyze_file_thread)
        thread.daemon = True
        thread.start()
        
    def _analyze_file_thread(self):
        """Функция анализа в отдельном потоке"""
        try:
            file_path = self.input_file_path.get()
            
            # Обновляем консоль
            self._update_console(f"Обработка файла: {file_path}\n")
            
            # Группируем семьи по цветам
            self.families_by_color = group_families_by_color(file_path)
            
            # Выводим статистику в консоль
            self._display_statistics(self.families_by_color)
            
            # Обновляем состояние кнопок
            self.after(0, lambda: self.analyze_button.configure(state=tk.NORMAL))
            self.after(0, lambda: self.save_button.configure(state=tk.NORMAL))
            
        except Exception as e:
            self._update_console(f"Ошибка при обработке файла: {str(e)}\n")
            import traceback
            self._update_console(traceback.format_exc())
            self.after(0, lambda: self.analyze_button.configure(state=tk.NORMAL))
            
    def _update_console(self, text):
        """Обновление консоли из потока"""
        self.after(0, lambda: self.console.insert(tk.END, text))
        self.after(0, lambda: self.console.see(tk.END))
        
    def _display_statistics(self, families_by_color):
        """Отображение статистики"""
        stats_text = "\nСтатистика по цветам заливки семей:\n"
        stats_text += "="*50 + "\n"
        
        total_families = sum(len(families) for families in families_by_color.values())
        
        # Классификация цветов по статусам
        refused_calls = 0  # Не ответили на звонок (красный)
        done_entries = 0   # Занесено в базу (желтый, зеленый)
        not_filled = 0     # Еще не сделано (без заливки, белый)
        done_not_entered = 0  # Сделано, но не занесено (серый)
        other_colors = 0   # Другие цвета
        
        color_classification = {
            'FF0066CC': 'Другой цвет',
            'FF03FF00': 'Занесено в базу',  # зеленый
            'FF333399': 'Другой цвет',
            'FF339966': 'Другой цвет',
            'FF800080': 'Другой цвет',
            'FFC0C0C0': 'Сделано, но не занесено',  # серый
            'FFFF0000': 'Не ответили на звонок',  # красный
            'FFFFCC99': 'Другой цвет',
            'FFFFFF00': 'Занесено в базу',  # желтый
            'FFFFFF99': 'Другой цвет',
            'FFFFFFFF': 'Еще не сделано'  # белый
        }
        
        # Сортируем цвета для вывода
        sorted_items = sorted(
            [(k, v) for k, v in families_by_color.items() if k is not None],
            key=lambda x: x[0]
        )
        
        if None in families_by_color:
            sorted_items.append((None, families_by_color[None]))
        
        for color, families in sorted_items:
            count = len(families)
            if color is None:
                not_filled += count
                stats_text += f"Без заливки: {count} семей ({count/total_families*100:.1f}%)\n"
            else:
                color_status = color_classification.get(color, 'Другой цвет')
                stats_text += f"Цвет {color} ({color_status}): {count} семей ({count/total_families*100:.1f}%)\n"
                
                if color == 'FFFF0000':  # Красный - не ответили на звонок
                    refused_calls = count
                elif color in ['FFFFFF00', 'FF03FF00']:  # Желтый и зеленый - занесено в базу
                    done_entries += count
                elif color == 'FFFFFFFF':  # Белый - еще не сделано
                    not_filled += count
                elif color == 'FFC0C0C0':  # Серый - сделано, но не занесено
                    done_not_entered += count
                else:
                    other_colors += count
        
        # Подсчитываем "другие цвета" для неучтенных
        other_colors = total_families - (refused_calls + done_entries + not_filled + done_not_entered)
        
        stats_text += f"\nВсего семей: {total_families}\n"
        stats_text += "="*50 + "\n"
        stats_text += "Классификация по статусам:\n"
        stats_text += f"- Не ответили на звонок (красный): {refused_calls} ({refused_calls/total_families*100:.1f}%)\n"
        stats_text += f"- Занесено в базу (желтый/зеленый): {done_entries} ({done_entries/total_families*100:.1f}%)\n"
        stats_text += f"- Еще не сделано (без заливки/белый): {not_filled} ({not_filled/total_families*100:.1f}%)\n"
        stats_text += f"- Сделано, но не занесено (серый): {done_not_entered} ({done_not_entered/total_families*100:.1f}%)\n"
        stats_text += f"- Другие цвета: {other_colors} ({other_colors/total_families*100:.1f}%)\n"
        stats_text += "="*50 + "\n"
        
        self._update_console(stats_text)
        
    def save_sorted_file(self):
        """Сохранение отсортированного файла"""
        if not self.families_by_color:
            messagebox.showwarning("Предупреждение", "Сначала выполните анализ файла")
            return
            
        output_path = filedialog.asksaveasfilename(
            title="Сохранить отсортированный файл",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if output_path:
            try:
                # Показываем сообщение
                self._update_console(f"\nСохраняем файл: {output_path}\n")
                
                # Создаем отсортированный Excel файл
                create_sorted_excel(self.families_by_color, output_path)
                
                self._update_console(f"Файл успешно сохранен: {output_path}\n")
                messagebox.showinfo("Успех", f"Файл успешно сохранен:\n{output_path}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении файла:\n{str(e)}")


def main():
    app = ColorSorterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()