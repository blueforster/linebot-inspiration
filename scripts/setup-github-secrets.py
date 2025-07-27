#!/usr/bin/env python3
"""
GitHub Secrets 設定腳本
協助使用者安全地設定 GitHub Repository Secrets
"""

import os
import json
import base64
import getpass
import requests
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

class GitHubSecretsManager:
    def __init__(self, owner, repo, token):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_public_key(self):
        """取得 Repository 的公鑰"""
        url = f"{self.base_url}/actions/secrets/public-key"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"無法取得公鑰: {response.status_code} - {response.text}")
    
    def encrypt_secret(self, public_key, secret_value):
        """使用公鑰加密 secret 值"""
        public_key_bytes = base64.b64decode(public_key)
        
        # 載入公鑰
        public_key_obj = serialization.load_der_public_key(public_key_bytes)
        
        # 加密 secret
        encrypted = public_key_obj.encrypt(
            secret_value.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def create_or_update_secret(self, secret_name, secret_value):
        """建立或更新 Repository Secret"""
        # 取得公鑰
        public_key_data = self.get_public_key()
        
        # 加密 secret 值
        encrypted_value = self.encrypt_secret(public_key_data['key'], secret_value)
        
        # 建立 secret
        url = f"{self.base_url}/actions/secrets/{secret_name}"
        data = {
            "encrypted_value": encrypted_value,
            "key_id": public_key_data['key_id']
        }
        
        response = requests.put(url, headers=self.headers, json=data)
        
        if response.status_code in [201, 204]:
            print(f"✅ Secret '{secret_name}' 設定成功")
            return True
        else:
            print(f"❌ Secret '{secret_name}' 設定失敗: {response.status_code} - {response.text}")
            return False

def read_env_file():
    """讀取 .env 檔案"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env 檔案不存在")
        return {}
    
    env_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    return env_vars

def read_google_credentials():
    """讀取 Google 憑證檔案"""
    cred_file = Path('config/google-credentials.json')
    if not cred_file.exists():
        print("❌ Google 憑證檔案不存在")
        return None
    
    with open(cred_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_user_input():
    """取得使用者輸入"""
    print("🔧 GitHub Repository Secrets 設定工具")
    print("=" * 50)
    
    # GitHub 資訊
    owner = input("GitHub 使用者名稱或組織名稱: ").strip()
    repo = input("Repository 名稱: ").strip()
    
    print("\n📝 請建立 GitHub Personal Access Token:")
    print("1. 前往: https://github.com/settings/tokens")
    print("2. 點擊 'Generate new token (classic)'")
    print("3. 選擇 'repo' 權限")
    print("4. 複製產生的 token")
    print()
    
    token = getpass.getpass("GitHub Personal Access Token: ").strip()
    
    return owner, repo, token

def main():
    try:
        # 取得使用者輸入
        owner, repo, token = get_user_input()
        
        # 建立 GitHub Secrets Manager
        manager = GitHubSecretsManager(owner, repo, token)
        
        print(f"\n🔗 連接到 GitHub Repository: {owner}/{repo}")
        
        # 測試連線
        try:
            manager.get_public_key()
            print("✅ GitHub API 連線成功")
        except Exception as e:
            print(f"❌ GitHub API 連線失敗: {e}")
            return
        
        # 讀取環境變數
        print("\n📖 讀取環境變數...")
        env_vars = read_env_file()
        
        # 讀取 Google 憑證
        print("📖 讀取 Google 憑證...")
        google_creds = read_google_credentials()
        
        # 定義需要設定的 secrets
        secrets_to_set = {}
        
        # 從 .env 檔案取得的 secrets
        required_env_vars = [
            'LINE_CHANNEL_ACCESS_TOKEN',
            'LINE_CHANNEL_SECRET',
            'GOOGLE_SHEET_ID',
            'SECRET_KEY'
        ]
        
        for var in required_env_vars:
            if var in env_vars and env_vars[var]:
                secrets_to_set[var] = env_vars[var]
            else:
                print(f"⚠️  環境變數 {var} 未設定或為空")
        
        # Google 憑證 JSON
        if google_creds:
            secrets_to_set['GOOGLE_SERVICE_ACCOUNT_JSON'] = json.dumps(google_creds, separators=(',', ':'))
        else:
            print("⚠️  Google 憑證檔案未找到")
        
        # 可選的環境變數
        optional_vars = ['GOOGLE_CLOUD_PROJECT']
        for var in optional_vars:
            if var in env_vars and env_vars[var]:
                secrets_to_set[var] = env_vars[var]
        
        # 顯示將要設定的 secrets
        print(f"\n📋 將設定以下 Secrets:")
        for secret_name in secrets_to_set.keys():
            print(f"  • {secret_name}")
        
        # 確認設定
        print()
        confirm = input("是否繼續設定 GitHub Secrets? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 取消設定")
            return
        
        # 設定 secrets
        print("\n🔐 開始設定 GitHub Secrets...")
        success_count = 0
        
        for secret_name, secret_value in secrets_to_set.items():
            if manager.create_or_update_secret(secret_name, secret_value):
                success_count += 1
        
        # 結果報告
        print(f"\n📊 設定結果:")
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失敗: {len(secrets_to_set) - success_count}")
        
        if success_count == len(secrets_to_set):
            print("\n🎉 所有 GitHub Secrets 設定完成！")
            print("\n📝 接下來的步驟:")
            print("1. 推送程式碼到 GitHub Repository")
            print("2. GitHub Actions 會自動執行測試和部署")
            print("3. 檢查 Actions 分頁查看部署狀態")
        else:
            print("\n⚠️  部分 Secrets 設定失敗，請檢查錯誤訊息並重試")
    
    except KeyboardInterrupt:
        print("\n\n❌ 使用者中斷操作")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")

if __name__ == "__main__":
    # 檢查必要套件
    try:
        import requests
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
    except ImportError as e:
        print("❌ 缺少必要的 Python 套件")
        print("請執行: pip install requests cryptography")
        exit(1)
    
    main()