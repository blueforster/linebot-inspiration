# 靈感筆記 LINE Bot

一個智能的 LINE Bot，幫助您記錄和管理靈感筆記，支援文字、語音和圖片訊息，自動整合到 Google Sheets 進行儲存和分析。

## ✨ 主要功能

### 📝 多媒體記錄
- **文字訊息**：直接記錄您的靈感和想法
- **🎵 語音訊息**：自動轉換為文字並記錄
  - 支援繁體中文、英文、日文多語言識別
  - 自動標點符號添加
  - 智能音訊格式處理（M4A、MP3、WEBM等）
- **🖼️ 圖片訊息**：OCR 自動辨識圖片中的文字
  - 支援多語言文字識別（中英日等主要語言）
  - 手寫字和印刷字體都能識別
  - 文件、截圖、標誌等各種圖片類型
  - 長文字智能預覽（前200字符）
- **標籤系統**：使用 `#標籤` 語法自動分類和組織

### 🔍 智能搜尋與統計
- **關鍵字搜尋**：快速找到歷史記錄
- **標籤統計**：查看最常使用的標籤
- **日期查詢**：查看今日或特定時間的記錄
- **個人統計**：了解您的記錄習慣和趨勢

### ☁️ 雲端整合
- **Google Sheets**：自動同步所有記錄到試算表
- **即時備份**：資料安全存儲，永不丟失
- **多裝置存取**：隨時隨地查看和管理記錄

## 🚀 快速開始

### 前置需求

- Python 3.9+
- LINE Developer Account
- Google Cloud Platform 帳號
- Google Sheets API 存取權限

### 1. 克隆專案

```bash
git clone <your-repo-url>
cd linebot1
```

### 2. 建立虛擬環境

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows
venv\\Scripts\\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安裝依賴

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 環境設定

1. 複製環境變數範例檔案：
```bash
cp .env.example .env
```

2. 編輯 `.env` 檔案，填入您的設定：

```bash
# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here

# Google Sheets 設定
GOOGLE_SHEET_ID=your_google_sheet_id_here
GOOGLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...your_private_key...\n-----END PRIVATE KEY-----

# Flask 設定
PORT=5000
FLASK_ENV=development
FLASK_DEBUG=True
```

### 5. Google 服務設定

#### 5.1 建立 Google Service Account

**步驟 1: 建立 Google Cloud 專案**

1. 開啟瀏覽器，前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 如果是第一次使用，請登入您的 Google 帳號
3. 點擊頂部的「選取專案」下拉選單
4. 點擊「新增專案」
5. 輸入專案名稱（例如：`linebot-inspiration`）
6. 點擊「建立」

**步驟 2: 啟用必要的 API**

1. 在 Google Cloud Console 左側選單中，點擊「API 和服務」>「程式庫」
2. 或直接前往：https://console.cloud.google.com/apis/library
3. 搜尋並啟用以下 API：

   **Google Sheets API**：
   - 在搜尋框輸入「Google Sheets API」
   - 點擊搜尋結果中的「Google Sheets API」
   - 點擊「啟用」按鈕

   **Google Drive API**：
   - 搜尋「Google Drive API」
   - 點擊結果並「啟用」

   **Google Cloud Speech-to-Text API（語音轉文字功能）**：
   - 搜尋「Cloud Speech-to-Text API」
   - 點擊結果並「啟用」
   - ⚠️ 此 API 為付費服務，每月前 60 分鐘免費

   **Google Cloud Vision API（圖片轉文字功能）**：
   - 搜尋「Cloud Vision API」
   - 點擊結果並「啟用」
   - ⚠️ 此 API 為付費服務，每月前 1000 次免費

**步驟 3: 建立 Service Account**

1. 在左側選單點擊「IAM 與管理」>「服務帳戶」
2. 或直接前往：https://console.cloud.google.com/iam-admin/serviceaccounts
3. 點擊「建立服務帳戶」
4. 填寫服務帳戶詳細資料：
   - **服務帳戶名稱**：`linebot-sheets-service`
   - **服務帳戶 ID**：會自動產生
   - **說明**：`LINE Bot 存取 Google Sheets 的服務帳戶`
