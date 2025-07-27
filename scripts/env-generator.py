#!/usr/bin/env python3
"""
環境變數生成器
協助使用者生成 Zeabur 部署所需的環境變數
"""

import os
import json
import secrets
import base64
from pathlib import Path

def print_header():
    print("🔧 Zeabur 環境變數設定助手")
    print("=" * 50)
    print()

def generate_secret_key():
    """生成安全的 SECRET_KEY"""
    return secrets.token_urlsafe(32)

def read_google_credentials():
    """讀取 Google 憑證檔案"""
    cred_file = Path('config/google-credentials.json')
    if not cred_file.exists():
        print("❌ Google 憑證檔案不存在: config/google-credentials.json")
        print("請先完成 Google Service Account 設定")
        return None
    
    try:
        with open(cred_file, 'r', encoding='utf-8') as f:
            cred_data = json.load(f)
        
        # 驗證必要欄位
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in cred_data:
                print(f"❌ Google 憑證檔案缺少必要欄位: {field}")
                return None
        
        return cred_data
    except json.JSONDecodeError:
        print("❌ Google 憑證檔案格式錯誤")
        return None
    except Exception as e:
        print(f"❌ 讀取 Google 憑證檔案失敗: {e}")
        return None

def get_user_input():
    """取得使用者輸入的設定"""
    print("📝 請輸入以下設定資訊：")
    print()
    
    # LINE Bot 設定
    print("🤖 LINE Bot 設定")
    print("從 LINE Developers Console 取得：")
    line_token = input("LINE_CHANNEL_ACCESS_TOKEN: ").strip()
    line_secret = input("LINE_CHANNEL_SECRET: ").strip()
    print()
    
    # Google Sheets 設定
    print("📊 Google Sheets 設定")
    print("從 Google Sheets URL 中取得 ID：")
    sheets_id = input("GOOGLE_SHEET_ID: ").strip()
    print()
    
    # Google Cloud 專案（可選）
    print("☁️ Google Cloud 設定（可選，用於語音轉文字）")
    gcp_project = input("GOOGLE_CLOUD_PROJECT (可選): ").strip()
    print()
    
    return {
        'line_token': line_token,
        'line_secret': line_secret,
        'sheets_id': sheets_id,
        'gcp_project': gcp_project
    }

def validate_inputs(inputs, google_creds):
    """驗證輸入資料"""
    errors = []
    
    # 檢查必要欄位
    if not inputs['line_token']:
        errors.append("LINE_CHANNEL_ACCESS_TOKEN 不能為空")
    
    if not inputs['line_secret']:
        errors.append("LINE_CHANNEL_SECRET 不能為空")
    
    if not inputs['sheets_id']:
        errors.append("GOOGLE_SHEET_ID 不能為空")
    
    if not google_creds:
        errors.append("Google 憑證檔案未正確載入")
    
    # 檢查格式
    if inputs['line_token'] and not inputs['line_token'].startswith(('CHANNEL_ACCESS_TOKEN', '/')):
        # LINE Token 通常很長且包含特殊字元
        if len(inputs['line_token']) < 20:
            errors.append("LINE_CHANNEL_ACCESS_TOKEN 格式可能不正確")
    
    if inputs['sheets_id'] and len(inputs['sheets_id']) < 20:
        errors.append("GOOGLE_SHEET_ID 格式可能不正確（應該是長字串）")
    
    return errors

def generate_env_vars(inputs, google_creds):
    """生成環境變數"""
    env_vars = {}
    
    # LINE Bot 設定
    env_vars['LINE_CHANNEL_ACCESS_TOKEN'] = inputs['line_token']
    env_vars['LINE_CHANNEL_SECRET'] = inputs['line_secret']
    
    # Google Sheets 設定
    env_vars['GOOGLE_SHEET_ID'] = inputs['sheets_id']
    
    # Google 憑證 JSON
    if google_creds:
        # 壓縮 JSON（移除空格）
        env_vars['GOOGLE_SERVICE_ACCOUNT_JSON'] = json.dumps(google_creds, separators=(',', ':'))
    
    # Google Cloud 專案（可選）
    if inputs['gcp_project']:
        env_vars['GOOGLE_CLOUD_PROJECT'] = inputs['gcp_project']
    
    # Flask 設定
    env_vars['FLASK_ENV'] = 'production'
    env_vars['SECRET_KEY'] = generate_secret_key()
    
    return env_vars

