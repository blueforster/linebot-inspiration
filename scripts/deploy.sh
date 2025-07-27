#!/bin/bash

# LINE Bot 部署腳本
# 使用方法: ./scripts/deploy.sh [platform] [environment]
# 範例: ./scripts/deploy.sh github production

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

# 檢查必要工具
check_dependencies() {
    local deps=("git" "python3" "pip")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep 未安裝，請先安裝必要的依賴"
            exit 1
        fi
    done
    
    log_success "所有依賴檢查通過"
}

# 驗證環境變數
validate_env() {
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
        log_error "缺少必要的環境變數："
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_info "請設定環境變數或建立 .env 檔案"
        exit 1
    fi
    
    log_success "環境變數驗證通過"
}

# 檢查敏感檔案
check_sensitive_files() {
    local sensitive_files=(
        ".env"
        "config/google-credentials.json"
    )
    
    log_info "檢查敏感檔案是否已排除..."
    
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

# 執行測試
run_tests() {
    log_info "執行測試套件..."
    
    # 建立臨時測試環境
    export LINE_CHANNEL_ACCESS_TOKEN="test_token"
    export LINE_CHANNEL_SECRET="test_secret"
    export GOOGLE_SHEET_ID="test_sheet"
    export FLASK_ENV="testing"
    
    # 建立模擬的 Google 憑證檔案
    mkdir -p config
    echo '{"type": "service_account", "project_id": "test"}' > config/google-credentials.json
    
    # 執行測試
    if python -m pytest tests/ -v; then
        log_success "所有測試通過"
    else
        log_error "測試失敗"
        exit 1
    fi
    
    # 清理測試檔案
    rm -f config/google-credentials.json
}

# 程式碼品質檢查
code_quality_check() {
    log_info "執行程式碼品質檢查..."
    
    # 安裝檢查工具（如果尚未安裝）
    pip install flake8 black isort --quiet
    
    # 程式碼格式檢查
    log_info "檢查程式碼格式..."
    if flake8 app/ --max-line-length=100 --exclude=__pycache__; then
        log_success "程式碼格式檢查通過"
    else
        log_warning "程式碼格式有問題，建議修復後再部署"
    fi
}

# GitHub 部署
deploy_to_github() {
    local environment=$1
    
    log_info "準備部署到 GitHub ($environment)..."
    
    # 檢查 Git 狀態
    if [[ -n "$(git status --porcelain)" ]]; then
        log_error "有未提交的變更，請先提交所有變更"
        git status
        exit 1
    fi
    
    # 檢查分支
    local current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" ]] && [[ "$environment" == "production" ]]; then
        log_warning "目前在 $current_branch 分支，生產環境建議使用 main 分支"
        read -p "是否繼續？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # 推送到 GitHub
    log_info "推送到 GitHub..."
    git push origin "$current_branch"
    
    log_success "GitHub 部署完成"
    log_info "請前往 GitHub Actions 查看部署狀態"
}

# Docker 部署
deploy_to_docker() {
    local environment=$1
    
    log_info "準備 Docker 部署 ($environment)..."
    
    # 檢查 Docker 是否安裝
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi
    
    # 建構映像
    local image_tag="linebot-inspiration:$environment"
    log_info "建構 Docker 映像: $image_tag"
    
    if docker build -t "$image_tag" .; then
        log_success "Docker 映像建構成功"
    else
        log_error "Docker 映像建構失敗"
        exit 1
    fi
    
    # 詢問是否立即執行
    read -p "是否立即執行容器？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 停止現有容器（如果存在）
        docker stop linebot-app 2>/dev/null || true
        docker rm linebot-app 2>/dev/null || true
        
        # 執行新容器
        log_info "啟動 Docker 容器..."
        docker run -d \
            --name linebot-app \
            --env-file .env \
            -p 5000:5000 \
            "$image_tag"
        
        log_success "Docker 容器啟動成功"
        log_info "容器日誌: docker logs linebot-app"
    fi
}

# Heroku 部署
deploy_to_heroku() {
    local app_name=$1
    
    log_info "準備部署到 Heroku..."
    
    # 檢查 Heroku CLI
    if ! command -v heroku &> /dev/null; then
        log_error "Heroku CLI 未安裝"
        log_info "請前往 https://devcenter.heroku.com/articles/heroku-cli 安裝"
        exit 1
    fi
    
    # 登入檢查
    if ! heroku auth:whoami &>/dev/null; then
        log_info "請先登入 Heroku"
        heroku login
    fi
    
    # 檢查應用程式是否存在
    if [[ -n "$app_name" ]]; then
        if ! heroku apps:info "$app_name" &>/dev/null; then
            log_info "建立 Heroku 應用程式: $app_name"
            heroku create "$app_name"
        fi
        
        # 設定 Git remote
        if ! git remote get-url heroku &>/dev/null; then
            heroku git:remote -a "$app_name"
        fi
    fi
    
    # 部署
    log_info "部署到 Heroku..."
    git push heroku main
    
    log_success "Heroku 部署完成"
    log_info "應用程式 URL: $(heroku info -s | grep web_url | cut -d= -f2)"
}

# 部署後驗證
post_deploy_verification() {
    local url=$1
    
    if [[ -z "$url" ]]; then
        log_warning "未提供 URL，跳過部署驗證"
        return
    fi
    
    log_info "驗證部署結果..."
    
    # 健康檢查
    local health_check_url="$url/health"
    log_info "健康檢查: $health_check_url"
    
    # 等待服務啟動
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f "$health_check_url" &>/dev/null; then
            log_success "健康檢查通過"
            break
        else
            if [[ $attempt -eq $max_attempts ]]; then
                log_error "健康檢查失敗"
                exit 1
            fi
            log_info "等待服務啟動... ($attempt/$max_attempts)"
            sleep 5
            ((attempt++))
        fi
    done
    
    # Webhook 健康檢查
    local webhook_health_url="$url/webhook/health"
    log_info "Webhook 健康檢查: $webhook_health_url"
    
    if curl -f "$webhook_health_url" &>/dev/null; then
        log_success "Webhook 健康檢查通過"
    else
        log_warning "Webhook 健康檢查失敗，請檢查設定"
    fi
}

# 主要執行邏輯
main() {
    local platform=${1:-"github"}
    local environment=${2:-"production"}
    local app_name=${3:-""}
    
    log_info "開始部署流程..."
    log_info "平台: $platform"
    log_info "環境: $environment"
    
    # 載入環境變數
    if [[ -f ".env" ]]; then
        set -a
        source .env
        set +a
        log_info "環境變數已載入"
    fi
    
    # 執行檢查
    check_dependencies
    check_sensitive_files
    validate_env
    code_quality_check
    run_tests
    
    # 根據平台部署
    case $platform in
        "github")
            deploy_to_github "$environment"
            ;;
        "docker")
            deploy_to_docker "$environment"
            ;;
        "heroku")
            deploy_to_heroku "$app_name"
            ;;
        *)
            log_error "不支援的部署平台: $platform"
            log_info "支援的平台: github, docker, heroku"
            exit 1
            ;;
    esac
    
    log_success "部署流程完成！"
}

# 顯示使用說明
show_usage() {
    echo "使用方法: $0 [platform] [environment] [app-name]"
    echo ""
    echo "平台選項:"
    echo "  github    - GitHub + GitHub Actions (預設)"
    echo "  docker    - Docker 容器部署"
    echo "  heroku    - Heroku 部署"
    echo ""
    echo "環境選項:"
    echo "  production - 生產環境 (預設)"
    echo "  staging    - 測試環境"
    echo ""
    echo "範例:"
    echo "  $0 github production"
    echo "  $0 docker staging"
    echo "  $0 heroku production my-linebot-app"
}

# 參數檢查
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_usage
    exit 0
fi

# 執行主程式
main "$@"