"""Тест режима PyInstaller для копирования файлов"""

import sys
import os
import shutil

def test_pyinstaller_mode():
    """Тест определения пути в режиме PyInstaller"""
    from family_creator.gui import JSONFamilyCreatorGUI
    
    # Сохраняем оригинальные значения
    original_frozen = getattr(sys, 'frozen', None)
    original_executable = getattr(sys, 'executable', None)
    
    try:
        # Имитируем режим PyInstaller
        sys.frozen = True
        sys.executable = r"C:\Test\AutoFormFiller.exe"
        
        # Создаем экземпляр GUI
        gui = object.__new__(JSONFamilyCreatorGUI)
        base_dir = gui.get_base_project_dir()
        
        print("[TEST] Режим PyInstaller:")
        print("   sys.executable: {}".format(sys.executable))
        print("   Базовый путь: {}".format(base_dir))
        
        # Проверяем, что путь ведет к папке, где находится exe
        expected = r"C:\Test"
        if base_dir == expected:
            print("[OK] Путь определен корректно")
            return True
        else:
            print("[ERROR] Ожидалось: {}, получено: {}".format(expected, base_dir))
            return False
    finally:
        # Восстанавливаем оригинальные значения
        if original_frozen is not None:
            sys.frozen = original_frozen
        elif hasattr(sys, 'frozen'):
            delattr(sys, 'frozen')
        if original_executable is not None:
            sys.executable = original_executable

def test_normal_mode():
    """Тест обычного режима"""
    from family_creator.gui import JSONFamilyCreatorGUI
    
    try:
        gui = object.__new__(JSONFamilyCreatorGUI)
        base_dir = gui.get_base_project_dir()
        
        print("\n[TEST] Обычный режим:")
        print("   Базовый путь: {}".format(base_dir))
        
        # Проверяем, что путь ведет к папке с gui.py
        expected_suffix = r"family_creator"
        if base_dir.endswith(expected_suffix):
            print("[OK] Путь определен корректно")
            return True
        else:
            print("[ERROR] Путь не заканчивается на {}".format(expected_suffix))
            return False
    except Exception as e:
        print("[ERROR] Исключение: {}".format(e))
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Тест режимов работы (PyInstaller vs Обычный)")
    print("=" * 60)
    
    test1 = test_normal_mode()
    test2 = test_pyinstaller_mode()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("[SUCCESS] Все тесты пройдены!")
    else:
        print("[FAIL] Некоторые тесты не пройдены")
    print("=" * 60)
