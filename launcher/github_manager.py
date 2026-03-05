#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Manager for Family System Launcher
Handles GitHub integration and updates
"""

import os
import sys
import platform
import threading
import subprocess
import hashlib
from datetime import datetime
import customtkinter as ctk


class GitHubManager:
    def __init__(self, system_dir, log_callback=None, progress_callback=None):
        self.system_dir = system_dir
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.github_token = None
        self.github_token_file = os.path.join(self.system_dir, ".github_token") if self.system_dir else None
        self.load_github_token()

    def load_github_token(self):
        """Load GitHub token from local file"""
        if self.github_token_file and os.path.exists(self.github_token_file):
            try:
                with open(self.github_token_file, 'r', encoding='utf-8') as f:
                    self.github_token = f.read().strip()
                    if self.github_token:
                        if self.log_callback:
                            self.log_callback("🔑 GitHub token loaded from local storage")
            except:
                self.github_token = None

    def save_github_token(self, token):
        """Save GitHub token to local file"""
        if not self.github_token_file:
            return False
        try:
            with open(self.github_token_file, 'w', encoding='utf-8') as f:
                f.write(token.strip())
            os.chmod(self.github_token_file, 0o600)  # Only for owner
            self.github_token = token.strip()
            if self.log_callback:
                self.log_callback("✅ GitHub token saved locally")
            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Error saving token: {e}")
            return False

    def ask_github_token(self):
        """Ask user for GitHub token"""
        dialog = ctk.CTkInputDialog(
            text="Введите GitHub Personal Access Token (необязательно):\n\n"
                "Без токена: 60 запросов в час\n"
                "С токеном: 5000 запросов в час\n\n"
                "Как получить токен:\n"
                "1. GitHub → Settings → Developer settings\n"
                "2. Personal access tokens → Tokens (classic)\n"
                "3. Выберите scopes: repo (все)\n\n"
                "Оставьте поле пустым для работы без токена:",
            title="GitHub Token"
        )
        token = dialog.get_input()
        
        if token and token.strip():
            if self.save_github_token(token):
                return True
        elif token == "":  # User explicitly pressed OK without token
            self.save_github_token("")  # Save empty token
            return True
        
        return False

    def update_from_github(self):
        """Update system files from GitHub repository"""
        try:
            # Check if system is installed
            if not os.path.exists(self.system_dir):
                if self.log_callback:
                    self.log_callback("❌ Система не установлена. Сначала установите систему!")
                return
            
            # Request token on first update
            if self.github_token is None:
                if not self.ask_github_token():
                    if self.log_callback:
                        self.log_callback("⚠️ Обновление отменено пользователем")
                    return
            
            if self.log_callback:
                self.log_callback("🔄 Проверяю обновления на GitHub...")
            
            # Run update in separate thread
            threading.Thread(target=self._github_update_thread, daemon=True).start()
            
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Error starting update: {str(e)}")

    def _github_update_thread(self):
        """Thread for GitHub update"""
        try:
            import requests
            
            repo_owner = "verblud1"
            repo_name = "AutoFormFiller"
            branch = "main"
            
            if self.log_callback:
                self.log_callback(f"📡 Connecting to repository: {repo_owner}/{repo_name}")
            
            # Show progress bar
            if self.progress_callback:
                self.progress_callback(True, 0, "Connecting to GitHub...")
            
            # Create session with token if available
            session = requests.Session()
            if self.github_token:
                session.headers.update({"Authorization": f"token {self.github_token}"})
            
            # Repository URL
            repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
            
            # Get all files from repository
            if self.log_callback:
                self.log_callback("🔄 Fetching repository file list...")
            
            if self.progress_callback:
                self.progress_callback(True, 5, "Fetching repository file list...")
            
            response = session.get(repo_url, params={"ref": branch}, timeout=10)
            
            if response.status_code == 403 and "rate limit" in response.text.lower():
                if self.log_callback:
                    self.log_callback("⚠️ GitHub rate limit reached. Try later or use token.")
                if self.progress_callback:
                    self.progress_callback(False, 0, "Rate limit reached")
                return
            
            if response.status_code != 200:
                if self.log_callback:
                    self.log_callback(f"❌ Failed to fetch repository contents: {response.status_code}")
                if self.progress_callback:
                    self.progress_callback(False, 0, "Failed to fetch repository")
                return
            
            contents = response.json()
            
            # Files to skip (configs, data, logs, etc.)
            skip_patterns = [
                '.git', '__pycache__', '.pyc', '.log', '.tmp', '.backup',
                'config/', 'logs/', 'screenshots/', 'files for fill queue/',
                'Installer/', 'documentation/', 'examples/', 'color_sorter/',
                'autoprint.py', 'autosave_families.json'
            ]
            
            updated_files = 0
            skipped_files = 0
            error_files = 0
            total_files = len([item for item in contents if item['type'] == 'file'])
            
            if self.log_callback:
                self.log_callback(f"📊 Found {total_files} files in repository")
            
            if self.progress_callback:
                self.progress_callback(True, 10, f"Found {total_files} files to process")
            
            # Process all files
            processed_files = 0
            for item in contents:
                if item['type'] != 'file':
                    continue
                    
                filename = item['path']
                
                # Skip unwanted files
                if any(pattern in filename for pattern in skip_patterns):
                    if self.log_callback:
                        self.log_callback(f"⏭️ Skipped: {filename}")
                    processed_files += 1
                    if self.progress_callback and total_files > 0:
                        progress = 10 + (processed_files / total_files) * 80
                        self.progress_callback(True, progress, f"Skipped: {filename}")
                    continue
                
                try:
                    if self.log_callback:
                        self.log_callback(f"🔄 Processing: {filename}")
                    
                    if self.progress_callback:
                        processed_files += 1
                        if total_files > 0:
                            progress = 10 + (processed_files / total_files) * 80
                            self.progress_callback(True, progress, f"Processing: {filename}")
                    
                    # Get file info from GitHub
                    file_url = f"{repo_url}/{filename}?ref={branch}"
                    response = session.get(file_url, timeout=10)
                    
                    if response.status_code != 200:
                        if self.log_callback:
                            self.log_callback(f"⚠️ Skipped {filename}: not found")
                        continue
                    
                    file_info = response.json()
                    content_encoded = file_info.get("content", "")
                    sha_github = file_info.get("sha", "")
                    
                    # Decode content (base64)
                    import base64
                    content = base64.b64decode(content_encoded).decode('utf-8')
                    
                    # Local file path
                    local_path = os.path.join(self.system_dir, filename)
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    
                    # Check if local file exists and compare content hash
                    need_update = True
                    if os.path.exists(local_path):
                        with open(local_path, 'r', encoding='utf-8') as f:
                            local_content = f.read()
                        
                        # Compute hash of local content
                        local_hash = hashlib.sha1(local_content.encode()).hexdigest()
                        
                        if local_hash == sha_github:
                            if self.log_callback:
                                self.log_callback(f"✓ {filename} is up to date")
                            skipped_files += 1
                            need_update = False
                    
                    if not need_update:
                        continue
                    
                    # Create backup if file exists
                    if os.path.exists(local_path):
                        backup_path = local_path + ".backup"
                        import shutil
                        shutil.copy2(local_path, backup_path)
                        if self.log_callback:
                            self.log_callback(f"📦 Backed up: {filename}")
                    
                    # Save new file
                    with open(local_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Make executable if needed
                    if filename.endswith(".sh"):
                        os.chmod(local_path, 0o755)
                    
                    if self.log_callback:
                        self.log_callback(f"✅ Updated: {filename}")
                    updated_files += 1
                    
                    # Small delay between requests
                    import time
                    time.sleep(0.3)
                    
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"❌ Error updating {filename}: {str(e)}")
                    error_files += 1
            
            # Update README if available
            if self.log_callback:
                self.log_callback("🔄 Updating README...")
            self.update_readme_from_github(session, repo_url, branch)
            
            # Final report
            if self.log_callback:
                self.log_callback("\n" + "="*50)
                self.log_callback("✨ UPDATE COMPLETED!")
                self.log_callback("="*50)
                self.log_callback(f"📊 Updated: {updated_files}")
                self.log_callback(f"✓ Up to date: {skipped_files}")
                if error_files > 0:
                    self.log_callback(f"⚠️ Errors: {error_files}")
                self.log_callback("="*50)
                
            if self.progress_callback:
                self.progress_callback(False, 100, "Update completed!")
                
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Update error: {str(e)}")
            if self.progress_callback:
                self.progress_callback(False, 0, f"Error: {str(e)}")

    def update_readme_from_github(self, session, repo_url, branch):
        """Update README file if there are changes"""
        try:
            readme_files = ["README.md", "README.txt", "readme.md"]
            
            for readme_file in readme_files:
                file_url = f"{repo_url}/{readme_file}?ref={branch}"
                response = session.get(file_url, timeout=5)
                
                if response.status_code == 200:
                    file_info = response.json()
                    content_encoded = file_info.get("content", "")
                    
                    import base64
                    content = base64.b64decode(content_encoded).decode('utf-8')
                    
                    local_path = os.path.join(self.system_dir, "README_GITHUB.txt")
                    with open(local_path, 'w', encoding='utf-8') as f:
                        f.write(f"# UPDATE FROM GITHUB\n\n")
                        f.write(f"Date: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                        f.write(f"Repo: https://github.com/verblud1/AutoFormFiller\n\n")
                        f.write(content)
                    
                    if self.log_callback:
                        self.log_callback(f"📄 Updated README_GITHUB.txt file")
                    break
                    
        except:
            pass  # Ignore README errors