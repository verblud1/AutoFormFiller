#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Manager for Family System Launcher
Обёртка над унифицированным модулем utils/statistics.py
"""

from utils.statistics import StatisticsManager as BaseStatisticsManager


class StatisticsManager(BaseStatisticsManager):
    """Менеджер статистики для лаунчера (наследует базовую функциональность).

    Наследует все методы из utils/statistics.py и добавляет
    специфичный для лаунчера вывод сообщений.
    """

    def update(self, success_count: int) -> bool:
        """Обновление статистики с выводом сообщения.

        Args:
            success_count: Количество успешно обработанных семей.

        Returns:
            True если обновление успешно, иначе False.
        """
        result = super().update(success_count)
        if result:
            print(f"📊 Статистика обновлена: +{success_count} семей")
        return result

    # Сохраняем обратную совместимость со старыми именами методов
    def load_statistics(self):
        """Загрузка статистики (алиас для load())."""
        return self.load()

    def save_statistics(self):
        """Сохранение статистики (алиас для save())."""
        return self.save()

    def update_statistics(self, success_count):
        """Обновление статистики (алиас для update())."""
        return self.update(success_count)

    def get_statistics_for_period(self):
        """Получение статистики за период (алиас для get_for_period())."""
        return self.get_for_period()