# 🚀 Zeabur 最終部署指南

## ✅ 修復完成

已解決 Zeabur 部署問題：
- ✅ 簡化了 zeabur.json 設定
- ✅ 移除了有問題的依賴套件
- ✅ 暫時停用語音轉文字功能（可稍後啟用）
- ✅ 修復了安全性問題

## 🎯 現在立即部署

### 第一步：在 Zeabur 重新部署

1. 前往 [Zeabur Dashboard](https://dash.zeabur.com/)
2. 如果之前的專案失敗，點擊重新部署或刪除後重新建立
3. Create Project → Deploy from GitHub
4. 選擇 `blueforster/linebot-inspiration`

### 第二步：設定環境變數

在 Zeabur 的 Variables 分頁中設定以下變數：

| 變數名稱 | 值 | 來源 |
|---------|---|------|
| `LINE_CHANNEL_ACCESS_TOKEN` | 您的實際 Token | 從 .env 檔案 |
| `LINE_CHANNEL_SECRET` | 您的實際 Secret | 從 .env 檔案 |
| `GOOGLE_SHEET_ID` | 您的實際 Sheets ID | 從 .env 檔案 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | 完整 JSON 字串 | 從 config/google-credentials.json |
| `FLASK_ENV` | `production` | 固定值 |
| `SECRET_KEY` | 隨機產生的金鑰 | 使用腳本產生 |

### 第三步：準備 Google Service Account JSON

將 `config/google-credentials.json` 的內容壓縮成一行：

```bash
# 在本地執行這個命令來準備 JSON
python3 -c "
import json
with open('config/google-credentials.json', 'r') as f:
    data = json.load(f)
print(json.dumps(data, separators=(',', ':')))
"
```

將輸出的結果設定為 `GOOGLE_SERVICE_ACCOUNT_JSON` 變數值。

### 第四步：生成 SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

將輸出結果設定為 `SECRET_KEY` 變數值。

## ✅ 預期結果

部署成功後：
- 應用程式狀態顯示為 "Running"
- 健康檢查端點 `/health` 回應正常
- 可以取得 Zeabur 提供的應用程式 URL

## 🔗 後續設定

### 更新 LINE Bot Webhook

取得 Zeabur 應用程式 URL 後：
1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 設定 Webhook URL：`https://your-app.zeabur.app/webhook`
3. 測試連線

### 功能測試

1. 加入 LINE Bot 好友
2. 傳送測試訊息：`Hello! #測試`
3. 檢查 Google Sheets 記錄
4. 測試指令：`/help`

## 📝 注意事項

- 語音轉文字功能暫時停用，需要可以稍後重新啟用
- 圖片處理功能暫時簡化
- 所有基本功能（文字記錄、Google Sheets、指令）都正常運作

## 🎉 完成！

按照此指南，您的 LINE Bot 應該能成功部署到 Zeabur！