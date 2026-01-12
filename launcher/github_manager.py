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
    def __init__(self, system_dir, log_callback=None):
        self.system_dir = system_dir
        self.log_callback = log_callback
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
            
            # Create session with token if available
            session = requests.Session()
            if self.github_token:
                session.headers.update({"Authorization": f"token {self.github_token}"})
            
            # Repository URL
            repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
            
            # List of files to update (excluding configs)
            files_to_update = [
                "database_client.sh",
                "family_system_launcher.py"
            ]
            
            updated_files = 0
            skipped_files = 0
            error_files = 0
            
            for filename in files_to_update:
                try:
                    # Get file info from GitHub
                    file_url = f"{repo_url}/{filename}?ref={branch}"
                    response = session.get(file_url, timeout=10)
                    
                    if response.status_code == 403 and "rate limit" in response.text.lower():
                        if self.log_callback:
                            self.log_callback("⚠️ GitHub rate limit reached. Try later or use token.")
                        break
                    
                    if response.status_code != 200:
                        if self.log_callback:
                            self.log_callback(f"⚠️ File {filename} not found on GitHub")
                        continue
                    
                    file_info = response.json()
                    content_encoded = file_info.get("content", "")
                    sha_github = file_info.get("sha", "")
                    
                    # Decode content (base64)
                    import base64
                    content = base64.b64decode(content_encoded).decode('utf-8')
                    
                    # Local file path
                    local_path = os.path.join(self.system_dir, filename)
                    
                    # Check if local file exists
                    if os.path.exists(local_path):
                        # Read local file and compute hash
                        with open(local_path, 'r', encoding='utf-8') as f:
                            local_content = f.read()
                        
                        # Compare hashes
                        local_hash = hashlib.sha1(local_content.encode()).hexdigest()
                        
                        if local_hash == sha_github:
                            if self.log_callback:
                                self.log_callback(f"✓ {filename} is already up to date")
                            skipped_files += 1
                            continue
                    
                    # Create backup if file exists
                    if os.path.exists(local_path):
                        backup_path = local_path + ".backup"
                        import shutil
                        shutil.copy2(local_path, backup_path)
                    
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
                    time.sleep(0.5)
                    
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"❌ Error updating {filename}: {str(e)}")
                    error_files += 1
            
            # Update modules from GitHub as well
            try:
                import requests
                import zipfile
                import io
                
                # Get the latest repository content
                repo_content_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
                response = session.get(repo_content_url, params={"ref": branch})
                
                if response.status_code == 200:
                    contents = response.json()
                    
                    # Find and download module directories
                    for item in contents:
                        if item['type'] == 'dir' and item['name'] in ['family_creator', 'mass_processor']:
                            module_name = item['name']
                            self.log_callback(f"🔄 Updating module: {module_name}")
                            
                            # Download the entire directory as a zip
                            module_url = f"https://github.com/{repo_owner}/{repo_name}/archive/{branch}.zip"
                            
                            zip_response = session.get(module_url)
                            if zip_response.status_code == 200:
                                # Extract the specific module from the zip
                                with zipfile.ZipFile(io.BytesIO(zip_response.content)) as zip_file:
                                    # Find the correct folder path in the zip (it includes the repo name and branch)
                                    zip_contents = zip_file.namelist()
                                    
                                    # Extract only the specific module directory
                                    module_prefix = f"{repo_name}-{branch}/{module_name}/"
                                    
                                    # Create a temporary directory for extraction
                                    temp_extract_dir = os.path.join(self.system_dir, f"temp_{module_name}")
                                    
                                    # Extract the specific module
                                    for file_path in zip_contents:
                                        if file_path.startswith(module_prefix):
                                            # Calculate the destination path
                                            dest_path = file_path.replace(module_prefix, "")
                                            if dest_path:  # Skip the directory itself
                                                full_dest_path = os.path.join(temp_extract_dir, dest_path)
                                                
                                                # Create directory if needed
                                                os.makedirs(os.path.dirname(full_dest_path), exist_ok=True)
                                                
                                                # Extract file
                                                with zip_file.open(file_path) as source, open(full_dest_path, 'wb') as target:
                                                    target.write(source.read())
                                    
                                    # Remove old module if it exists
                                    old_module_path = os.path.join(self.system_dir, module_name)
                                    if os.path.exists(old_module_path):
                                        import shutil
                                        shutil.rmtree(old_module_path)
                                    
                                    # Move extracted module to final location
                                    final_module_path = os.path.join(self.system_dir, module_name)
                                    import shutil
                                    shutil.move(temp_extract_dir, final_module_path)
                                    
                                    self.log_callback(f"✅ Updated module: {module_name}")
                                    updated_files += 1
                            else:
                                self.log_callback(f"❌ Failed to download module: {module_name}")
                                error_files += 1
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"❌ Error updating modules: {str(e)}")
                error_files += 1
            
            # Update README if available
            self.update_readme_from_github(session, repo_url, branch)
            
            # Final report
            if updated_files > 0:
                if self.log_callback:
                    self.log_callback(f"\n✨ Update completed!")
                    self.log_callback(f"📊 Updated files: {updated_files}")
                    self.log_callback(f"📊 Skipped (up to date): {skipped_files}")
                    if error_files > 0:
                        self.log_callback(f"⚠️ With errors: {error_files}")
            else:
                if self.log_callback:
                    self.log_callback("ℹ️ All files are already up to date. No updates required.")
                
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Update error: {str(e)}")

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