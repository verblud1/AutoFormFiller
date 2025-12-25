import os
import platform
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import requests
from packaging import version


def get_chrome_version():
    """Получение версии Chrome"""
    system = platform.system().lower()
    try:
        if system == "windows":
            import winreg
            # Путь к версии Chrome в реестре
            chrome_path = r"SOFTWARE\Google\Chrome\BLBeacon"
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chrome_path) as key:
                    version_num = winreg.QueryValueEx(key, "version")[0]
                    return version_num
            except FileNotFoundError:
                # Альтернативный способ для Windows - поиск в стандартной директории
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ]
                for path in chrome_paths:
                    if os.path.exists(path):
                        result = subprocess.run([path, "--version"], capture_output=True, text=True)
                        version_output = result.stdout.strip()
                        # Извлечение версии из строки вроде "Google Chrome 19.0.5414.120"
                        version_part = version_output.split()[-1]
                        return version_part
        elif system == "linux":
            result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version_output = result.stdout.strip()
                version_part = version_output.split()[-1]
                return version_part
    except Exception:
        pass
    return None


def is_compatible_version(driver_version, browser_version):
    """Проверка совместимости версий ChromeDriver и Chrome"""
    try:
        # Для старых версий Chrome используем упрощенную проверку
        driver_ver = version.parse(driver_version)
        browser_ver = version.parse(browser_version)
        
        # Если версия браузера 19.x, то нужен соответствующий старый драйвер
        if browser_ver.major == 19:
            return driver_ver.major == 19
        elif browser_ver.major <= 115:
            # Для более старых версий Chrome используем старые драйверы
            return driver_ver.major <= 115
        else:
            # Для новых версий - стандартная проверка
            return driver_ver.major == browser_ver.major
    except:
        # Если не удается распарсить, возвращаем True как запасной вариант
        return True


def download_chrome_driver_for_old_version(version, download_path):
    """Скачивание ChromeDriver для старой версии Chrome"""
    # Для версии Chrome 19.x нужно использовать ChromeDriver версии 2.x
    print(f"Попытка загрузки ChromeDriver для старой версии Chrome: {version}")
    
    # Попробуем использовать ChromeDriver 2.x для Chrome 19
    old_versions = ['2.10', '2.9', '2.8', '2.7', '2.6', '2.5', '2.4', '2.3', '2.2', '2.1', '2.0']
    
    for old_ver in old_versions:  # Начинаем с более новых
        try:
            print(f"Пробуем загрузить ChromeDriver версии {old_ver} через webdriver-manager...")
            driver_path = ChromeDriverManager(version=f"{old_ver}").install()
            print(f"Успешно загружен ChromeDriver: {driver_path}")
            return driver_path
        except Exception as e:
            print(f"webdriver-manager не смог загрузить ChromeDriver {old_ver}: {e}")
            continue
    
    # Если webdriver-manager не может, скачиваем вручную
    print("Попытка загрузки ChromeDriver вручную...")
    return download_old_chrome_driver_manually(download_path)


