from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import requests
from datetime import datetime
import os

app = Flask(__name__)

# ========== 環境變數設定 ==========
# 請在 Render 的環境變數中設定這些值
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
CWA_API_KEY = os.environ.get('CWA_API_KEY')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ========== 台灣縣市列表 ==========
TAIWAN_CITIES = [
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市",
    "基隆市", "新竹市", "嘉義市", "新竹縣", "苗栗縣", "彰化縣",
    "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
    "臺東縣", "澎湖縣", "金門縣", "連江縣"
]

# ========== 天氣查詢函式 ==========

def get_weather_forecast(city="臺南市"):
    """取得指定縣市的天氣預報"""
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"
    
    params = {
        "Authorization": CWA_API_KEY,
        "locationName": city,
        "elementName": "MinT,MaxT,Wx,PoP12h"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get('success') == 'true':
            return parse_weather_data(data, city)
        else:
            error_msg = data.get('message', '未知錯誤')
            return f"❌ API 查詢失敗：{error_msg}"
    
    except requests.exceptions.Timeout:
        return "❌ 查詢逾時，請稍後再試"
    except Exception as e:
        return f"❌ 發生錯誤：{str(e)}"


def parse_weather_data(data, city):
    """解析天氣資料並格式化"""
    try:
        locations = data.get('records', {}).get('locations', [])
        if not locations:
            return f"❌ 找不到 {city} 的天氣資料"
        
        location = locations[0].get('location', [])
        if not location:
            return f"❌ {city} 資料格式錯誤"
        
        weather_elements = location[0].get('weatherElement', [])
        
        # 整理資料
        weather_info = {}
        for element in weather_elements:
            element_name = element['elementName']
            weather_info[element_name] = element['time']
        
        # 建立訊息
        message = f"☀️ {city} 未來一週天氣\n"
        message += f"📅 查詢時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        message += "=" * 25 + "\n\n"
        
        # 取前14筆資料（約7天，每12小時一筆）
        num_forecasts = min(14, len(weather_info.get('Wx', [])))
        
        for i in range(num_forecasts):
            if i >= len(weather_info['Wx']):
                break
                
            start_time = weather_info['Wx'][i]['startTime']
            date_obj = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            # 格式化日期時間
            weekday = ['一', '二', '三', '四', '五', '六', '日'][date_obj.weekday()]
            date_str = date_obj.strftime(f'%m/%d({weekday}) %H:%M')
            
            wx = weather_info['Wx'][i]['elementValue'][0]['value']
            min_t = weather_info['MinT'][i]['elementValue'][0]['value']
            max_t = weather_info['MaxT'][i]['elementValue'][0]['value']
            pop = weather_info['PoP12h'][i]['elementValue'][0]['value']
            
            # 選擇天氣圖示
            weather_icon = get_weather_icon(wx)
            
            message += f"📆 {date_str}\n"
            message += f"{weather_icon} {wx}\n"
            message += f"🌡️ {min_t}°C ~ {max_t}°C\n"
            message += f"💧 降雨 {pop}%\n"
            message += "-" * 20 + "\n"
        
        return message
        
    except Exception as e:
        return f"❌ 資料解析錯誤：{str(e)}"


def get_weather_icon(weather_desc):
    """根據天氣描述回傳對應的 emoji"""
    if "晴" in weather_desc:
        return "☀️"
    elif "雨" in weather_desc:
        return "🌧️"
    elif "雲" in weather_desc or "陰" in weather_desc:
        return "☁️"
    elif "雷" in weather_desc:
        return "⛈️"
    else:
        return "🌤️"


# ========== LINE Bot Webhook ==========

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhook 接收訊息"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理使用者訊息"""
    user_message = event.message.text.strip()
    
    # 判斷使用者輸入
    if user_message in ["天氣", "查天氣", "weather"]:
        # 顯示縣市快速選單
        quick_reply_buttons = []
        for city in TAIWAN_CITIES[:13]:  # LINE 快速回覆最多 13 個選項
            quick_reply_buttons.append(
                QuickReplyButton(
                    action=MessageAction(label=city, text=city)
                )
            )
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請選擇要查詢的縣市：",
                quick_reply=QuickReply(items=quick_reply_buttons)
            )
        )
    
    elif user_message in TAIWAN_CITIES:
        # 查詢該縣市天氣
        weather_info = get_weather_forecast(user_message)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=weather_info)
        )
    
    else:
        # 預設回應
        help_text = (
            "🌤️ 天氣查詢小幫手\n\n"
            "請輸入「天氣」來查詢天氣預報\n\n"
            "📍 支援台灣所有縣市\n"
            "📅 提供未來一週預報\n"
            "🌡️ 包含溫度、天氣、降雨機率"
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text)
        )


# ========== 健康檢查端點 ==========

@app.route("/", methods=['GET'])
def health_check():
    """健康檢查端點"""
    return "LINE Weather Bot is running! 🌤️"


# ========== 啟動伺服器 ==========

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
