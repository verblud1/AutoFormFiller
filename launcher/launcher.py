#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЕДИНАЯ ТОЧКА ВХОДА - СИСТЕМА РАБОТЫ С СЕМЬЯМИ
Main launcher that integrates all components
Портативный режим - без установки
"""

import os
import sys
from datetime import datetime, timedelta

from .gui_components import LauncherGUI
from .statistics_manager import StatisticsManager
from .github_manager import GitHubManager
from .component_launcher import ComponentLauncher

# Импортируем функцию экспорта матерей
from utils.mothers_exporter import select_and_export_mothers


class FamilySystemLauncher:
    def __init__(self):
        # Initialize paths - portable mode uses application directory
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.system_dir = self.app_dir  # In portable mode, system dir is the app directory
        
        # Setup config directory
        self.setup_config_directory()
        
        # Initialize components
        self.statistics_manager = StatisticsManager(self.config_dir)
        self.github_manager = GitHubManager(self.system_dir, self.log_message, self.update_progress_callback)
        self.component_launcher = ComponentLauncher(self.system_dir, self.log_message)
        
        # Initialize GUI
        self.gui = LauncherGUI(self)
        
        # In portable mode, system is always "installed"
        self.is_installed = True
        
        # Set callbacks for GUI
        self.gui.log_callback = self.log_message
        
        # Update statistics display after initialization
        self.gui.app.after(200, self.update_statistics_display)
        
        # Periodic statistics update (every 30 seconds) - using tracked scheduling
        self.gui.schedule_periodic_update(self.update_statistics_display, 30000)

    def setup_config_directory(self):
        """Create configuration folder"""
        try:
            # Determine application directory path
            app_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir = os.path.join(app_dir, "config")
            
            # Create config folder if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                print(f"[OK] Created config directory: {self.config_dir}")
            
            # Create logs subfolder
            self.logs_dir = os.path.join(self.config_dir, "logs")
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
                print(f"[OK] Created logs directory: {self.logs_dir}")
                
            # Create screenshots subfolder
            self.screenshots_dir = os.path.join(self.config_dir, "screenshots")
            if not os.path.exists(self.screenshots_dir):
                os.makedirs(self.screenshots_dir)
                print(f"[OK] Created screenshots directory: {self.screenshots_dir}")
                
        except Exception as e:
            print(f"[ERROR] Error creating config directory: {e}")
            # If we can't create config folder, use current directory
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
            self.logs_dir = self.config_dir
            self.screenshots_dir = self.config_dir

    def check_installation_status(self):
        """Check installation status in portable mode (always installed)"""
        self.is_installed = True
        
        self.gui.update_status_label(
            f"✅ Портативный режим: {self.app_dir}",
            "green"
        )
        
        # Check availability of components
        self.check_components()
        
        # Update statistics
        self.update_statistics_display()
    
    def check_components(self):
        """Check for system components"""
        missing = []
        
        # Check for module directories instead of individual files
        modules = ["family_creator", "mass_processor"]
        for module in modules:
            module_path = os.path.join(self.system_dir, module)
            if not os.path.exists(module_path):
                missing.append(module)
        
        # Check OS-specific files
        if sys.platform == "win32":
            windows_files = ["database_client.bat"]
            for file in windows_files:
                file_path = os.path.join(self.system_dir, file)
                if not os.path.exists(file_path):
                    missing.append(file)
        else:  # Linux/RedOS
            linux_files = ["database_client.sh"]
            for file in linux_files:
                file_path = os.path.join(self.system_dir, file)
                if not os.path.exists(file_path):
                    missing.append(file)
        
        if missing:
            self.log_message(f"[WARN] Отсутствуют компоненты: {', '.join(missing)}")
            # Allow using components even if database files are missing
            self.gui.btn_json.configure(state="normal")
            self.gui.btn_mass.configure(state="normal")
            # Enable database button only if file exists
            if sys.platform == "win32":
                if os.path.exists(os.path.join(self.system_dir, "database_client.bat")):
                    self.gui.btn_db.configure(state="normal")
                else:
                    self.gui.btn_db.configure(state="disabled")
            else:
                if os.path.exists(os.path.join(self.system_dir, "database_client.sh")):
                    self.gui.btn_db.configure(state="normal")
                else:
                    self.gui.btn_db.configure(state="disabled")
        else:
            self.gui.btn_json.configure(state="normal")
            self.gui.btn_mass.configure(state="normal")
            self.gui.btn_db.configure(state="normal")
            self.log_message("[OK] Все компоненты системы доступны")
    
    def launch_json_creator(self):
        """Launch JSON creator"""
        self.component_launcher.launch_json_creator()
    
    def launch_mass_processor(self):
        """Launch mass processor"""
        self.component_launcher.launch_mass_processor()
    
    def launch_database(self):
        """Launch database client"""
        self.component_launcher.launch_database()
    
    def open_system_folder(self):
        """Open system folder"""
        self.component_launcher.open_system_folder()
    
    def update_from_github(self):
        """Update from GitHub"""
        self.github_manager.update_from_github()
    
    def increment_success_count(self, count=1):
        """Increment success counter"""
        try:
            # Update statistics
            self.statistics_manager.update_statistics(count)
        except Exception as e:
            print(f"[WARN] Error updating statistics: {e}")
    
    def get_statistics_for_period(self):
        """Get statistics for the period"""
        return self.statistics_manager.get_statistics_for_period()
    
    def update_statistics_display(self):
        """Update statistics display"""
        self.gui.update_statistics_display()
    
    def periodic_statistics_update(self):
        """Periodic statistics update (now handled by schedule_periodic_update)"""
        try:
            # Update statistics only - scheduling is handled by schedule_periodic_update
            self.update_statistics_display()
        except Exception as e:
            print(f"[WARN] Error in periodic statistics update: {e}")
    
    def log_message(self, message):
        """Log message"""
        self.gui.log_message(message)
    
    def update_progress_callback(self, visible, progress, details=""):
        """Callback for GitHub update progress"""
        try:
            if visible:
                self.gui.set_progress_visible(True)
            self.gui.update_progress(progress, 100, details)
        except Exception as e:
            print(f"[WARN] Progress update error: {e}")
    
    def run(self):
        """Run the application"""
        # In portable mode, check components immediately
        self.check_installation_status()
        self.gui.run()

    def export_mothers_to_txt(self):
        """Экспорт ФИО матерей в текстовый файл"""
        try:
            # Вызываем функцию экспорта матерей
            select_and_export_mothers()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Ошибка при экспорте матерей в текстовый файл:\n{str(e)}")
            print(f"❌ Ошибка экспорта матерей в текстовый файл: {e}")

if __name__ == "__main__":
    launcher = FamilySystemLauncher()
    launcher.run()
