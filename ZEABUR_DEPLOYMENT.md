# Zeabur 部署完整指南

本指南將協助您將 LINE Bot 靈感筆記專案部署到 Zeabur 平台。

## 🚀 快速開始檢查清單

在開始部署前，請確認以下項目已完成：

- ✅ LINE Bot Channel 已建立（Token 和 Secret 已取得）
- ✅ Google Cloud 專案已設定（Service Account 和 Sheets ID 已取得）
- ✅ GitHub Repository 已建立
- ✅ Zeabur 帳戶已註冊並購買方案

## 📋 第一步：準備部署資料

### 1. 收集必要的環境變數

請準備以下資訊（稍後在 Zeabur 中設定）：

```bash
# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN=你的_channel_access_token
LINE_CHANNEL_SECRET=你的_channel_secret

# Google Sheets 設定  
GOOGLE_SHEET_ID=你的_google_sheet_id

# Google Service Account 憑證（完整 JSON）
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"...","private_key":"..."}

# 應用程式設定
FLASK_ENV=production
SECRET_KEY=你的_安全金鑰（隨機字串）

# 可選：Google Cloud 語音服務
GOOGLE_CLOUD_PROJECT=你的_google_cloud_project_id
```

### 2. 生成安全金鑰

執行以下 Python 指令生成安全的 SECRET_KEY：

```python
import secrets
print(secrets.token_urlsafe(32))
```

## 🌐 第二步：GitHub Repository 設定

### 1. 初始化並推送到 GitHub

```bash
# 初始化 Git repository
git init

# 添加所有檔案（敏感檔案已被 .gitignore 排除）
git add .

# 提交變更
git commit -m "Initial commit: LINE Bot inspiration notes for Zeabur deployment"

# 連接到您的 GitHub repository
git remote add origin https://github.com/您的用戶名/linebot-inspiration.git

# 推送到 main 分支
git push -u origin main
```

### 2. 驗證敏感檔案已被排除

確認以下檔案沒有被推送到 GitHub：
- `.env`
- `config/google-credentials.json`

## ⚡ 第三步：Zeabur 部署設定

### 1. 登入 Zeabur 並建立專案

