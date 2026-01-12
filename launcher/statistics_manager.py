#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Manager for Family System Launcher
Handles processing statistics and tracking
"""

import json
import os
from datetime import datetime, timedelta

class StatisticsManager:
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.stats_file = os.path.join(self.config_dir, "processing_statistics.json")
        self.stats = self.load_statistics()
        
        # Initialize counters
        self.success_count = 0
        self.daily_stat = 0
        self.weekly_stat = 0

    def load_statistics(self):
        """Load processing statistics"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    
                    # Check structure of file
                    if not isinstance(stats, dict):
                        stats = {}
                    
                    # Check for required fields
                    if 'daily' not in stats:
                        stats['daily'] = {}
                    if 'weekly' not in stats:
                        stats['weekly'] = {}
                    
                    return stats
            return {'daily': {}, 'weekly': {}}
        except Exception as e:
            print(f"⚠️ Ошибка загрузки статистики: {e}")
            return {'daily': {}, 'weekly': {}}

    def save_statistics(self):
        """Save processing statistics"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения статистики: {e}")
            return False

    def update_statistics(self, success_count):
        """Update processing statistics"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Update daily statistics
            if today in self.stats['daily']:
                self.stats['daily'][today] += success_count
            else:
                self.stats['daily'][today] = success_count
            
            # Update weekly statistics
            # Get week number
            week_num = datetime.now().strftime("%Y-W%W")
            if week_num in self.stats['weekly']:
                self.stats['weekly'][week_num] += success_count
            else:
                self.stats['weekly'][week_num] = success_count
            
            # Save statistics
            self.save_statistics()
            
            print(f"📊 Статистика обновлена: +{success_count} семей")
            return True
        except Exception as e:
            print(f"⚠️ Ошибка обновления статистики: {e}")
            return False

    def get_statistics_for_period(self):
        """Get statistics for day and week"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            today_stat = self.stats['daily'].get(today, 0)
            
            # Get current week statistics (Monday-Friday)
            week_stat = 0
            current_date = datetime.now()
            
            # Find Monday of current week
            start_of_week = current_date - timedelta(days=current_date.weekday())
            
            # For each day of the week from Monday to Friday (0-4)
            for i in range(5):
                day_date = start_of_week + timedelta(days=i)
                day_str = day_date.strftime("%Y-%m-%d")
                week_stat += self.stats['daily'].get(day_str, 0)
            
            return today_stat, week_stat
        except Exception as e:
            print(f"⚠️ Ошибка получения статистики: {e}")
            return 0, 0