import os
import requests
from flask import Flask, request, abort

# 引入 LINE Bot SDK
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

# --- 讀取環境變數 ---
# 警告：請確保 Render 上的 KEY 名稱與這裡的字串「完全一致」
try:
    LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
    LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
    CWA_API_KEY = os.environ['CWA_API_KEY']
except KeyError as e:
    # 偵測到環境變數缺失，在日誌中印出明確錯誤
    print(f"錯誤：環境變數 {e} 尚未設定。")
    print("請檢查 Render > Environment 頁面是否已設定所有必要的 KEY。")
    # 讓程式在啟動時就失敗，以便在 Logs 中看到錯誤
    raise ValueError(f"環境變數 {e} 尚未設定")

# --- 初始化 LINE Bot ---
try:
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    handler = WebhookHandler(LINE_CHANNEL_SECRET)
    print("LINE Bot API 和 WebhookHandler 初始化成功。")
except Exception as e:
    print(f"LINE Bot 初始化失敗: {e}")
    raise e

# --- Webhook 路由 ---
# 這是 LINE 傳送訊息來的唯一入口
@app.route("/callback", methods=['POST'])
def callback():
    # 取得 X-Line-Signature 標頭值
    signature = request.headers['X-Line-Signature']
    
    # 取得請求主體 (request body)
    # 關鍵：必須以 as_text=True 取得原始文字
    body = request.get_data(as_text=True)
    
    # 在日誌中印出收到的原始內容 (方便除錯)
    print("--- 收到 LINE Webhook 請求 ---")
    print(f"Request Body: {body}")
    print(f"Signature: {signature}")
    print("-----------------------------")

    # 驗證簽章
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 簽章驗證失敗
        print("簽章驗證失敗 (InvalidSignatureError)！")
        print("請立刻檢查：")
        print("1. Render 上的 'LINE_CHANNEL_SECRET' 是否與 LINE 後台完全一致？")
        print("2. 複製貼上時，是否有多餘的「空白字元」？")
        abort(400) # 回應 400 錯誤
    except Exception as e:
        # 其他錯誤
        print(f"處理訊息時發生未預期的錯誤: {e}")
        abort(500) # 回應 500 錯誤

    return 'OK' # 回應 200 OK

# --- 處理文字訊息 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    reply_token = event.reply_token
    
    print(f"收到來自 {event.source.user_id} 的訊息: {user_message}")

    # 簡單的關鍵字判斷
    if "天氣" in user_message:
        # 嘗試從訊息中提取地名
        location = user_message.replace("天氣", "").strip()
        
        if not location:
            # 如果使用者只說 "天氣"，給予提示
            reply_text = "請告訴我要查詢哪個縣市的天氣喔！\n例如：「臺北天氣」"
        else:
            # 呼叫 CWA API 查詢天氣
            print(f"正在查詢「{location}」的天氣...")
            weather_data = get_cwa_weather(location, CWA_API_KEY)
            reply_text = weather_data
    
    else:
        # 非天氣關鍵字的回應
        reply_text = f"您好！這是一個天氣機器人。\n\n請試著輸入「[縣市名稱]天氣」，例如：「高雄天氣」。"

    # 回傳訊息給使用者
    try:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=reply_text)
        )
        print("成功回覆訊息。")
    except Exception as e:
        print(f"回覆訊息時發生錯誤: {e}")

# --- 輔助函式：呼叫中央氣象署 CWA API ---
def get_cwa_weather(location_name, api_key):
    # 使用 CWA 36小時天氣預報 API
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    
    params = {
        'Authorization': api_key,
        'locationName': location_name,
        'elementName': 'Wx,PoP,MinT,MaxT,CI', # 天氣現象, 降雨機率, 最低溫, 最高溫, 舒適度
        'sort': 'time'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # 如果 API 回傳 4xx or 5xx，觸發錯誤
        data = response.json()

        if not data.get('success'):
            return "氣象局 API 查詢失敗 (success=false)。"

        # 檢查是否找到該地點
        locations = data.get('records', {}).get('location', [])
        if not locations:
            return f"找不到「{location_name}」的天氣資訊。\n\n請確認是臺灣的縣市名稱 (例如：臺北、宜蘭、花蓮...)"

        # 解析資料 (取未來 0-12 小時的預報)
        location_data = locations[0]
        elements = location_data['weatherElement']
        
        time_period = elements[0]['time'][0] # 取得第一個時段的資料
        
        wx = time_period['parameter']['parameterName'] # 天氣現象
        pop = elements[1]['time'][0]['parameter']['parameterName'] # 降雨機率 %
        min_t = elements[2]['time'][0]['parameter']['parameterName'] # 最低溫
        max_t = elements[3]['time'][0]['parameter']['parameterName'] # 最高溫
        ci = elements[4]['time'][0]['parameter']['parameterName'] # 舒適度

        # 組合回傳訊息
        result = (
            f"📍 {location_name} (未來 12 小時)\n"
            f"--------------------\n"
            f"天氣現象：{wx}\n"
            f"降雨機率：{pop} %\n"
            f"溫　　度：{min_t}°C - {max_t}°C\n"
            f"舒適程度：{ci}"
        )
        return result

    except requests.exceptions.RequestException as e:
        print(f"CWA API 請求失敗: {e}")
        return "很抱歉，連線到氣象局時發生錯誤。"
    except (KeyError, IndexError, TypeError) as e:
        print(f"解析 CWA API 資料失敗: {e}")
        print(f"收到的資料: {data}")
        return "很抱歉，解析氣象局資料時發生錯誤。"

# --- 啟動伺服器 ---
if __name__ == "__main__":
    # Render 會使用 Gunicorn 執行，不會跑到這一段
    # 這一段是留給 "本機" 測試 (e.g. python app.py) 用的
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