5. 點擊「建立並繼續」
6. **授予服務帳戶專案存取權**：
   - 選擇角色：「編輯器」或「基本」>「編輯者」
   - 點擊「繼續」
7. 點擊「完成」

**步驟 4: 下載金鑰檔案**

1. 在服務帳戶列表中，找到剛建立的服務帳戶
2. 點擊服務帳戶的電子郵件地址
3. 切換到「金鑰」分頁
4. 點擊「新增金鑰」>「建立新的金鑰」
5. 選擇「JSON」格式
6. 點擊「建立」
7. 金鑰檔案會自動下載到您的電腦
8. 將下載的檔案重新命名為 `google-credentials.json`
9. 將檔案移動到專案的 `config/` 資料夾中

**重要提醒**：請妥善保管這個 JSON 檔案，不要將其上傳到公開的程式碼倉庫。

#### 5.2 建立 Google Sheets

**步驟 1: 建立新的試算表**

1. 開啟瀏覽器，前往 [Google Sheets](https://sheets.google.com/)
2. 點擊「+」或「空白」建立新的試算表
3. 將試算表重新命名為有意義的名稱，例如：`LINE Bot 靈感記錄`

**步驟 2: 取得試算表 ID**

1. 在試算表開啟狀態下，檢查瀏覽器網址列
2. URL 格式如下：
   ```
   https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
   ```
3. 複製 `/d/` 和 `/edit` 之間的長字串（這就是 Sheets ID）
4. 例如上述 URL 中的 `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

**步驟 3: 設定共用權限**

1. 在試算表中，點擊右上角的「共用」按鈕
2. 在「新增使用者和群組」欄位中，輸入您的 Service Account 電子郵件地址
   - 電子郵件格式類似：`linebot-sheets-service@your-project-id.iam.gserviceaccount.com`
   - 這個電子郵件可以在 Google Cloud Console 的服務帳戶頁面找到
3. 在權限下拉選單中選擇「編輯者」
4. **取消勾選**「通知使用者」（因為這是服務帳戶，不需要通知）
5. 點擊「共用」

**步驟 4: 更新環境變數**

將取得的 Sheets ID 新增到 `.env` 檔案：
```bash
GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

#### 5.3 LINE Bot 設定

**步驟 1: 註冊 LINE Developers 帳號**

1. 前往 [LINE Developers](https://developers.line.biz/)
2. 點擊右上角「Log in」
3. 使用您的 LINE 帳號登入
4. 如果是第一次使用，需要同意開發者條款

**步驟 2: 建立 Provider**

1. 登入後，點擊「Create a new provider」
2. 輸入 Provider 名稱（例如：`我的 LINE Bot 專案`）
3. 點擊「Create」

**步驟 3: 建立 Messaging API Channel**

1. 在 Provider 頁面中，點擊「Create a Messaging API channel」
2. 填寫 Channel 資訊：
   - **App name**：`靈感筆記機器人`
   - **App description**：`協助記錄和管理靈感筆記的智能機器人`
   - **App icon**：可上傳機器人頭像（可選）
   - **App banner**：可上傳橫幅圖片（可選）
   - **Large size icon**：大尺寸圖示（可選）
   - **Plan**：選擇「Developer Trial」或「Free」
   - **Category**：選擇適合的類別（如：Productivity）
   - **Subcategory**：選擇子類別
   - **Subcategory (Large size icon)**：選擇子類別
   - **Region**：選擇「Taiwan」或「Japan」
   - **App types**：可選擇「App」

3. 閱讀並同意服務條款
4. 點擊「Create」

**步驟 4: 取得 Channel Access Token**

1. 在 Channel 設定頁面中，切換到「Messaging API」分頁
2. 向下捲動找到「Channel access token」區塊
3. 點擊「Generate」或「Issue」
4. 複製產生的 Token（長字串）
5. 將 Token 貼到 `.env` 檔案：
   ```bash
   LINE_CHANNEL_ACCESS_TOKEN=你的_channel_access_token
   ```

**步驟 5: 取得 Channel Secret**

1. 在同一頁面中，切換到「Basic settings」分頁
2. 找到「Channel secret」區塊
3. 複製 Channel secret
4. 將 Secret 貼到 `.env` 檔案：
   ```bash
   LINE_CHANNEL_SECRET=你的_channel_secret
   ```

**步驟 6: 設定 Webhook URL**

1. 回到「Messaging API」分頁
2. 找到「Webhook settings」區塊
3. 點擊「Edit」
4. 輸入您的 Webhook URL：
   - **本地測試**：`https://your-ngrok-url.ngrok.io/webhook`
   - **正式部署**：`https://your-domain.com/webhook`
5. 點擊「Update」
6. **啟用「Use webhook」**：將開關切換為「Enabled」

**步驟 7: 啟用自動回覆功能**

1. 在「Messaging API」分頁中
2. 找到「LINE Official Account features」區塊
3. 將「Auto-reply messages」設定為「Disabled」（停用預設自動回覆）
4. 將「Greeting messages」設定為「Disabled」（停用問候訊息）
5. 這樣可以避免與您的 Bot 程式衝突

**步驟 8: 測試 Bot 連線**

1. 在 Channel 設定頁面找到 QR Code
2. 使用 LINE App 掃描 QR Code 加入機器人好友
3. 先不要傳送訊息，等部署完成後再測試

**LINE 設定完成檢查清單**：
- ✅ Provider 已建立
- ✅ Messaging API Channel 已建立
- ✅ Channel Access Token 已取得並設定到 `.env`
- ✅ Channel Secret 已取得並設定到 `.env`
- ✅ Webhook URL 已設定並啟用
- ✅ 自動回覆功能已停用
- ✅ 已加入機器人好友（但先不要測試）

### 6. 本地開發

```bash
# 啟動開發伺服器
python app.py
```

使用 ngrok 進行本地測試：

```bash
# 安裝 ngrok
npm install -g ngrok

# 啟動 ngrok
ngrok http 5000

# 將 ngrok URL 設定到 LINE Bot Webhook
```

## 🚀 快速部署到 Zeabur

> 🎯 **15 分鐘快速部署**: 詳見 [QUICK_START.md](QUICK_START.md)

### ⚡ 一鍵部署（推薦）

```bash
# 1. 自動生成環境變數
python scripts/env-generator.py

# 2. 自動化部署準備
./scripts/zeabur-deploy.sh

# 3. 前往 Zeabur 完成部署
```

### 📋 部署檢查清單

- ✅ **LINE Bot Channel** 已建立（Token + Secret）
- ✅ **Google Sheets** 已建立並設定 Service Account
- ✅ **Zeabur 帳戶** 已註冊並購買方案
- ✅ **GitHub Repository** 已建立

### 🌐 Zeabur 部署步驟

#### 1. 環境準備
```bash
# 生成所有必要的環境變數
python scripts/env-generator.py
```

#### 2. 推送到 GitHub
```bash
# 自動化部署腳本會處理所有檢查和推送
./scripts/zeabur-deploy.sh
```

#### 3. Zeabur 設定
1. 前往 [Zeabur](https://dash.zeabur.com/)
2. **Create Project** → **Deploy from GitHub**
3. 選擇您的 repository
4. 在 **Variables** 中設定環境變數（複製 `.env.zeabur` 檔案內容）
5. 等待部署完成

#### 4. LINE Bot 設定
1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 更新 Webhook URL：`https://your-app.zeabur.app/webhook`
3. 測試連線

### ✅ 驗證部署

```bash
# 健康檢查
curl https://your-app.zeabur.app/health

# 測試 LINE Bot 功能
# 1. 掃描 QR Code 加入好友
# 2. 傳送 "Hello! #測試"
# 3. 檢查 Google Sheets 記錄
```

### 📚 詳細指南

- 🚀 **快速開始**: [QUICK_START.md](QUICK_START.md) - 15 分鐘完成部署
- 📖 **完整指南**: [ZEABUR_DEPLOYMENT.md](ZEABUR_DEPLOYMENT.md) - 詳細步驟說明
- 🔒 **安全指南**: [SECURITY.md](SECURITY.md) - 安全最佳實務
- 🛠️ **通用部署**: [DEPLOYMENT.md](DEPLOYMENT.md) - 多平台部署選項

### 🔧 其他部署選項

<details>
<summary>Docker 部署</summary>

```bash
# 建構映像
docker build -t linebot-inspiration .

# 執行容器
docker run -d \
  --name linebot-app \
  --env-file .env.zeabur \
  -p 5000:5000 \
  linebot-inspiration
```
</details>

<details>
<summary>Heroku 部署</summary>

```bash
# 建立應用程式
heroku create your-app-name

# 設定環境變數（使用 .env.zeabur 內容）
heroku config:set LINE_CHANNEL_ACCESS_TOKEN="your_token"
# ... 其他變數

# 部署
git push heroku main
```
</details>

## 📱 使用指南

### 基本操作

1. **加入好友**：掃描 LINE Bot QR Code
2. **📝 文字記錄**：直接發送文字訊息，立即記錄到 Google Sheets
3. **🎵 語音記錄**：發送語音訊息，自動轉換為文字並記錄
4. **🖼️ 圖片記錄**：發送包含文字的圖片，OCR 自動辨識文字內容
5. **標籤分類**：在訊息中加入 `#工作` `#想法` 等標籤

### 指令功能

| 指令 | 功能 | 範例 |
|------|------|------|
| `/today` 或 `/今日` | 查看今日記錄 | `/today` |
| `/stats` 或 `/統計` | 查看統計資料 | `/stats` |
| `/tags` 或 `/標籤` | 查看標籤統計 | `/tags` |
| `/search 關鍵字` | 搜尋記錄 | `/search 會議` |
| `/help` 或 `/幫助` | 顯示說明 | `/help` |

### 進階功能

#### 標籤系統
在訊息中加入 `#` 符號建立標籤：
```
今天的會議很有收穫 #工作 #會議 #想法
```

#### 🎵 語音轉文字功能
- **多語言支援**：繁體中文、英文、日文
- **智能音訊處理**：自動處理 M4A、MP3、WEBM 等格式
- **自動標點符號**：提升文字可讀性
- **容錯處理**：多重編碼嘗試確保成功率
- **純淨儲存**：Google Sheets 中只儲存轉文字結果，無額外前綴

**使用方式**：
1. 在 LINE 中長按錄音按鈕
2. 錄製您的語音內容
3. 發送後會自動轉為文字並儲存到 Google Sheets
4. Bot 會回覆轉文字結果供確認

#### 🖼️ 圖片轉文字 (OCR) 功能
- **多語言辨識**：繁體中文、簡體中文、英文、日文等
- **多種圖片類型**：截圖、文件照片、手機拍攝、掃描檔案
- **智能文字識別**：印刷字體和清晰手寫字都能識別
- **長文字處理**：自動截斷預覽，完整內容儲存到 Google Sheets

**使用方式**：
1. 拍攝或選擇包含文字的圖片
2. 在 LINE 中發送圖片
3. Bot 自動進行 OCR 文字辨識
4. 辨識結果會顯示預覽並儲存到 Google Sheets

**適用場景**：
- 📄 文件和合約的文字擷取
- 📚 書籍和筆記的內容記錄  
- 🏪 標示和告示的文字保存
- ✍️ 手寫筆記的數位化
- 💻 螢幕截圖的文字提取

## 📊 資料結構

### Google Sheets 欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| timestamp | 記錄時間 | 2024-01-01 12:00:00 |
| message_type | 訊息類型 | text, audio, image |
| content | 訊息內容 | 今天的想法很棒 |
| user_id | 使用者 ID | U1234567890 |
| tags | 標籤列表 | 工作, 想法 |
| status | 處理狀態 | processed |

## 🔧 開發指南

### 專案結構

```
linebot1/
├── server.py                   # 主程式檔案（所有功能整合）
├── requirements.txt            # Python 依賴
├── wsgi.py                    # WSGI 部署入口
├── zeabur.json                # Zeabur 部署設定
├── Procfile                   # 處理程序定義
├── .env.example               # 環境變數範例
├── CLAUDE.md                  # 開發記錄文件
├── README.md                  # 專案說明文件
└── config/                    # 設定檔案目錄
    └── linebot-note-01-xxx.json # Google Service Account 憑證（本機開發用）
```

### 核心技術架構

#### 簡化設計理念
- **單檔案架構**：所有功能整合在 `server.py` 中，便於維護和部署
- **統一認證**：Google Sheets、Speech-to-Text 和 Vision API 使用相同的 Service Account
- **多媒體處理**：完整支援文字、語音、圖片三種訊息類型
- **容錯設計**：多重備援策略和自動格式修復
- **雲端就緒**：無外部系統依賴，純 API 調用，適合容器化部署

#### 核心依賴套件
```bash
flask==3.0.0                    # Web 框架
line-bot-sdk==3.9.0             # LINE Bot 整合
gspread==6.0.0                  # Google Sheets 操作
google-cloud-speech==2.23.0     # 語音轉文字
google-cloud-vision==3.4.4      # 圖片轉文字 OCR
```

### 核心類別

#### MessageModel
處理訊息資料的核心模型：
```python
from app.models.message_model import MessageModel

message = MessageModel(
    user_id="U1234567890",
    message_type="text",
    content="這是一個測試訊息 #測試"
)
```

#### SheetsService
Google Sheets 操作服務：
```python
from app.services.sheets_service import SheetsService

sheets = SheetsService()
sheets.add_message(message)
recent = sheets.get_recent_messages(user_id, days=7)
```

#### SpeechService
語音轉文字服務：
```python
from app.services.speech_service import SpeechService

speech = SpeechService()
result = speech.convert_audio_to_text(audio_url)
```

### 測試

```bash
# 執行所有測試
python -m pytest

# 執行特定測試
python -m pytest tests/test_webhook.py

# 測試覆蓋率
python -m pytest --cov=app
```

### 本地除錯

1. 設定 `FLASK_DEBUG=True`
2. 查看日誌輸出
3. 使用 ngrok 測試 Webhook
4. 檢查 Google Sheets 是否正確更新

## 🔐 安全性

### 資料保護
- LINE Webhook 簽名驗證
- Google Service Account 金鑰加密
- 輸入資料清理和驗證
- 檔案上傳大小限制

### 隱私保護
- 不記錄敏感個人資訊
- 使用 LINE User ID（非個人資料）
- 可隨時刪除個人記錄

## 🐛 故障排除

### 常見問題

#### 1. Webhook 無法接收訊息
- 檢查 LINE Bot Webhook URL 設定
- 確認 SSL 憑證有效
- 檢查防火牆設定

#### 2. Google Sheets 寫入失敗
- 確認 Service Account 權限
- 檢查 Sheets ID 是否正確
- 驗證 API 配額是否用盡

#### 3. 語音轉文字失敗
- 檢查音訊檔案格式
- 確認 Google Cloud Speech API 啟用
- 檢查網路連線狀況

#### 4. 部署失敗
- 檢查 `requirements.txt` 依賴
- 確認環境變數設定
- 檢查部署日誌錯誤訊息

### 日誌檢查

檢查應用程式日誌：
```bash
# 本地開發
tail -f app.log

# Zeabur 部署
# 在控制台查看即時日誌
```

### 健康檢查

訪問健康檢查端點：
```
GET /health
GET /webhook/health
```

## 📈 效能優化

### 建議設定
- 使用 Redis 快取常用資料
- 批次處理 Google Sheets 寫入
- 非同步處理語音轉文字
- 限制並發請求數量

### 監控指標
- 回應時間
- 錯誤率
- API 使用量
- 記憶體使用量

## 🤝 貢獻指南

1. Fork 專案
2. 建立功能分支：`git checkout -b feature/new-feature`
3. 提交變更：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 提交 Pull Request

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 📞 支援與聯絡

- 問題回報：[GitHub Issues](https://github.com/your-username/linebot1/issues)
- 功能建議：[GitHub Discussions](https://github.com/your-username/linebot1/discussions)
- 電子郵件：your-email@example.com

## 🎯 未來規劃

- [ ] OCR 圖片文字識別
- [ ] 情感分析功能
- [ ] 多語言支援擴充
- [ ] Web 管理介面
- [ ] 匯出功能（PDF、Word）
- [ ] 提醒和通知功能
- [ ] 團隊協作功能

---

**享受記錄靈感的樂趣！** ✨