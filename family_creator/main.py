"""Основной исполняемый файл для генератора JSON файлов с семьями"""

import sys
import os
import traceback
from tkinter import messagebox

# Добавляем путь к корню проекта для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from family_creator.gui import JSONFamilyCreatorGUI


def main():
    """Основная функция запуска приложения"""
    try:
        app = JSONFamilyCreatorGUI()
        app.run()
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"Критическая ошибка при запуске приложения: {error_msg}")
        messagebox.showerror(
            "Критическая ошибка", 
            f"Приложение не может быть запущено:\n\n{str(e)}\n\n"
            "Проверьте наличие всех необходимых библиотек и файлов конфигурации."
        )


if __name__ == "__main__":
    main()