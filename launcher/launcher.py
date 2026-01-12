#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЕДИНАЯ ТОЧКА ВХОДА - СИСТЕМА РАБОТЫ С СЕМЬЯМИ
Main launcher that integrates all components
"""

import os
import sys
import platform
from datetime import datetime, timedelta

from .gui_components import LauncherGUI
from .statistics_manager import StatisticsManager
from .installer import Installer
from .github_manager import GitHubManager
from .component_launcher import ComponentLauncher


class FamilySystemLauncher:
    def __init__(self):
        # Initialize paths
        self.home_dir = os.path.expanduser("~")
        self.desktop_path = self.get_desktop_path()
        self.system_dir = os.path.join(self.desktop_path, "FamilySystem")
        
        # Setup config directory
        self.setup_config_directory()
        
        # Initialize components
        self.installer = Installer(self.system_dir, self.desktop_path)
        self.statistics_manager = StatisticsManager(self.config_dir)
        self.github_manager = GitHubManager(self.system_dir, self.log_message)
        self.component_launcher = ComponentLauncher(self.system_dir, self.log_message)
        
        # Initialize GUI
        self.gui = LauncherGUI(self)
        
        # Check installation status
        self.is_installed = os.path.exists(self.system_dir)
        
        # Set callbacks for GUI
        self.gui.log_callback = self.log_message
        
        # Update statistics display after initialization
        self.gui.app.after(200, self.update_statistics_display)
        
        # Periodic statistics update (every 30 seconds)
        self.gui.app.after(30000, self.periodic_statistics_update)

    def setup_config_directory(self):
        """Create configuration folder"""
        try:
            # Determine application directory path
            app_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_dir = os.path.join(app_dir, "config")
            
            # Create config folder if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                print(f"✅ Created config directory: {self.config_dir}")
            
            # Create logs subfolder
            self.logs_dir = os.path.join(self.config_dir, "logs")
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
                print(f"✅ Created logs directory: {self.logs_dir}")
                
            # Create screenshots subfolder
            self.screenshots_dir = os.path.join(self.config_dir, "screenshots")
            if not os.path.exists(self.screenshots_dir):
                os.makedirs(self.screenshots_dir)
                print(f"✅ Created screenshots directory: {self.screenshots_dir}")
                
        except Exception as e:
            print(f"❌ Error creating config directory: {e}")
            # If we can't create config folder, use current directory
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
            self.logs_dir = self.config_dir
            self.screenshots_dir = self.config_dir

    def get_desktop_path(self):
        """Determine desktop path for different OS"""
        home_dir = os.path.expanduser("~")
        system = platform.system()
        
        if system == "Windows":
            desktop = os.path.join(home_dir, "Desktop")
        elif system in ["Linux", "RedOS"]:
            # Try different options for Linux
            possible_paths = [
                os.path.join(home_dir, "Рабочий стол"),
                os.path.join(home_dir, "Desktop"),
                os.path.join(home_dir, "desktop"),
                os.path.join(home_dir, "Стол")
            ]
            
            desktop = home_dir + "/Desktop"  # Default
            
            for path in possible_paths:
                if os.path.exists(path):
                    desktop = path
                    break
            else:
                # If folder doesn't exist, create it
                desktop = os.path.join(home_dir, "Desktop")
                os.makedirs(desktop, exist_ok=True)
        else:
            desktop = os.path.join(home_dir, "Desktop")
        
        return desktop
    
    def check_installation_status(self):
        """Check installation status and update interface"""
        self.is_installed = os.path.exists(self.system_dir)
        
        if self.is_installed:
            self.gui.update_status_label(
                f"✅ Система установлена в: {self.system_dir}",
                "green"
            )
            self.gui.btn_install.configure(state="disabled", text="✅ УСТАНОВЛЕНА")
            self.gui.btn_update.configure(state="normal")
            self.gui.btn_uninstall.configure(state="normal")
            self.gui.btn_open_folder.configure(state="normal")
            
            # Check availability of components
            self.check_components()
            
            # Update statistics
            self.update_statistics_display()
        else:
            self.gui.update_status_label(
                "❌ Система не установлена. Нажмите 'Установить систему'",
                "red"
            )
            self.gui.btn_install.configure(state="normal", text="📦 УСТАНОВИТЬ СИСТЕМУ")
            self.gui.btn_update.configure(state="disabled")
            self.gui.btn_uninstall.configure(state="disabled")
            self.gui.btn_open_folder.configure(state="disabled")
            
            # Disable main buttons
            self.gui.btn_json.configure(state="disabled")
            self.gui.btn_mass.configure(state="disabled")
            self.gui.btn_db.configure(state="disabled")
    
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
        if platform.system() == "Windows":
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
            self.log_message(f"⚠️ Отсутствуют компоненты: {', '.join(missing)}")
            # Allow using components even if database files are missing
            self.gui.btn_json.configure(state="normal")
            self.gui.btn_mass.configure(state="normal")
            # Enable database button only if file exists
            if platform.system() == "Windows":
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
            self.log_message("✅ Все компоненты системы доступны")
    
    def install_system(self):
        """Install the system"""
        self.installer.install_system(self.log_message)
        self.check_installation_status()
    
    def update_system(self):
        """Update the system"""
        self.installer.update_system(self.log_message)
        self.check_components()
    
    def uninstall_system(self):
        """Uninstall the system"""
        self.installer.uninstall_system(self.log_message)
        self.check_installation_status()
    
    def open_system_folder(self):
        """Open system folder"""
        self.installer.open_system_folder(self.log_message)
    
    def launch_json_creator(self):
        """Launch JSON creator"""
        self.component_launcher.launch_json_creator()
    
    def launch_mass_processor(self):
        """Launch mass processor"""
        self.component_launcher.launch_mass_processor()
    
    def launch_database(self):
        """Launch database client"""
        self.component_launcher.launch_database()
    
    def update_from_github(self):
        """Update from GitHub"""
        self.github_manager.update_from_github()
    
    def increment_success_count(self, count=1):
        """Increment success counter"""
        try:
            # Update statistics
            self.statistics_manager.update_statistics(count)
        except Exception as e:
            print(f"⚠️ Error updating statistics: {e}")
    
    def get_statistics_for_period(self):
        """Get statistics for the period"""
        return self.statistics_manager.get_statistics_for_period()
    
    def update_statistics_display(self):
        """Update statistics display"""
        self.gui.update_statistics_display()
    
    def periodic_statistics_update(self):
        """Periodic statistics update"""
        try:
            # Update statistics
            self.update_statistics_display()
            
            # Schedule next update
            self.gui.app.after(30000, self.periodic_statistics_update)
        except Exception as e:
            print(f"⚠️ Error in periodic statistics update: {e}")
    
    def log_message(self, message):
        """Log message"""
        self.gui.log_message(message)
    
    def run(self):
        """Run the application"""
        # Check installation status after startup
        self.gui.app.after(100, self.check_installation_status)
        self.gui.run()


if __name__ == "__main__":
    launcher = FamilySystemLauncher()
    launcher.run()