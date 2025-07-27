# 🔧 Zeabur Permission Denied 解決方案

## ❌ 問題原因
您的 GitHub repository `blueforster/linebot-inspiration` 目前是 **Private**（私有），Zeabur 無法存取私有 repository，因此出現 Permission denied 錯誤。

## ✅ 解決方案

### 方法 1：將 Repository 設為 Public（推薦）

1. **前往 GitHub Repository**：
   https://github.com/blueforster/linebot-inspiration

2. **進入設定**：
   - 點擊 **"Settings"** 分頁
   - 滾動到最下方的 **"Danger Zone"**

3. **變更可見性**：
   - 點擊 **"Change repository visibility"**
   - 選擇 **"Make public"**
   - 輸入 repository 名稱確認：`blueforster/linebot-inspiration`
   - 點擊 **"I understand, make this repository public"**

4. **重新在 Zeabur 部署**：
   - 前往 Zeabur Dashboard
   - Create Project → Deploy from GitHub
   - 現在應該可以成功找到並匯入您的 repository

### 方法 2：在 Zeabur 中授權 GitHub 存取（如果要保持私有）

如果您希望保持 repository 為私有：

1. **檢查 Zeabur GitHub 整合**：
   - 在 Zeabur Dashboard 中，前往 Settings
   - 確認 GitHub 整合已正確設定
   - 重新授權 GitHub 存取權限

2. **GitHub App 權限**：
   - 確保 Zeabur GitHub App 有存取私有 repository 的權限
   - 前往 GitHub Settings > Applications > Installed GitHub Apps
   - 找到 Zeabur 並確認權限設定

## 🎯 推薦做法

**建議使用方法 1（設為 Public）**，因為：

✅ **安全性無虞**：
- 所有敏感資訊（API keys、憑證）都已在 `.gitignore` 中排除
- 實際的敏感資料通過環境變數在 Zeabur 中設定
- 程式碼本身不包含任何機密資訊

✅ **部署更簡單**：
- Zeabur 可以直接存取 public repository
- 不需要處理複雜的權限設定
- 自動 CI/CD 更容易設定

✅ **便於維護**：
- GitHub Actions 可以正常運作
- 其他協作者更容易存取
- 便於分享和展示專案

## 📋 設為 Public 後的檢查清單

設為 Public 後，請確認：

□ `.gitignore` 正確排除所有敏感檔案
□ `.env` 檔案未被推送到 GitHub
□ `config/google-credentials.json` 未被推送到 GitHub
□ GitHub repository 中沒有任何 API keys 或 tokens

## 🚀 完成後續步驟

Repository 設為 Public 後：

1. **重新部署到 Zeabur**：
   - Create Project → Deploy from GitHub
   - 選擇 `blueforster/linebot-inspiration`

2. **設定環境變數**：
   - 使用準備好的 `.env.zeabur` 檔案內容

3. **更新 LINE Bot Webhook**：
   - 使用 Zeabur 提供的 URL

---

**注意**：將 repository 設為 public 是完全安全的，因為我們已經確保所有敏感資訊都通過環境變數安全地傳遞，而不是存儲在程式碼中。