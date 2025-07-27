# 部署指南

本文件詳細說明如何將 LINE Bot 靈感筆記專案部署到不同的平台，並確保敏感資訊的安全性。

## 🔐 安全設定檢查清單

在部署之前，請確保完成以下安全設定：

- ✅ `.env` 檔案已加入 `.gitignore`
- ✅ `config/google-credentials.json` 已加入 `.gitignore`
- ✅ 所有敏感資訊使用環境變數
- ✅ GitHub Secrets 已正確設定
- ✅ 依賴套件已更新到最新版本

## 📋 部署前準備

### 1. 環境變數設定

創建生產環境的環境變數，**永遠不要將這些值提交到 Git**：

```bash
# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN=your_production_token
LINE_CHANNEL_SECRET=your_production_secret

# Google 設定
GOOGLE_SHEET_ID=your_production_sheet_id
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=config/google-credentials.json

# 應用程式設定
FLASK_ENV=production
PORT=5000
SECRET_KEY=your_secure_random_secret_key

# 可選：Google Cloud Project
GOOGLE_CLOUD_PROJECT=your_production_project_id
```

### 2. Google 憑證檔案處理

對於生產環境，建議使用以下方法之一來處理 Google 憑證：

#### 方法 A: 環境變數 (推薦)

將整個 JSON 憑證內容作為環境變數：

```bash
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","private_key":"..."}'
```

然後修改 `config/settings.py` 來支援此方法：

```python
import json
import os
from google.oauth2.service_account import Credentials

def get_google_credentials():
    # 優先使用環境變數中的 JSON
    json_str = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if json_str:
        cred_dict = json.loads(json_str)
        return Credentials.from_service_account_info(cred_dict)
    
    # 備選：使用檔案路徑
    key_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
    if key_path and os.path.exists(key_path):
        return Credentials.from_service_account_file(key_path)
    
    raise ValueError("No Google credentials found")
```

#### 方法 B: 安全檔案掛載

在部署時將憑證檔案安全地掛載到容器中，而不包含在映像中。

## 🌐 部署到不同平台

### 1. GitHub + Zeabur 部署

#### 步驟 1: 設定 GitHub Repository

```bash
# 初始化 Git repository
git init
git add .
git commit -m "Initial commit: LINE Bot inspiration notes project"

# 添加 GitHub remote (替換為您的 repository URL)
git remote add origin https://github.com/blueforster/linebot-inspiration.git
git branch -M main
git push -u origin main
```

#### 步驟 2: 設定 GitHub Secrets

前往 GitHub Repository > Settings > Secrets and variables > Actions，添加以下 Secrets：

```
LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET
GOOGLE_SHEET_ID
GOOGLE_SERVICE_ACCOUNT_JSON
SECRET_KEY
GOOGLE_CLOUD_PROJECT (可選)
```

#### 步驟 3: Zeabur 部署

