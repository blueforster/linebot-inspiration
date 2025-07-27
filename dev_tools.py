#!/usr/bin/env python3
"""
開發工具腳本 - 提供本地開發和測試功能
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

class DevTools:
    def __init__(self):
        self.project_root = Path(__file__).parent
        
    def run_command(self, command, description="", check=True):
        """執行命令行指令"""
        if description:
            print(f"🔧 {description}")
        
        print(f"執行: {command}")
        try:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.stdout:
                print(result.stdout)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"❌ 錯誤: {e}")
            if e.stderr:
                print(f"錯誤詳情: {e.stderr}")
            return False
    
    def start_dev_server(self, port=5000, debug=True):
        """啟動開發伺服器"""
        print(f"🚀 啟動開發伺服器 (端口: {port})")
        
        # 設定環境變數
        env_vars = {
            'FLASK_ENV': 'development',
            'FLASK_DEBUG': 'True' if debug else 'False',
            'PORT': str(port)
        }
        
        # 準備命令
        if os.name == 'nt':  # Windows
            activate_cmd = "venv\\Scripts\\activate && "
        else:  # macOS/Linux
            activate_cmd = "source venv/bin/activate && "
        
        # 設定環境變數的命令
        env_cmd = " && ".join([f"set {k}={v}" if os.name == 'nt' else f"export {k}={v}" 
                              for k, v in env_vars.items()])
        
        full_command = f"{activate_cmd}{env_cmd} && python app.py"
        
        print("按 Ctrl+C 停止伺服器")
        self.run_command(full_command, check=False)
    
    def run_tests(self, verbose=True, coverage=False):
        """執行測試"""
        print("🧪 執行測試套件")
        
        if os.name == 'nt':  # Windows
            activate_cmd = "venv\\Scripts\\activate && "
        else:  # macOS/Linux
            activate_cmd = "source venv/bin/activate && "
        
        # 基礎測試命令
        test_cmd = "python -m pytest"
        
        if verbose:
            test_cmd += " -v"
        
        if coverage:
            test_cmd += " --cov=app --cov-report=html --cov-report=term"
        
        test_cmd += " tests/"
        
        success = self.run_command(f"{activate_cmd}{test_cmd}", "執行測試")
        
        if coverage and success:
            print("📊 測試覆蓋率報告已生成在 htmlcov/ 目錄")
        
        return success
    
    def generate_test_data(self, count=10):
        """生成測試資料"""
        print(f"📝 生成 {count} 筆測試資料")
        
        test_messages = [
            "今天學到了新的 Python 技巧 #python #學習",
            "會議記錄：討論專案進度 #工作 #會議",
            "讀書心得：這本書很有趣 #讀書 #心得",
            "運動後的感想 #運動 #健康",
            "美食推薦：今天吃到很棒的餐廳 #美食 #推薦",
            "旅遊計畫：下個月要去日本 #旅遊 #計畫",
            "電影觀後感：這部電影很感人 #電影 #心得",
            "工作靈感：新的產品功能想法 #工作 #靈感",
            "學習筆記：演算法複習 #學習 #演算法",
            "生活感悟：時間管理的重要性 #生活 #感悟"
        ]
        
        from app.models.message_model import MessageModel
        
        messages = []
        for i in range(count):
            content = test_messages[i % len(test_messages)]
            message = MessageModel(
                user_id=f"test_user_{i % 3 + 1}",
                message_type="text",
                content=f"{content} (測試資料 {i+1})"
            )
            messages.append(message)
        
        # 輸出到檔案
        test_data_file = self.project_root / "test_data.json"
        with open(test_data_file, 'w', encoding='utf-8') as f:
            json.dump([msg.to_dict() for msg in messages], f, ensure_ascii=False, indent=2)
        
        print(f"✅ 測試資料已生成: {test_data_file}")
        return messages
    
    def validate_config(self):
        """驗證設定檔案"""
        print("🔍 驗證專案設定")
        
        errors = []
        warnings = []
        
        # 檢查 .env 檔案
        env_file = self.project_root / ".env"
        if not env_file.exists():
            errors.append(".env 檔案不存在")
        else:
            print("✅ .env 檔案存在")
            
            # 檢查必要的環境變數
            required_vars = [
                'LINE_CHANNEL_ACCESS_TOKEN',
                'LINE_CHANNEL_SECRET',
                'GOOGLE_SHEET_ID'
            ]
            
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            for var in required_vars:
                if f"{var}=" not in env_content or f"{var}=your_" in env_content:
                    warnings.append(f"環境變數 {var} 可能未正確設定")
        
        # 檢查 Google 憑證檔案
        credentials_file = self.project_root / "config" / "google-credentials.json"
        if not credentials_file.exists():
            errors.append("Google 憑證檔案不存在: config/google-credentials.json")
        else:
            print("✅ Google 憑證檔案存在")
            
            try:
                with open(credentials_file, 'r') as f:
                    cred_data = json.load(f)
                
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                for field in required_fields:
                    if field not in cred_data:
                        errors.append(f"Google 憑證檔案缺少必要欄位: {field}")
                
                if cred_data.get('project_id') == 'your-project-id':
                    warnings.append("Google 憑證檔案使用範例值，請更換為實際憑證")
            
            except json.JSONDecodeError:
                errors.append("Google 憑證檔案格式錯誤")
        
        # 檢查虛擬環境
        venv_path = self.project_root / "venv"
        if not venv_path.exists():
            warnings.append("虛擬環境不存在，請執行 python setup.py")
        else:
            print("✅ 虛擬環境存在")
        
        # 輸出結果
        if errors:
            print("\n❌ 發現錯誤:")
            for error in errors:
                print(f"   • {error}")
        
        if warnings:
            print("\n⚠️  警告:")
            for warning in warnings:
                print(f"   • {warning}")
        
        if not errors and not warnings:
            print("\n✅ 所有設定檢查通過！")
        
        return len(errors) == 0
    
    def start_ngrok(self, port=5000):
        """啟動 ngrok（需要先安裝）"""
        print(f"🌐 啟動 ngrok (端口: {port})")
        
        # 檢查 ngrok 是否已安裝
        check_cmd = "ngrok version"
        if not self.run_command(check_cmd, check=False):
            print("❌ ngrok 未安裝。請先安裝 ngrok:")
            print("   https://ngrok.com/download")
            return False
        
        print(f"⚡ 建立 ngrok 隧道到 localhost:{port}")
        print("按 Ctrl+C 停止 ngrok")
        
        self.run_command(f"ngrok http {port}", check=False)
    
    def lint_code(self):
        """程式碼檢查"""
        print("🔍 檢查程式碼風格")
        
        if os.name == 'nt':  # Windows
            activate_cmd = "venv\\Scripts\\activate && "
        else:  # macOS/Linux
            activate_cmd = "source venv/bin/activate && "
        
        # 安裝 flake8（如果未安裝）
        self.run_command(f"{activate_cmd}pip install flake8", "安裝 flake8", check=False)
        
        # 執行程式碼檢查
        success = self.run_command(
            f"{activate_cmd}flake8 app/ --max-line-length=100 --exclude=__pycache__",
            "執行程式碼檢查"
        )
        
        if success:
            print("✅ 程式碼風格檢查通過")
        else:
            print("⚠️  發現程式碼風格問題")
        
        return success
    
    def backup_data(self):
        """備份資料"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_file = backup_dir / f"backup_{timestamp}.json"
        
        print(f"💾 建立資料備份: {backup_file}")
        
        try:
            from app.services.sheets_service import SheetsService
            
            sheets_service = SheetsService()
            success = sheets_service.backup_data(str(backup_file))
            
            if success:
                print("✅ 資料備份完成")
            else:
                print("❌ 資料備份失敗")
            
            return success
            
        except Exception as e:
            print(f"❌ 備份過程發生錯誤: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="LINE Bot 開發工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 啟動開發伺服器
    server_parser = subparsers.add_parser('serve', help='啟動開發伺服器')
    server_parser.add_argument('--port', type=int, default=5000, help='伺服器端口')
    server_parser.add_argument('--no-debug', action='store_true', help='關閉除錯模式')
    
    # 執行測試
    test_parser = subparsers.add_parser('test', help='執行測試')
    test_parser.add_argument('--coverage', action='store_true', help='產生測試覆蓋率報告')
    test_parser.add_argument('--quiet', action='store_true', help='簡化輸出')
    
    # 驗證設定
    subparsers.add_parser('validate', help='驗證專案設定')
    
    # 生成測試資料
    data_parser = subparsers.add_parser('generate-data', help='生成測試資料')
    data_parser.add_argument('--count', type=int, default=10, help='生成資料數量')
    
    # 啟動 ngrok
    ngrok_parser = subparsers.add_parser('ngrok', help='啟動 ngrok')
    ngrok_parser.add_argument('--port', type=int, default=5000, help='目標端口')
    
    # 程式碼檢查
    subparsers.add_parser('lint', help='檢查程式碼風格')
    
    # 備份資料
    subparsers.add_parser('backup', help='備份資料')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    dev_tools = DevTools()
    
    if args.command == 'serve':
        dev_tools.start_dev_server(port=args.port, debug=not args.no_debug)
    elif args.command == 'test':
        dev_tools.run_tests(verbose=not args.quiet, coverage=args.coverage)
    elif args.command == 'validate':
        dev_tools.validate_config()
    elif args.command == 'generate-data':
        dev_tools.generate_test_data(count=args.count)
    elif args.command == 'ngrok':
        dev_tools.start_ngrok(port=args.port)
    elif args.command == 'lint':
        dev_tools.lint_code()
    elif args.command == 'backup':
        dev_tools.backup_data()

if __name__ == "__main__":
    main()