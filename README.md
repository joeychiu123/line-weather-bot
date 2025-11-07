# LINE 天氣查詢 Bot

一個可以查詢台灣各縣市未來一週天氣預報的 LINE Bot。

## 功能特色

- 🌤️ 支援台灣所有縣市天氣查詢
- 📅 提供未來一週（14個時段）天氣預報
- 🌡️ 顯示最高溫、最低溫、天氣狀況、降雨機率
- 💬 快速回覆按鈕，方便選擇縣市
- 🎨 使用 emoji 圖示，視覺化天氣狀態

## 使用方式

1. 加入 LINE Bot 好友：`@469voixi`
2. 傳送「天氣」給 Bot
3. 點選想查詢的縣市
4. 立即收到該縣市未來一週天氣預報！

## 部署到 Render（免費）

### 步驟一：準備 GitHub Repository

1. 前往 https://github.com 並登入
2. 點選右上角「+」→「New repository」
3. Repository 名稱：`line-weather-bot`
4. 設為「Public」
5. 點選「Create repository」

### 步驟二：上傳程式碼到 GitHub

有兩種方式：

**方式 A：使用 GitHub 網頁介面上傳**

1. 在您的 Repository 頁面，點選「uploading an existing file」
2. 將以下檔案拖曳上傳：
   - `app.py`
   - `requirements.txt`
   - `README.md`
3. 點選「Commit changes」

**方式 B：使用 Git 指令（進階）**

```bash
# 在本地資料夾執行
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/line-weather-bot.git
git push -u origin main
```

### 步驟三：在 Render 建立 Web Service

1. 前往 https://render.com/ 並註冊/登入
2. 點選「New +」→「Web Service」
3. 連結您的 GitHub 帳號
4. 選擇 `line-weather-bot` repository
5. 設定以下資訊：
   - **Name**: `line-weather-bot`（或任何您喜歡的名稱）
   - **Region**: Singapore（最接近台灣）
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`

### 步驟四：設定環境變數

在 Render 的設定頁面，點選「Environment」分頁，新增以下環境變數：

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_ACCESS_TOKEN` | 您的 LINE Channel Access Token |
| `LINE_CHANNEL_SECRET` | 您的 LINE Channel Secret |
| `CWA_API_KEY` | 您的中央氣象署 API 授權碼 |
| `PORT` | `10000` |

設定完成後，點選「Save Changes」。

### 步驟五：部署

1. Render 會自動開始部署
2. 等待約 3-5 分鐘
3. 部署完成後，您會看到一個網址，例如：
   ```
   https://line-weather-bot-xxxx.onrender.com
   ```
4. 複製這個網址

### 步驟六：設定 LINE Webhook URL

1. 回到 LINE Developers Console
2. 選擇您的 Channel → Messaging API
3. 在「Webhook URL」欄位填入：
   ```
   https://line-weather-bot-xxxx.onrender.com/callback
   ```
   （記得加上 `/callback`）
4. 點選「Update」
5. 點選「Verify」測試連線
6. 確認「Use webhook」是「Enabled」狀態

### 步驟七：測試 Bot

1. 用手機掃描 QR Code 加入 Bot 好友（@469voixi）
2. 傳送「天氣」給 Bot
3. 點選縣市
4. 查看天氣預報！🎉

## 常見問題

### Q1: Render 部署失敗怎麼辦？

檢查以下項目：
- 確認 `requirements.txt` 檔案存在且格式正確
- 檢查環境變數是否都已正確設定
- 查看 Render 的 Logs 了解錯誤訊息

### Q2: Bot 沒有回應？

檢查以下項目：
- Webhook URL 是否正確設定並加上 `/callback`
- 環境變數是否都正確填入
- 在 LINE Official Account Manager 確認：
  - Webhook：已啟用
  - 自動回應訊息：已停用
  - 加入好友的歡迎訊息：已停用

### Q3: 天氣資料查詢失敗？

- 確認中央氣象署 API 授權碼是否正確
- 檢查 API 呼叫次數是否超過限制（免費版有次數限制）

### Q4: Render 免費方案的限制？

- 閒置 15 分鐘後會進入睡眠模式
- 首次喚醒可能需要等待 30 秒
- 每月有 750 小時的免費使用時間（足夠個人使用）

## 技術架構

- **後端框架**: Flask
- **LINE SDK**: line-bot-sdk
- **天氣資料來源**: 中央氣象署開放資料平台
- **部署平台**: Render
- **程式語言**: Python 3

## 作者

JOEY

## 授權

MIT License