def save_env_file(env_vars, filename='.env.zeabur'):
    """儲存環境變數到檔案"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Zeabur 環境變數設定\n")
            f.write("# 請將以下變數複製到 Zeabur 控制台\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ 環境變數已儲存到: {filename}")
        return True
    except Exception as e:
        print(f"❌ 儲存環境變數失敗: {e}")
        return False

def display_env_vars(env_vars):
    """顯示環境變數"""
    print("📋 生成的環境變數：")
    print("=" * 50)
    
    for key, value in env_vars.items():
        if key == 'GOOGLE_SERVICE_ACCOUNT_JSON':
            # JSON 太長，只顯示前後部分
            preview = value[:50] + "..." + value[-20:] if len(value) > 80 else value
            print(f"{key}={preview}")
        else:
            print(f"{key}={value}")
    
    print("=" * 50)

def display_zeabur_instructions():
    """顯示 Zeabur 設定指引"""
    print("\n🚀 Zeabur 部署指引：")
    print("-" * 30)
    print()
    print("1. 前往 Zeabur 控制台：https://dash.zeabur.com/")
    print("2. 建立新專案並從 GitHub 部署")
    print("3. 在服務設定中，前往 'Variables' 分頁")
    print("4. 逐一添加上述環境變數")
    print("5. 等待部署完成")
    print("6. 取得應用程式 URL")
    print("7. 更新 LINE Bot Webhook URL")
    print()
    print("💡 小提示：")
    print("- 可以直接複製 .env.zeabur 檔案中的內容")
    print("- GOOGLE_SERVICE_ACCOUNT_JSON 請確保複製完整")
    print("- 設定完成後記得刪除本地的 .env.zeabur 檔案")

def create_deployment_checklist():
    """建立部署檢查清單"""
    checklist = """
Zeabur 部署檢查清單
==================

部署前檢查：
□ GitHub Repository 已建立
□ 程式碼已推送到 GitHub
□ Google Service Account 已設定
□ Google Sheets 已建立並共用給 Service Account
□ LINE Bot Channel 已建立

Zeabur 設定：
□ 專案已從 GitHub 匯入
□ 所有環境變數已設定
□ 服務已成功啟動
□ 健康檢查通過 (/health)

LINE Bot 設定：
□ Webhook URL 已更新
□ Webhook 驗證通過
□ 自動回覆功能已停用

測試：
□ 傳送文字訊息測試
□ Google Sheets 記錄正常
□ 指令功能正常 (/help, /today)
□ 語音轉文字功能正常（如啟用）

部署完成！
"""
    
    with open('zeabur-deployment-checklist.txt', 'w', encoding='utf-8') as f:
        f.write(checklist)
    
    print("✅ 部署檢查清單已建立: zeabur-deployment-checklist.txt")

def main():
    print_header()
    
    # 讀取 Google 憑證
    print("📖 讀取 Google 憑證檔案...")
    google_creds = read_google_credentials()
    
    if not google_creds:
        print("\n❌ 無法繼續，請先設定 Google Service Account")
        print("參考文件: README.md 中的 Google 服務設定章節")
        return
    
    print("✅ Google 憑證檔案讀取成功")
    print(f"專案 ID: {google_creds.get('project_id', 'N/A')}")
    print(f"服務帳戶: {google_creds.get('client_email', 'N/A')}")
    print()
    
    # 取得使用者輸入
    inputs = get_user_input()
    
    # 驗證輸入
    errors = validate_inputs(inputs, google_creds)
    if errors:
        print("❌ 輸入驗證失敗：")
        for error in errors:
            print(f"  • {error}")
        return
    
    print("✅ 輸入驗證通過")
    print()
    
    # 生成環境變數
    print("🔧 生成環境變數...")
    env_vars = generate_env_vars(inputs, google_creds)
    
    # 顯示環境變數
    display_env_vars(env_vars)
    
    # 儲存到檔案
    print()
    save_env_file(env_vars)
    
    # 建立檢查清單
    create_deployment_checklist()
    
    # 顯示後續指引
    display_zeabur_instructions()
    
    print("\n🎉 環境變數生成完成！")
    print("請繼續按照 ZEABUR_DEPLOYMENT.md 完成部署")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 使用者中斷操作")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        print("請檢查設定並重試")