1. 前往 [Zeabur](https://zeabur.com/)
2. 使用 GitHub 帳號登入
3. 點擊 **"Create Project"**
4. 選擇 **"Deploy from GitHub"**
5. 選擇您的 **linebot-inspiration** repository

### 2. 設定服務

1. Zeabur 會自動偵測到這是 Python 專案
2. 確認使用 **Python** 運行環境
3. 點擊 **"Deploy"** 開始初始部署

### 3. 設定環境變數

部署完成後，需要設定環境變數：

1. 在 Zeabur 專案頁面，點擊您的服務
2. 前往 **"Variables"** 分頁
3. 逐一添加以下環境變數：

#### 必要環境變數

| 變數名稱 | 值 | 說明 |
|---------|---|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | `你的_channel_access_token` | LINE Bot Channel Access Token |
| `LINE_CHANNEL_SECRET` | `你的_channel_secret` | LINE Bot Channel Secret |
| `GOOGLE_SHEET_ID` | `你的_google_sheet_id` | Google Sheets 文件 ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | `{"type":"service_account",...}` | 完整的 Google 憑證 JSON |
| `FLASK_ENV` | `production` | Flask 環境設定 |
| `SECRET_KEY` | `你的_隨機金鑰` | Flask 安全金鑰 |

#### 可選環境變數

| 變數名稱 | 值 | 說明 |
|---------|---|------|
| `GOOGLE_CLOUD_PROJECT` | `你的_project_id` | Google Cloud 專案 ID（語音功能） |

### 4. 取得應用程式 URL

1. 在服務頁面中，找到 **"Domains"** 區塊
2. 複製自動產生的 URL（格式類似：`https://your-app.zeabur.app`）
3. 記錄此 URL，稍後需要設定到 LINE Bot

## 🔗 第四步：LINE Bot Webhook 設定

### 1. 更新 Webhook URL

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 選擇您的 Channel
3. 前往 **"Messaging API"** 分頁
4. 在 **"Webhook settings"** 區塊：
   - 點擊 **"Edit"**
   - 輸入：`https://your-app.zeabur.app/webhook`
   - 點擊 **"Update"**
   - 確保 **"Use webhook"** 已啟用

### 2. 測試 Webhook 連線

1. 在 LINE Developers Console 中，點擊 **"Verify"** 測試連線
2. 應該顯示 **"Success"** 訊息

## ✅ 第五步：部署驗證

### 1. 健康檢查

在瀏覽器中訪問以下 URL：

```
https://your-app.zeabur.app/health
```

應該看到類似以下的回應：
```json
{
  "status": "healthy",
  "service": "linebot-inspiration"
}
```

### 2. Webhook 健康檢查

```
https://your-app.zeabur.app/webhook/health
```

### 3. 測試 LINE Bot 功能

1. 掃描 LINE Bot QR Code 加入好友
2. 傳送測試訊息：`Hello!`
3. 檢查是否收到確認回覆
4. 檢查 Google Sheets 是否有新記錄

## 📊 第六步：監控和維護

### 1. 查看 Zeabur 日誌

1. 在 Zeabur 服務頁面，點擊 **"Logs"** 分頁
2. 即時監控應用程式運行狀況

### 2. 監控指標

- **回應時間**
- **錯誤率**
- **記憶體使用量**
- **CPU 使用率**

## 🔧 故障排除

### 常見問題和解決方案

#### 1. 部署失敗
```bash
# 檢查 zeabur.json 設定
# 檢查 requirements.txt 格式
# 查看 Zeabur 建置日誌
```

#### 2. 環境變數錯誤
```bash
# 檢查變數名稱拼寫
# 確認 JSON 格式正確（使用 JSON 驗證器）
# 檢查是否有多餘的空格或特殊字元
```

#### 3. Google Sheets 連線失敗
```bash
# 確認 Service Account 權限
# 檢查 Sheets 共用設定
# 驗證 JSON 憑證格式
```

#### 4. LINE Bot 無回應
```bash
# 檢查 Webhook URL 設定
# 確認 Channel Access Token 正確
# 查看 Zeabur 日誌中的錯誤訊息
```

### 日誌分析

在 Zeabur 日誌中查找關鍵字：
- `ERROR`: 錯誤訊息
- `Webhook received`: Webhook 事件
- `sheets_service`: Google Sheets 操作
- `speech_service`: 語音處理

## 🚀 進階設定

### 1. 自訂網域

1. 在 Zeabur 服務頁面，前往 **"Domains"**
2. 點擊 **"Add Domain"**
3. 輸入您的自訂網域
4. 按照指示設定 DNS 記錄
5. 更新 LINE Bot Webhook URL

### 2. 效能優化

在 Zeabur 中調整以下設定：
- **Worker 數量**: 根據流量調整
- **記憶體配置**: 適當增加記憶體
- **自動擴縮**: 啟用自動擴縮功能

### 3. 備份策略

1. **程式碼備份**: GitHub Repository
2. **資料備份**: Google Sheets（雲端自動備份）
3. **設定備份**: 記錄所有環境變數

## 📱 使用者測試流程

部署完成後，請按以下順序測試：

### 1. 基本功能測試
```
使用者動作: 傳送 "測試訊息 #測試"
預期結果: 收到確認回覆，Google Sheets 新增記錄
```

### 2. 指令功能測試
```
使用者動作: 傳送 "/help"
預期結果: 收到使用說明
```

### 3. 語音功能測試
```
使用者動作: 傳送語音訊息
預期結果: 語音轉文字並記錄
```

### 4. 搜尋功能測試
```
使用者動作: 傳送 "/search 測試"
預期結果: 回傳搜尋結果
```

## 🎉 部署完成

恭喜！您的 LINE Bot 靈感筆記應用程式已成功部署到 Zeabur。

### 下一步建議

1. **設定監控告警**：關注應用程式健康狀況
2. **優化效能**：根據使用情況調整資源配置
3. **功能擴充**：根據需求添加新功能
4. **備份計畫**：定期備份重要資料

### 支援和維護

- **Zeabur 文件**: [https://zeabur.com/docs](https://zeabur.com/docs)
- **專案 GitHub**: 您的 Repository URL
- **技術支援**: 查看專案 Issues 或 Discussions

---

🔗 **重要連結**
- Zeabur 專案: `https://dash.zeabur.com/projects/your-project-id`
- 應用程式 URL: `https://your-app.zeabur.app`
- LINE Bot 管理: [LINE Developers Console](https://developers.line.biz/)
- Google Sheets: 您的試算表連結

**部署成功！開始享受您的智能靈感筆記機器人吧！** ✨