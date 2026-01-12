#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installer component for Family System Launcher
Handles installation, uninstallation and system management
"""

import os
import sys
import platform
import shutil
import subprocess
from datetime import datetime


class Installer:
    def __init__(self, system_dir, desktop_path):
        self.system_dir = system_dir
        self.desktop_path = desktop_path
        # We'll install the whole modules rather than individual files
        self.files_to_copy = [
            "database_client.sh",
            "database_client.bat",
            "config.env",
            "family_system_launcher.py"  # This file
        ]

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

    def install_system(self, log_callback=None):
        """Install the system to desktop"""
        try:
            # Create system folder
            os.makedirs(self.system_dir, exist_ok=True)
            if log_callback:
                log_callback(f"📁 Создана папка: {self.system_dir}")
            
            # Copy files
            script_dir = os.path.dirname(os.path.abspath(__file__))
            copied_files = 0
            
            for filename in self.files_to_copy:
                src_path = os.path.join(script_dir, "..", filename)  # Go up one level to find files
                dst_path = os.path.join(self.system_dir, filename)
                
                if os.path.exists(src_path):
                    try:
                        shutil.copy2(src_path, dst_path)
                        copied_files += 1
                        if log_callback:
                            log_callback(f"📄 Скопирован: {filename}")
                    except Exception as e:
                        if log_callback:
                            log_callback(f"❌ Ошибка копирования {filename}: {e}")
                else:
                    if log_callback:
                        log_callback(f"⚠️ Файл не найден: {filename}")
            
            # Also copy the family_creator and mass_processor directories
            import sys
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up two levels to project root
            
            # Copy family_creator module
            src_family_creator = os.path.join(current_dir, "family_creator")
            dst_family_creator = os.path.join(self.system_dir, "family_creator")
            if os.path.exists(src_family_creator):
                if os.path.exists(dst_family_creator):
                    shutil.rmtree(dst_family_creator)  # Remove old version
                shutil.copytree(src_family_creator, dst_family_creator)
                if log_callback:
                    log_callback("📁 Скопирован модуль family_creator")
                copied_files += 1
            
            # Copy mass_processor module
            src_mass_processor = os.path.join(current_dir, "mass_processor")
            dst_mass_processor = os.path.join(self.system_dir, "mass_processor")
            if os.path.exists(src_mass_processor):
                if os.path.exists(dst_mass_processor):
                    shutil.rmtree(dst_mass_processor)  # Remove old version
                shutil.copytree(src_mass_processor, dst_mass_processor)
                if log_callback:
                    log_callback("📁 Скопирован модуль mass_processor")
                copied_files += 1
            
            # Create config file if it doesn't exist
            config_file = os.path.join(self.system_dir, "config.env")
            if not os.path.exists(config_file):
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write("""# Database connection configuration
# FILL THESE SETTINGS BEFORE RUNNING

SSH_HOST="192.168.10.59"
SSH_USER="sshuser"
SSH_PASSWORD="orsd321"
LOCAL_PORT="8080"
REMOTE_HOST="172.30.1.18"
REMOTE_PORT="80"
WEB_PATH="/aspnetkp/common/FindInfo.aspx"
""")
                if log_callback:
                    log_callback("⚙️ Created config.env configuration file")
            
            # Make scripts executable (for Linux)
            if platform.system() in ["Linux", "RedOS"]:
                for script in ["database_client.sh"]:
                    script_path = os.path.join(self.system_dir, script)
                    if os.path.exists(script_path):
                        os.chmod(script_path, 0o755)
                        if log_callback:
                            log_callback(f"🔧 Made executable: {script}")
            
            # Create shortcut (Windows only)
            if platform.system() == "Windows":
                self.create_windows_shortcut(log_callback)
            
            # Create .desktop file (Linux/RedOS)
            elif platform.system() in ["Linux", "RedOS"]:
                self.create_linux_desktop_file(log_callback)
            
            if log_callback:
                log_callback(f"✅ Installation completed! Files copied: {copied_files}")
            
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Installation error: {str(e)}")
            return False

    def create_windows_shortcut(self, log_callback=None):
        """Create desktop shortcut on Windows"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            # Create shortcut on desktop
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Система работы с семьями.lnk")
            
            target = sys.executable
            arguments = os.path.join(self.system_dir, "family_system_launcher.py")
            working_dir = self.system_dir
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.Arguments = f'"{arguments}"'
            shortcut.WorkingDirectory = working_dir
            shortcut.IconLocation = target  # Use Python icon
            shortcut.save()
            
            if log_callback:
                log_callback("🖱️ Created Windows desktop shortcut")
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Could not create Windows shortcut: {e}")
            return False

    def create_linux_desktop_file(self, log_callback=None):
        """Create .desktop file for Linux/RedOS"""
        try:
            desktop_file = os.path.join(self.desktop_path, "family_system.desktop")
            
            with open(desktop_file, 'w', encoding='utf-8') as f:
                f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Система работы с семьями