def download_old_chrome_driver_manually(download_path):
    """Ручное скачивание старого ChromeDriver"""
    # Для Chrome 19 подойдет ChromeDriver 2.0 - 2.10
    # Пробуем скачать подходящую версию
    system = platform.system().lower()
    
    # Определяем URL в зависимости от операционной системы
    if system == "windows":
        old_driver_urls = [
            "https://chromedriver.storage.googleapis.com/2.9/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.8/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.7/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.6/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.5/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.4/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.3/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.2/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.1/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.0/chromedriver_win32.zip"
        ]
    elif system in ["linux", "redos"]:
        old_driver_urls = [
            "https://chromedriver.storage.googleapis.com/2.9/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.8/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.7/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.6/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.5/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.4/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.3/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.2/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.1/chromedriver_linux64.zip",
            "https://chromedriver.storage.googleapis.com/2.0/chromedriver_linux64.zip"
        ]
    else:
        # Для других систем используем URL для Windows как fallback
        old_driver_urls = [
            "https://chromedriver.storage.googleapis.com/2.9/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.8/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.7/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.6/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.5/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.4/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.3/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.2/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.1/chromedriver_win32.zip",
            "https://chromedriver.storage.googleapis.com/2.0/chromedriver_win32.zip"
        ]
    
    import zipfile
    
    for url in old_driver_urls:
        try:
            print(f"Попытка загрузки ChromeDriver: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                zip_path = os.path.join(download_path, "chromedriver.zip")
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                # Распаковываем архив
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(download_path)
                
                # Удаляем архив
                os.remove(zip_path)
                
                # Ищем исполняемый файл chromedriver
                driver_name = "chromedriver.exe" if system == "windows" else "chromedriver"
                driver_path = os.path.join(download_path, driver_name)
                
                if os.path.exists(driver_path):
                    # Делаем файл исполняемым в Linux
                    if system in ["linux", "redos"]:
                        os.chmod(driver_path, 0o755)
                    
                    print(f"ChromeDriver успешно загружен: {driver_path}")
                    return driver_path
        except Exception as e:
            print(f"Ошибка загрузки {url}: {e}")
            continue
    
    return None


def setup_chrome_driver():
    """Настройка ChromeDriver с учетом старых версий"""
    system = platform.system().lower()
    chrome_version = get_chrome_version()
    
    print(f"Обнаруженная версия Chrome: {chrome_version}")
    
    # Создаем директорию для драйверов
    driver_dir = os.path.join(os.path.dirname(__file__), "drivers")
    os.makedirs(driver_dir, exist_ok=True)
    
    if chrome_version:
        # Проверяем, является ли версия старой (ниже 70)
        major_version = int(chrome_version.split('.')[0]) if chrome_version.split('.')[0].isdigit() else 0
        
        if major_version < 70:
            print(f"Обнаружена старая версия Chrome ({chrome_version}), используем совместимый драйвер...")
            
            # Для старых версий Chrome используем альтернативный подход
            driver_path = download_chrome_driver_for_old_version(chrome_version, driver_dir)
            
            if driver_path and os.path.exists(driver_path):
                print(f"Используем ChromeDriver: {driver_path}")
            else:
                # Если не удалось получить подходящий драйвер, пробуем использовать любой доступный
                print("Попытка использования последней доступной версии ChromeDriver...")
                try:
                    driver_path = ChromeDriverManager().install()
                except:
                    # Если ничего не помогает, возвращаем None и будем использовать альтернативный подход
                    print("Не удалось получить подходящий ChromeDriver")
                    return None
        else:
            # Для новых версий используем стандартный подход
            try:
                driver_path = ChromeDriverManager().install()
            except Exception as e:
                print(f"Ошибка установки ChromeDriver через webdriver-manager: {e}")
                return None
    else:
        # Если версию Chrome определить не удалось, используем последнюю версия драйвера
        print("Не удалось определить версию Chrome, используем последнюю версию ChromeDriver")
        try:
            driver_path = ChromeDriverManager().install()
        except Exception as e:
            print(f"Ошибка установки ChromeDriver: {e}")
            return None
    
    # Настройка опций Chrome
    options = Options()
    if system in ["linux", "redos"]:
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
    
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Для старых версий Chrome добавляем дополнительные опции
    if chrome_version and int(chrome_version.split('.')[0]) < 70:
        print("Добавляем опции для совместимости с устаревшей версией Chrome")
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')  # Может быть нужно для старых версий
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Установка драйвера с сервисом
    service = Service(driver_path)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        print("ChromeDriver успешно настроен")
        return driver
    except Exception as e:
        print(f"Ошибка создания экземпляра ChromeDriver: {e}")
        # Попробуем альтернативный способ для старых версий
        try:
            # Для очень старых версий Chrome может потребоваться другой подход
            driver = webdriver.Chrome(executable_path=driver_path, options=options)
            print("ChromeDriver успешно настроен (старый метод)")
            return driver
        except Exception as e2:
            print(f"Ошибка создания экземпляра ChromeDriver (старый метод): {e2}")
            # Попробуем с упрощенными опциями
            try:
                # Убираем опции, которые могут не поддерживаться в старых версиях
                simple_options = Options()
                if system in ["linux", "redos"]:
                    simple_options.add_argument('--no-sandbox')
                    simple_options.add_argument('--disable-dev-shm-usage')
                
                driver = webdriver.Chrome(executable_path=driver_path, options=simple_options)
                print("ChromeDriver успешно настроен (упрощенный метод)")
                return driver
            except Exception as e3:
                print(f"Ошибка создания экземпляра ChromeDriver (упрощенный метод): {e3}")
                return None


if __name__ == "__main__":
    driver = setup_chrome_driver()
    if driver:
        print("ChromeDriver успешно инициализирован")
        driver.quit()
    else:
        print("Не удалось инициализировать ChromeDriver")