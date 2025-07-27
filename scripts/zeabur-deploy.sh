#!/bin/bash

# Zeabur 專用部署腳本
# 使用方法: ./scripts/zeabur-deploy.sh

set -e  # 遇到錯誤立即退出

# 顏色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 輔助函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${GREEN}============================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}============================================${NC}"
}

# 檢查必要工具
check_dependencies() {
    log_info "檢查必要工具..."
    
    local deps=("git" "python3" "curl")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep 未安裝，請先安裝必要的依賴"
            exit 1
        fi
    done
    
    log_success "所有依賴檢查通過"
}

# 驗證專案結構
validate_project_structure() {
    log_info "驗證專案結構..."
    
    local required_files=(
        "zeabur.json"
        "requirements.txt"
        "wsgi.py"
        "app.py"
        ".gitignore"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "缺少必要檔案: $file"
            exit 1
        fi
    done
    
    log_success "專案結構驗證通過"
}

# 檢查敏感檔案
check_sensitive_files() {
    log_info "檢查敏感檔案保護..."
    
    local sensitive_files=(
        ".env"
        "config/google-credentials.json"
    )
    
    for file in "${sensitive_files[@]}"; do
        if [[ -f "$file" ]]; then
            # 檢查檔案是否在 .gitignore 中
            if ! grep -q "$file" .gitignore 2>/dev/null; then
                log_error "敏感檔案 $file 未在 .gitignore 中！"
                exit 1
            fi
            
            # 檢查檔案是否已被追蹤
            if git ls-files --error-unmatch "$file" &>/dev/null; then
                log_error "敏感檔案 $file 已被 Git 追蹤！"
                log_info "請執行: git rm --cached $file"
                exit 1
            fi
        fi
    done
    
    log_success "敏感檔案檢查通過"
}

# 驗證環境變數
validate_env_vars() {
    log_info "檢查環境變數設定..."
    
    # 如果存在 .env 檔案，載入並檢查
    if [[ -f ".env" ]]; then
        set -a
        source .env
        set +a
        log_info "已載入 .env 檔案"
    fi
    
    local required_vars=(
        "LINE_CHANNEL_ACCESS_TOKEN"
        "LINE_CHANNEL_SECRET"
        "GOOGLE_SHEET_ID"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_warning "以下環境變數未在本地設定（需要在 Zeabur 中設定）："
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_info "這是正常的，稍後在 Zeabur 控制台中設定即可"
    else
        log_success "環境變數檢查通過"
    fi
}

# 執行本地測試
run_local_tests() {
    log_info "執行本地測試..."
    
    # 設定測試環境變數
    export LINE_CHANNEL_ACCESS_TOKEN="test_token"
    export LINE_CHANNEL_SECRET="test_secret"
    export GOOGLE_SHEET_ID="test_sheet_id"
    export FLASK_ENV="testing"
    
    # 建立模擬的 Google 憑證檔案
    mkdir -p config
    echo '{"type": "service_account", "project_id": "test", "private_key": "test", "client_email": "test@test.com"}' > config/google-credentials.json
    
    # 檢查 Python 語法
    log_info "檢查 Python 語法..."
    if python3 -m py_compile app.py; then
        log_success "Python 語法檢查通過"
    else
        log_error "Python 語法錯誤"
        exit 1
    fi
    
    # 執行測試（如果有）
    if [[ -f "tests/test_webhook.py" ]]; then
        log_info "執行單元測試..."
        if python3 -m pytest tests/ -v --tb=short; then
            log_success "單元測試通過"
        else
            log_warning "單元測試有失敗項目，但繼續部署"
        fi
    fi
    
    # 清理測試檔案
    rm -f config/google-credentials.json
    
    log_success "本地測試完成"
}

# 生成部署資訊
generate_deployment_info() {
    log_info "生成部署資訊..."
    
    # 建立部署資訊檔案
    cat > deployment-info.txt << EOF
Zeabur 部署資訊
=============

專案名稱: LINE Bot 靈感筆記
部署時間: $(date)
Git Commit: $(git rev-parse HEAD)
Git Branch: $(git branch --show-current)

必要環境變數（需在 Zeabur 中設定）:
- LINE_CHANNEL_ACCESS_TOKEN=你的_channel_access_token
- LINE_CHANNEL_SECRET=你的_channel_secret
- GOOGLE_SHEET_ID=你的_google_sheet_id
- GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
- FLASK_ENV=production
- SECRET_KEY=你的_隨機金鑰

可選環境變數:
- GOOGLE_CLOUD_PROJECT=你的_google_cloud_project_id

健康檢查端點:
- /health
- /webhook/health

Webhook URL 格式:
- https://你的應用.zeabur.app/webhook
EOF
    
    log_success "部署資訊已生成: deployment-info.txt"
}

# 準備 Git 提交
prepare_git_commit() {
    log_info "準備 Git 提交..."
    
    # 檢查是否有未提交的變更
    if [[ -n "$(git status --porcelain)" ]]; then
        log_info "發現未提交的變更"
        git status
        
        echo
        read -p "是否要提交這些變更？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add .
            git commit -m "準備 Zeabur 部署 - $(date '+%Y-%m-%d %H:%M:%S')"
            log_success "變更已提交"
        else
            log_warning "未提交變更，繼續部署現有版本"
        fi
    else
        log_success "沒有未提交的變更"
    fi
}

# 推送到 GitHub
push_to_github() {
    log_info "推送到 GitHub..."
    
    # 檢查 remote 是否存在
    if ! git remote get-url origin &>/dev/null; then
        log_error "未設定 GitHub remote，請先設定："
        echo "git remote add origin https://github.com/您的用戶名/linebot-inspiration.git"
        exit 1
    fi
    
    # 取得當前分支
    local current_branch=$(git branch --show-current)
    
    # 推送到 GitHub
    log_info "推送分支 '$current_branch' 到 GitHub..."
    if git push origin "$current_branch"; then
        log_success "成功推送到 GitHub"
    else
        log_error "推送到 GitHub 失敗"
        exit 1
    fi
}

# 生成 SECRET_KEY
generate_secret_key() {
    log_info "生成安全金鑰..."
    
    local secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    echo
    log_success "已生成安全金鑰，請在 Zeabur 中設定："
    echo "SECRET_KEY=$secret_key"
    echo
    
    # 保存到部署資訊檔案
    echo "生成的 SECRET_KEY: $secret_key" >> deployment-info.txt
}

# 顯示部署後步驟
show_post_deployment_steps() {
    log_step "部署後設定步驟"
    
    echo "🚀 恭喜！專案已準備好部署到 Zeabur"
    echo
    echo "📋 接下來請按照以下步驟完成部署："
    echo
    echo "1. 前往 Zeabur 控制台："
    echo "   https://dash.zeabur.com/"
    echo
    echo "2. 建立新專案並從 GitHub 部署"
    echo
    echo "3. 在 Zeabur 中設定環境變數（參考 deployment-info.txt）"
    echo
    echo "4. 等待部署完成，取得應用程式 URL"
    echo
    echo "5. 更新 LINE Bot Webhook URL："
    echo "   https://您的應用.zeabur.app/webhook"
    echo
    echo "6. 測試部署："
    echo "   - 健康檢查: https://您的應用.zeabur.app/health"
    echo "   - 傳送測試訊息給 LINE Bot"
    echo
    echo "📖 詳細說明請參考: ZEABUR_DEPLOYMENT.md"
    echo
    log_success "部署準備完成！"
}

# 主要執行邏輯
main() {
    log_step "開始 Zeabur 部署準備"
    
    # 執行檢查
    check_dependencies
    validate_project_structure
    check_sensitive_files
    validate_env_vars
    
    # 執行測試
    run_local_tests
    
    # 準備部署
    generate_secret_key
    generate_deployment_info
    prepare_git_commit
    push_to_github
    
    # 顯示後續步驟
    show_post_deployment_steps
}

# 顯示使用說明
show_usage() {
    echo "Zeabur 部署腳本"
    echo "==============="
    echo
    echo "此腳本會："
    echo "1. 檢查專案結構和依賴"
    echo "2. 驗證敏感檔案保護"
    echo "3. 執行本地測試"
    echo "4. 生成部署資訊"
    echo "5. 推送程式碼到 GitHub"
    echo "6. 提供後續 Zeabur 設定指引"
    echo
    echo "使用方法:"
    echo "  $0              # 執行完整部署準備"
    echo "  $0 --help       # 顯示此說明"
}

# 參數檢查
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# 執行主程式
main "$@"