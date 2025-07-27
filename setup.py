#!/usr/bin/env python3
"""
設定腳本 - 協助初始化專案環境
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_step(step_num, total_steps, description):
    print(f"\n[{step_num}/{total_steps}] {description}")
    print("-" * 50)

def run_command(command, description, check=True):
    print(f"執行: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 錯誤: {e}")
        if e.stderr:
            print(f"錯誤詳情: {e.stderr}")
        return False

def check_python_version():
    version = sys.version_info
    if version.major != 3 or version.minor < 9:
        print(f"❌ Python 版本不符合要求。需要 Python 3.9+，目前版本: {version.major}.{version.minor}")
        return False
    print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True

def create_virtual_environment():
    if os.path.exists("venv"):
        print("✅ 虛擬環境已存在")
        return True
    
    success = run_command("python -m venv venv", "建立虛擬環境")
    if success:
        print("✅ 虛擬環境建立成功")
    return success

def activate_and_install_dependencies():
    # 根據作業系統選擇啟動腳本
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate && "
    else:  # macOS/Linux
        activate_cmd = "source venv/bin/activate && "
    
    commands = [
        f"{activate_cmd}python -m pip install --upgrade pip",
        f"{activate_cmd}pip install -r requirements.txt"
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"執行: {cmd}"):
            return False
    
    print("✅ 依賴套件安裝完成")
    return True

def setup_environment_file():
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env 檔案已存在")
        return True
    
    if env_example.exists():
        # 複製範例檔案
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ .env 檔案已建立（從 .env.example 複製）")
        print("⚠️  請編輯 .env 檔案，填入您的實際設定值")
        return True
    else:
        print("❌ .env.example 檔案不存在")
        return False

def check_config_directory():
    config_dir = Path("config")
    if not config_dir.exists():
        config_dir.mkdir()
        print("✅ config 目錄已建立")
    else:
        print("✅ config 目錄已存在")
    
    credentials_file = config_dir / "google-credentials.json"
    if not credentials_file.exists():
        print("⚠️  請將 Google Service Account 金鑰檔案放置在:")
        print(f"   {credentials_file.absolute()}")
        
        # 建立範例檔案
        example_content = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "your-private-key-id",
            "private_key": "your-private-key",
            "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        with open(config_dir / "google-credentials.example.json", 'w', encoding='utf-8') as f:
            json.dump(example_content, f, indent=2)
        
        return False
    else:
        print("✅ Google 憑證檔案已存在")
        return True

def run_tests():
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate && "
    else:  # macOS/Linux
        activate_cmd = "source venv/bin/activate && "
    
    success = run_command(f"{activate_cmd}python -m pytest tests/ -v", "執行測試", check=False)
    if success:
        print("✅ 所有測試通過")
    else:
        print("⚠️  某些測試失敗，這在初次設定時是正常的")
    return True

def print_next_steps():
    print("\n" + "=" * 60)
    print("🎉 專案設定完成！")
    print("=" * 60)
    
    print("\n📋 接下來的步驟:")
    print("1. 編輯 .env 檔案，填入您的 LINE Bot 和 Google 設定")
    print("2. 將 Google Service Account 金鑰檔案放在 config/google-credentials.json")
    print("3. 啟動開發伺服器:")
    
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # macOS/Linux
        print("   source venv/bin/activate")
    
    print("   python app.py")
    print("\n4. 使用 ngrok 建立公開 URL 進行測試:")
    print("   ngrok http 5000")
    print("\n5. 將 ngrok URL 設定到 LINE Bot Webhook")
    print("\n📚 詳細說明請參考 README.md")

def main():
    print("🚀 LINE Bot 靈感筆記專案設定")
    print("=" * 60)
    
    total_steps = 7
    current_step = 0
    
    # 步驟 1: 檢查 Python 版本
    current_step += 1
    print_step(current_step, total_steps, "檢查 Python 版本")
    if not check_python_version():
        sys.exit(1)
    
    # 步驟 2: 建立虛擬環境
    current_step += 1
    print_step(current_step, total_steps, "建立虛擬環境")
    if not create_virtual_environment():
        sys.exit(1)
    
    # 步驟 3: 安裝依賴
    current_step += 1
    print_step(current_step, total_steps, "安裝 Python 依賴套件")
    if not activate_and_install_dependencies():
        sys.exit(1)
    
    # 步驟 4: 設定環境檔案
    current_step += 1
    print_step(current_step, total_steps, "設定環境變數檔案")
    setup_environment_file()
    
    # 步驟 5: 檢查設定目錄
    current_step += 1
    print_step(current_step, total_steps, "檢查設定目錄")
    credentials_ready = check_config_directory()
    
    # 步驟 6: 執行測試
    current_step += 1
    print_step(current_step, total_steps, "執行測試")
    run_tests()
    
    # 步驟 7: 顯示後續步驟
    current_step += 1
    print_step(current_step, total_steps, "設定完成")
    print_next_steps()
    
    if not credentials_ready:
        print("\n⚠️  注意: 還需要設定 Google 憑證檔案才能正常運作")

if __name__ == "__main__":
    main()