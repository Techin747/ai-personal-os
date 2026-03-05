import os
import sys
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# 1. ตั้งค่ากุญแจลับ (ดึงจาก Environment Variables ที่บอสใส่ใน Render)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# 2. ตั้งค่าบุคลิกของ Life OS (System Instruction)
instruction = "คุณคือ Life OS เลขาส่วนตัวที่ฉลาด ขี้เล่นแต่แอบดุ และซื่อสัตย์มาก พูดจาสุภาพลงท้ายด้วย คะ/ค่ะ เสมอ ทำหน้าที่จัดการตารางงานและตอบคำถามอย่างมืออาชีพ"
model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)

@app.route("/", methods=['GET'])
def index():
    return "Life OS is running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    try:
        # ส่งข้อความไปถาม Gemini AI
        chat = model.start_chat(history=[])
        response = chat.send_message(user_message)
        ai_reply = response.text
        
        # ส่งคำตอบกลับไปที่ LINE
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
    except Exception as e:
        app.logger.error(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขออภัยค่ะบอส เกิดข้อผิดพลาดในสมองนิดหน่อย ลองใหม่อีกครั้งนะคะ")
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
