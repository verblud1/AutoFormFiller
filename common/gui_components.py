"""Общие GUI компоненты для приложений"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext, filedialog
import threading
import json
from datetime import datetime
import os
import re
import shutil
import traceback
import pandas as pd
import numpy as np
from dateutil import parser
import subprocess
import platform


class BaseGUI:
    """Базовый класс для GUI приложений"""
    
    def __init__(self):
        self.app = None
        self.tabview = None
        self.setup_base_ui()
        
    def setup_base_ui(self):
        """Настройка базового пользовательского интерфейса"""
        self.app = ctk.CTk()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
    def setup_mouse_wheel_binding(self):
        """Настройка прокрутки колесиком мыши для всех вкладок"""
        # Привязываем прокрутку к основному окну
        self.app.bind("<MouseWheel>", self._on_mousewheel)  # Windows
        self.app.bind("<Button-4>", self._on_mousewheel)    # Linux
        self.app.bind("<Button-5>", self._on_mousewheel)    # Linux
        
        # Привязываем к дочерним виджетам (без tabview, так как он не поддерживает bind)
        for tab_name in ["auto_tab", "family_tab", "children_tab", "housing_tab", "income_tab", "adpi_tab", "manage_tab"]:
            if hasattr(self, tab_name):
                tab = getattr(self, tab_name)
                try:
                    tab.bind("<MouseWheel>", self._on_mousewheel)
                    tab.bind("<Button-4>", self._on_mousewheel)
                    tab.bind("<Button-5>", self._on_mousewheel)
                except:
                    # Некоторые виджеты могут не поддерживать bind
                    pass
                
                # Рекурсивно привязываем ко всем дочерним элементам
                self._bind_mousewheel_recursive(tab, self._on_mousewheel)
    
    def _bind_mousewheel_recursive(self, widget, callback):
        """Рекурсивная привязка события прокрутки ко всем дочерним виджетам"""
        try:
            for child in widget.winfo_children():
                try:
                    child.bind("<MouseWheel>", callback)  # Windows
                    child.bind("<Button-4>", callback)    # Linux
                    child.bind("<Button-5>", callback)    # Linux
                except:
                    # Некоторые виджеты могут не поддерживать bind
                    pass
                # Рекурсивный вызов для вложенных виджетов
                self._bind_mousewheel_recursive(child, callback)
        except:
            # Некоторые виджеты могут не поддерживать winfo_children()
            pass
    
    def _on_mousewheel(self, event):
        """Обработка события прокрутки колесиком мыши"""
        # Определяем направление прокрутки в зависимости от ОС
        if event.num == 4 or event.delta > 0:
            direction = -1  # Вверх
        elif event.num == 5 or event.delta < 0:
            direction = 1   # Вниз
        else:
            return
        
        # Находим виджет, над которым находится курсор
        widget = event.widget
        self._scroll_widget_if_scrollable(widget, direction)
    
    def _scroll_widget_if_scrollable(self, widget, direction):
        """Прокрутка виджета, если он поддерживает прокрутку"""
        # Проверяем, является ли виджет прокручиваемым фреймом
        if hasattr(widget, 'yview') and callable(getattr(widget, 'yview', None)):
            # Это может быть Text, Listbox, Canvas или виджет с прокруткой
            try:
                if direction == -1:
                    widget.yview_scroll(-1, "units")
                else:
                    widget.yview_scroll(1, "units")
            except:
                pass
        elif widget.__class__.__name__ in ['CTkScrollableFrame']:
            # Обработка CTkScrollableFrame - ищем внутренний canvas и прокручиваем его
            try:
                # Прокручиваем сам фрейм
                if direction == -1:
                    widget._parent_canvas.yview_scroll(-1, "units")
                else:
                    widget._parent_canvas.yview_scroll(1, "units")
            except:
                # Если прямой доступ не работает, пробуем рекурсивно найти canvas
                canvas = self._find_canvas_in_widget(widget)
                if canvas:
                    try:
                        if direction == -1:
                            canvas.yview_scroll(-1, "units")
                        else:
                            canvas.yview_scroll(1, "units")
                    except:
                        pass
        
        # Рекурсивно проверяем родительские виджеты
        parent = widget.master if hasattr(widget, 'master') else None
        if parent and parent != self.app:
            self._scroll_widget_if_scrollable(parent, direction)
    
    def _find_canvas_in_widget(self, widget):
        """Поиск canvas внутри виджета для прокрутки"""
        try:
            # Проверяем, есть ли у виджета _parent_canvas
            if hasattr(widget, '_parent_canvas'):
                return widget._parent_canvas
            # Ищем canvas рекурсивно среди дочерних элементов
            for child in widget.winfo_children():
                if child.__class__.__name__ in ['Canvas', 'tkinter.Canvas', 'customtkinter.CTkCanvas']:
                    return child
                canvas = self._find_canvas_in_widget(child)
                if canvas:
                    return canvas
        except:
            pass
        return None
    
    def _get_all_children(self, widget):
        """Получение всех дочерних виджетов рекурсивно"""
        children = [widget]
        for child in widget.winfo_children():
            children.extend(self._get_all_children(child))
        return children
    
    def create_income_field(self, parent, label, key):
        """Создание поля для ввода дохода"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(frame, text=label).pack(anchor="w", padx=5)
        
        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x", padx=5, pady=2)
        entry = ctk.CTkEntry(entry_frame, placeholder_text="Введите сумму или оставьте пустым")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(entry_frame, text="0", width=40,
                     command=lambda e=entry: e.delete(0, 'end')).pack(side="left", padx=5)
        
        return entry
    
    def log_message(self, message, log_widget=None):
        """Добавление сообщения в лог"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_text = f"[{timestamp}] {message}\n"
            
            if log_widget:
                log_widget.config(state="normal")
                log_widget.insert("end", log_text)
                log_widget.see("end")
                log_widget.config(state="disabled")
            
            print(log_text)
        except:
            pass
    
    def setup_scrollbar_visibility(self):
        """Улучшение видимости полос прокрутки"""
        # Настройка стиля полос прокрутки для лучшей видимости
        try:
            # Попытка настроить видимость полос прокрутки в CTk
            ctk.set_widget_scaling(1.0)  # Устанавливаем масштаб виджетов
        except:
            pass
        
        # Обновляем все виджеты для лучшей видимости полос прокрутки
        self.app.update_idletasks()
    
    def on_closing(self):
        """Обработка закрытия программы"""
        if messagebox.askyesno("Подтверждение выхода", "Вы уверены, что хотите выйти?"):
            self.app.quit()