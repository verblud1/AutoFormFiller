#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЕДИНАЯ ТОЧКА ВХОДА - СИСТЕМА РАБОТЫ С СЕМЬЯМИ
Main entry point that connects all system components
"""

import os
import sys
from Installer.launcher import FamilySystemLauncher


def main():
    """Main entry point for the application"""
    print("🚀 Запуск Системы работы с семьями...")
    
    # Create and run the launcher
    launcher = FamilySystemLauncher()
    launcher.run()


if __name__ == "__main__":
    main()