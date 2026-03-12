"""Тестовый скрипт для проверки функции копирования файлов"""

import sys
import os
import shutil

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_get_base_project_dir():
    """Тест определения базового пути проекта"""
    from family_creator.gui import JSONFamilyCreatorGUI
    
    # Создаем экземпляр GUI (без отображения окна)
    try:
        # Создаем минимальный экземпляр для теста
        gui = object.__new__(JSONFamilyCreatorGUI)
        
        # Вызываем только нужные методы для определения путей
        base_dir = gui.get_base_project_dir()
        print("[OK] Базовый путь проекта: {}".format(base_dir))
        
        # Проверяем существование папок
        registry_path = os.path.join(base_dir, "registry")
        adpi_path = os.path.join(base_dir, "adpi")
        
        reg_exists = "существует" if os.path.exists(registry_path) else "будет создана"
        adpi_exists = "существует" if os.path.exists(adpi_path) else "будет создана"
        print("   Папка registry: {} ({})".format(registry_path, reg_exists))
        print("   Папка adpi: {} ({})".format(adpi_path, adpi_exists))
        
        return True
    except Exception as e:
        print("[ERROR] Ошибка: {}".format(e))
        import traceback
        traceback.print_exc()
        return False

def test_copy_file():
    """Тест копирования файла"""
    from family_creator.gui import JSONFamilyCreatorGUI
    
    try:
        gui = object.__new__(JSONFamilyCreatorGUI)
        gui.base_project_dir = gui.get_base_project_dir()
        gui.registry_dir = os.path.join(gui.base_project_dir, "registry")
        gui.adpi_dir = os.path.join(gui.base_project_dir, "adpi")
        
        # Создаем тестовый файл
        test_source = "test_source.xlsx"
        with open(test_source, 'w') as f:
            f.write("test data")
        
        # Тестируем копирование
        success, result = gui.copy_file_to_project_folder(test_source, gui.registry_dir)
        if success:
            print("[OK] Файл скопирован успешно в: {}".format(result))
            # Проверяем, что файл существует
            if os.path.exists(result):
                print("[OK] Файл существует в целевой папке")
            else:
                print("[ERROR] Файл не найден в целевой папке")
        else:
            print("[ERROR] Ошибка копирования: {}".format(result))
        
        # Очищаем
        if os.path.exists(test_source):
            os.remove(test_source)
        if os.path.exists(result):
            os.remove(result)
        
        return success
    except Exception as e:
        print("[ERROR] Ошибка теста: {}".format(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Тест функциональности копирования файлов")
    print("=" * 60)
    
    print("\n1. Тест определения базового пути:")
    test1 = test_get_base_project_dir()
    
    print("\n2. Тест копирования файла:")
    test2 = test_copy_file()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("[SUCCESS] Все тесты пройдены успешно!")
    else:
        print("[FAIL] Некоторые тесты не пройдены")
    print("=" * 60)
