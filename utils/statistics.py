"""Унифицированный модуль статистики для проекта AutoFormFiller.

Предоставляет единый интерфейс для работы со статистикой обработки семей.
Структура данных: {'daily': {}, 'weekly': {}}
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple


def load_statistics(stats_file: str) -> Dict:
    """Загрузка статистики обработки из файла.

    Args:
        stats_file: Путь к файлу статистики.

    Returns:
        Словарь с структурой {'daily': {}, 'weekly': {}}.
    """
    try:
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)

                # Проверяем структуру файла
                if not isinstance(stats, dict):
                    stats = {}

                # Проверяем наличие необходимых полей
                if 'daily' not in stats:
                    stats['daily'] = {}
                if 'weekly' not in stats:
                    stats['weekly'] = {}

                return stats
        return {'daily': {}, 'weekly': {}}
    except Exception as e:
        print(f"⚠️ Ошибка загрузки статистики: {e}")
        return {'daily': {}, 'weekly': {}}


def save_statistics(stats_file: str, stats: Dict) -> bool:
    """Сохранение статистики обработки в файл.

    Args:
        stats_file: Путь к файлу статистики.
        stats: Словарь со статистикой.

    Returns:
        True если сохранение успешно, иначе False.
    """
    try:
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения статистики: {e}")
        return False


def update_statistics(stats: Dict, success_count: int) -> bool:
    """Обновление статистики обработки.

    Args:
        stats: Словарь со статистикой (будет изменён in-place).
        success_count: Количество успешно обработанных семей.

    Returns:
        True если обновление успешно, иначе False.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        # Обновляем дневную статистику
        if today in stats['daily']:
            stats['daily'][today] += success_count
        else:
            stats['daily'][today] = success_count

        # Обновляем недельную статистику
        week_num = datetime.now().strftime("%Y-W%W")
        if week_num in stats['weekly']:
            stats['weekly'][week_num] += success_count
        else:
            stats['weekly'][week_num] = success_count

        return True
    except Exception as e:
        print(f"⚠️ Ошибка обновления статистики: {e}")
        return False


def get_statistics_for_period(stats: Dict) -> Tuple[int, int]:
    """Получение статистики за день и неделю.

    Args:
        stats: Словарь со статистикой.

    Returns:
        Кортеж (today_stat, week_stat) - статистика за сегодня и за неделю.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        today_stat = stats['daily'].get(today, 0)

        # Получаем статистику за текущую неделю (понедельник-пятница)
        week_stat = 0
        current_date = datetime.now()

        # Находим понедельник текущей недели
        start_of_week = current_date - timedelta(days=current_date.weekday())

        # Для каждого дня недели с понедельника по пятницу (0-4)
        for i in range(5):
            day_date = start_of_week + timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            week_stat += stats['daily'].get(day_str, 0)

        return today_stat, week_stat
    except Exception as e:
        print(f"⚠️ Ошибка получения статистики: {e}")
        return 0, 0


class StatisticsManager:
    """Класс-обёртка для удобной работы со статистикой.

    Предоставляет объектно-ориентированный интерфейс для управления статистикой.
    """

    def __init__(self, config_dir: str):
        """
        Инициализация менеджера статистики.

        Args:
            config_dir: Директория для хранения файлов конфигурации.
        """
        self.config_dir = config_dir
        self.stats_file = os.path.join(self.config_dir, "processing_statistics.json")
        self.stats = load_statistics(self.stats_file)

    def load(self) -> Dict:
        """Загрузка статистики из файла.

        Returns:
            Словарь со статистикой.
        """
        self.stats = load_statistics(self.stats_file)
        return self.stats

    def save(self) -> bool:
        """Сохранение статистики в файл.

        Returns:
            True если сохранение успешно, иначе False.
        """
        return save_statistics(self.stats_file, self.stats)

    def update(self, success_count: int) -> bool:
        """Обновление статистики.

        Args:
            success_count: Количество успешно обработанных семей.

        Returns:
            True если обновление успешно, иначе False.
        """
        result = update_statistics(self.stats, success_count)
        if result:
            self.save()
        return result

    def get_for_period(self) -> Tuple[int, int]:
        """Получение статистики за день и неделю.

        Returns:
            Кортеж (today_stat, week_stat).
        """
        return get_statistics_for_period(self.stats)