Comment=Запуск всех компонентов системы обработки семей
Exec=python3 {os.path.join(self.system_dir, 'family_system_launcher.py')}
Path={self.system_dir}
Icon=system-run
Terminal=false
Categories=Utility;Office;
StartupNotify=true
""")
            
            os.chmod(desktop_file, 0o755)
            if log_callback:
                log_callback("🖱️ Created .desktop file on desktop")
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Could not create .desktop file: {e}")
            return False

    def update_system(self, log_callback=None):
        """Update the system"""
        try:
            if log_callback:
                log_callback("🔄 Starting system update...")
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Create config backup
            config_file = os.path.join(self.system_dir, "config.env")
            backup_file = os.path.join(self.system_dir, "config.env.backup")
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_file)
                if log_callback:
                    log_callback("📋 Created configuration backup")
            
            # Copy files with replacement
            for filename in self.files_to_copy:
                src_path = os.path.join(script_dir, "..", filename)  # Go up one level to find files
                dst_path = os.path.join(self.system_dir, filename)
                
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)
                    if log_callback:
                        log_callback(f"📄 Updated: {filename}")
            
            # Also update the family_creator and mass_processor directories
            import sys
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up two levels to project root
            
            # Update family_creator module
            src_family_creator = os.path.join(current_dir, "family_creator")
            dst_family_creator = os.path.join(self.system_dir, "family_creator")
            if os.path.exists(src_family_creator):
                if os.path.exists(dst_family_creator):
                    shutil.rmtree(dst_family_creator)  # Remove old version
                shutil.copytree(src_family_creator, dst_family_creator)
                if log_callback:
                    log_callback("📁 Обновлен модуль family_creator")
            
            # Update mass_processor module
            src_mass_processor = os.path.join(current_dir, "mass_processor")
            dst_mass_processor = os.path.join(self.system_dir, "mass_processor")
            if os.path.exists(src_mass_processor):
                if os.path.exists(dst_mass_processor):
                    shutil.rmtree(dst_mass_processor)  # Remove old version
                shutil.copytree(src_mass_processor, dst_mass_processor)
                if log_callback:
                    log_callback("📁 Обновлен модуль mass_processor")
            
            # Restore config from backup
            if os.path.exists(backup_file):
                shutil.move(backup_file, config_file)
                if log_callback:
                    log_callback("⚙️ Restored configuration from backup")
            
            if log_callback:
                log_callback("✅ Update completed")
            
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Update error: {str(e)}")
            return False

    def uninstall_system(self, log_callback=None):
        """Uninstall the system"""
        try:
            # Remove system folder
            if os.path.exists(self.system_dir):
                shutil.rmtree(self.system_dir)
                if log_callback:
                    log_callback(f"🗑️ Removed folder: {self.system_dir}")
            
            # Remove shortcuts
            if platform.system() == "Windows":
                try:
                    import winshell
                    desktop = winshell.desktop()
                    shortcut = os.path.join(desktop, "Система работы с семьями.lnk")
                    if os.path.exists(shortcut):
                        os.remove(shortcut)
                        if log_callback:
                            log_callback("🗑️ Removed Windows shortcut")
                except:
                    pass
            
            elif platform.system() in ["Linux", "RedOS"]:
                desktop_files = [
                    os.path.join(self.desktop_path, "family_system.desktop"),
                    os.path.join(self.desktop_path, "Система_работы_с_семьями.desktop")
                ]
                
                for desktop_file in desktop_files:
                    if os.path.exists(desktop_file):
                        os.remove(desktop_file)
                        if log_callback:
                            log_callback(f"🗑️ Removed .desktop file: {os.path.basename(desktop_file)}")
            
            if log_callback:
                log_callback("✅ System removed")
            
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Uninstall error: {str(e)}")
            return False

    def open_system_folder(self, log_callback=None):
        """Open system folder"""
        try:
            if os.path.exists(self.system_dir):
                if platform.system() == "Windows":
                    os.startfile(self.system_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", self.system_dir])
                else:  # Linux/RedOS
                    subprocess.Popen(["xdg-open", self.system_dir])
                if log_callback:
                    log_callback("📁 System folder opened")
            else:
                if log_callback:
                    log_callback("⚠️ System folder not found")
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Could not open folder: {e}")