#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Components for Family System Launcher
Contains all UI-related classes and methods
Портативный режим - без кнопок установки/удаления
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LauncherGUI:
    def __init__(self, launcher_instance):
        self.launcher = launcher_instance
        self.app = ctk.CTk()
        self.app.title("Система работы с семьями")
        self.app.geometry("800x600")
        self.app.resizable(False, False)
        
        # Track after() callbacks to cancel them on close
        self.after_ids = []
        
        # Center window
        self.center_window()
        
        self.setup_ui()
        
        # Handle window close event
        self.app.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Centers the window on screen"""
        self.app.update_idletasks()
        width = self.app.winfo_width()
        height = self.app.winfo_height()
        x = (self.app.winfo_screenwidth() // 2) - (width // 2)
        y = (self.app.winfo_screenheight() // 2) - (height // 2)
        self.app.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Sets up the user interface"""
        # Main container
        main_frame = ctk.CTkFrame(self.app)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="СИСТЕМА РАБОТЫ С СЕМЬЯМИ",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack()
        
        ctk.CTkLabel(
            title_frame,
            text="Портативный режим | Автоматическое заполнение форм",
            font=ctk.CTkFont(size=14)
        ).pack()
        
        # System info
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(
            info_frame,
            text="Статус: проверка...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Statistics display
        self.stat_label = ctk.CTkLabel(
            info_frame,
            text="📊 Статистика: Сегодня - 0 | Неделя - 0",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.stat_label.pack(pady=5)
        
        # Progress bar for updates
        self.progress_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=10, pady=5)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.progress_label.pack(anchor="w", pady=(0, 3))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=300,
            mode='determinate'
        )
        self.progress_bar.pack(fill="x", pady=3)
        self.progress_bar.set(0)
        
        self.progress_details = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.progress_details.pack(anchor="w", pady=(3, 0))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Button 1: JSON Creator
        self.btn_json = ctk.CTkButton(
            buttons_frame,
            text="ВНЕСТИ СЕМЬИ В JSON",
            command=self.launcher.launch_json_creator,
            height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#2B7A78",
            hover_color="#175A58"
        )
        self.btn_json.pack(fill="x", pady=10)
        
        # Button 2: Mass Processor
        self.btn_mass = ctk.CTkButton(
            buttons_frame,
            text="ЗАПОЛНИТЬ В БАЗУ",
            command=self.launcher.launch_mass_processor,
            height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#3A506B",
            hover_color="#2A406B"
        )
        self.btn_mass.pack(fill="x", pady=10)
        
        # Button 3: Database
        self.btn_db = ctk.CTkButton(
            buttons_frame,
            text="ЗАПУСТИТЬ БАЗУ ДАННЫХ",
            command=self.launcher.launch_database,
            height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#5E4AE3",
            hover_color="#4A3AD3"
        )
        self.btn_db.pack(fill="x", pady=10)
        
        # GitHub update button
        self.btn_github = ctk.CTkButton(
            buttons_frame,
            text="ОБНОВИТЬ ЧЕРЕЗ GITHUB",
            command=self.launcher.update_from_github,
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#6f42c1",
            hover_color="#5a32a3"
        )
        self.btn_github.pack(fill="x", pady=10)
        
        # Bottom management panel - only open folder button
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=(20, 0))
        
        # Only show "Open System Folder" button
        manage_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        manage_frame.pack(fill="x", pady=5)
        
        self.btn_open_folder = ctk.CTkButton(
            manage_frame,
            text="ОТКРЫТЬ ПАПКУ СИСТЕМЫ",
            command=self.launcher.open_system_folder,
            width=200,
            fg_color="#6C757D",
            hover_color="#5A6268"
        )
        self.btn_open_folder.pack(side="left", padx=5)
        
        # Log
        log_frame = ctk.CTkFrame(main_frame, height=120)
        log_frame.pack(fill="x", padx=10, pady=(20, 10))
        
        ctk.CTkLabel(
            log_frame,
            text="Лог действий:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=5,
            width=70,
            bg="#2B2B2B",
            fg="white",
            font=("Courier", 10)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.log_text.config(state="disabled")
    
    def update_statistics_display(self):
        """Update statistics display in the interface"""
        try:
            today_stat, week_stat = self.launcher.get_statistics_for_period()
            self.stat_label.configure(
                text=f"📊 Статистика: Сегодня - {today_stat} | Неделя - {week_stat}"
            )
        except Exception as e:
            print(f"⚠️ Ошибка обновления отображения статистики: {e}")
    
    def log_message(self, message):
        """Add message to the log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state="normal")
        self.log_text.insert("end", log_entry)
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        
        self.app.update_idletasks()
        print(log_entry.strip())
    
    def update_status_label(self, text, color=None):
        """Update the status label text and color"""
        self.status_label.configure(text=text)
        if color:
            self.status_label.configure(text_color=color)
    
    def run(self):
        """Run the GUI application"""
        self.app.mainloop()
    
    def on_closing(self):
        """Handle window closing - cancel all after() callbacks"""
        # Cancel all scheduled after() callbacks
        for after_id in self.after_ids:
            try:
                self.app.after_cancel(after_id)
            except:
                pass
        self.after_ids.clear()
        
        # Destroy the window
        self.app.destroy()
    
    def schedule_periodic_update(self, callback, interval_ms):
        """Schedule periodic callback and track its ID"""
        def wrapped_callback():
            callback()
            # Reschedule if app is still running
            if self.app.winfo_exists():
                new_id = self.app.after(interval_ms, wrapped_callback)
                self.after_ids.append(new_id)
        
        first_id = self.app.after(interval_ms, wrapped_callback)
        self.after_ids.append(first_id)
    
    def set_progress_visible(self, visible=True):
        """Show or hide progress bar"""
        if visible:
            self.progress_frame.pack(fill="x", padx=10, pady=5)
        else:
            self.progress_frame.pack_forget()
    
    def update_progress(self, current, total, details=""):
        """Update progress bar"""
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"Прогресс: {current}/{total} ({int(progress*100)}%)")
        else:
            self.progress_bar.set(0)
            self.progress_label.configure(text="")
        
        if details:
            self.progress_details.configure(text=details)
    
    def reset_progress(self):
        """Reset progress bar"""
        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.progress_details.configure(text="")