1. 前往 [Zeabur](https://zeabur.com/)
2. 連接您的 GitHub 帳號
3. 選擇 repository 並導入專案
4. 在 Zeabur 環境變數設定中添加所有必要的環境變數
5. 部署完成後，將域名更新到 LINE Bot Webhook 設定

### 2. Heroku 部署

#### 步驟 1: 安裝 Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# 其他平台請參考：https://devcenter.heroku.com/articles/heroku-cli
```

#### 步驟 2: 建立 Heroku 應用程式

```bash
# 登入 Heroku
heroku login

# 建立應用程式
heroku create your-linebot-app-name

# 設定環境變數
heroku config:set LINE_CHANNEL_ACCESS_TOKEN="your_token"
heroku config:set LINE_CHANNEL_SECRET="your_secret"
heroku config:set GOOGLE_SHEET_ID="your_sheet_id"
heroku config:set GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
heroku config:set SECRET_KEY="your_secret_key"
heroku config:set FLASK_ENV="production"
```

#### 步驟 3: 部署到 Heroku

```bash
# 推送到 Heroku
git push heroku main

# 查看日誌
heroku logs --tail

# 打開應用程式
heroku open
```

### 3. Docker 部署

#### 步驟 1: 建立 Dockerfile

```dockerfile
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements 並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 建立 config 目錄
RUN mkdir -p config

# 設定檔案權限
RUN chmod -R 755 /app

# 暴露端口
EXPOSE 5000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# 啟動命令
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
```

#### 步驟 2: 建立 .dockerignore

```
.git
.gitignore
README.md
DEPLOYMENT.md
SECURITY.md
CLAUDE.md
.env
config/google-credentials.json
tests/
.pytest_cache
__pycache__
*.pyc
.coverage
htmlcov/
.vscode
.idea
```

#### 步驟 3: 建構和執行

```bash
# 建構映像
docker build -t linebot-inspiration .

# 執行容器 (使用環境變數檔案)
docker run -d \
  --name linebot-app \
  --env-file .env.production \
  -p 5000:5000 \
  linebot-inspiration

# 或者直接指定環境變數
docker run -d \
  --name linebot-app \
  -e LINE_CHANNEL_ACCESS_TOKEN="your_token" \
  -e LINE_CHANNEL_SECRET="your_secret" \
  -e GOOGLE_SHEET_ID="your_sheet_id" \
  -e GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \
  -p 5000:5000 \
  linebot-inspiration
```

### 4. Google Cloud Platform 部署

#### 步驟 1: 設定 app.yaml (App Engine)

```yaml
runtime: python311

env_variables:
  LINE_CHANNEL_ACCESS_TOKEN: "your_token"
  LINE_CHANNEL_SECRET: "your_secret"
  GOOGLE_SHEET_ID: "your_sheet_id"
  FLASK_ENV: "production"
  SECRET_KEY: "your_secret_key"

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

#### 步驟 2: 部署到 App Engine

```bash
# 安裝 Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# 登入和設定專案
gcloud auth login
gcloud config set project your-project-id

# 部署
gcloud app deploy

# 查看服務
gcloud app browse
```

## 🔧 部署後設定

### 1. 更新 LINE Bot Webhook URL

部署完成後，將新的 URL 更新到 LINE Developers Console：

1. 前往 [LINE Developers](https://developers.line.biz/)
2. 選擇您的 Channel
3. 前往 Messaging API 設定
4. 更新 Webhook URL：`https://your-deployed-domain.com/webhook`
5. 測試 Webhook 連線

### 2. 驗證部署

```bash
# 健康檢查
curl https://your-deployed-domain.com/health

# Webhook 健康檢查
curl https://your-deployed-domain.com/webhook/health
```

### 3. 監控和日誌

#### Zeabur
- 在 Zeabur 控制台查看即時日誌和監控指標

#### Heroku
```bash
# 查看日誌
heroku logs --tail --app your-app-name

# 查看資源使用
heroku ps --app your-app-name
```

#### Docker
```bash
# 查看容器日誌
docker logs linebot-app

# 查看容器狀態
docker stats linebot-app
```

## 🚨 故障排除

### 常見問題和解決方案

#### 1. 環境變數未載入
```bash
# 檢查環境變數是否正確設定
python -c "import os; print(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))"
```

#### 2. Google 憑證問題
```bash
# 驗證 JSON 格式
python -c "import json; json.loads(open('config/google-credentials.json').read())"
```

#### 3. Webhook 連線失敗
- 確認 URL 是 HTTPS
- 檢查防火牆設定
- 驗證簽名驗證是否正確

#### 4. 記憶體不足
- 增加容器記憶體限制
- 優化代碼中的記憶體使用
- 使用更少的 worker 程序

### 日誌分析

查看關鍵日誌模式：
```bash
# 搜尋錯誤
grep "ERROR" app.log

# 搜尋 Webhook 事件
grep "Webhook received" app.log

# 搜尋 Google Sheets 操作
grep "sheets_service" app.log
```

## 📊 效能優化

### 生產環境建議

1. **使用生產級 WSGI 伺服器**
   ```bash
   gunicorn wsgi:app --workers 4 --timeout 120 --bind 0.0.0.0:5000
   ```

2. **啟用 Gzip 壓縮**
3. **設定適當的緩存標頭**
4. **使用 CDN 進行靜態資源**
5. **實施速率限制**
6. **設定監控和警報**

### 擴展性考量

- **水平擴展**: 增加更多實例
- **資料庫**: 考慮使用 PostgreSQL 或 MySQL
- **快取**: 實施 Redis 快取
- **佇列**: 使用 Celery 處理背景任務

## 🔄 CI/CD 流程

GitHub Actions 工作流程已設定在 `.github/workflows/deploy.yml`，包括：

1. **測試階段**
   - 程式碼風格檢查 (flake8)
   - 單元測試 (pytest)
   - 安全掃描 (Trivy)

2. **部署階段**
   - 自動部署到 staging 環境
   - 手動批准後部署到 production

### 手動觸發部署

```bash
# 推送到 main 分支觸發部署
git push origin main

# 或者建立發布標籤
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## 📱 測試部署

部署完成後，測試以下功能：

1. **基本功能**
   - 傳送文字訊息
   - 查看是否正確記錄到 Google Sheets
   - 測試指令功能 (`/today`, `/stats`)

2. **語音功能**
   - 傳送語音訊息
   - 確認語音轉文字功能正常

3. **錯誤處理**
   - 傳送無效指令
   - 確認錯誤訊息友善

4. **效能測試**
   - 同時傳送多條訊息
   - 監控回應時間

---

**重要提醒**: 部署到生產環境前，請務必在測試環境中驗證所有功能正常運作，並確保所有敏感資訊都已妥善保護！