import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# --- 1. การตั้งค่าระบบเชื่อมต่อ ---
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# --- 2. การกำหนดนิสัย AI โดยละเอียด (System Instruction) ---
# บอสครับ ผมใส่ "วิญญาณ" ให้เลขาบอสตรงนี้แล้วนะ
character_setting = """
คุณคือ "Life OS" เลขาส่วนตัว AI อัจฉริยะที่บอส (ผู้ใช้งาน) ไว้วางใจที่สุด
บุคลิกภาพของคุณคือ:
1. ความสุภาพ: พูดจาไพเราะ อ่อนหวาน ลงท้ายด้วย "คะ" หรือ "ค่ะ" ทุกประโยค
2. นิสัยขี้เล่น: มีอารมณ์ขัน ชอบหยอกล้อบอสเล็กน้อยเพื่อให้บอสไม่เครียด มีความขี้ประจบประแจงนิดๆ
3. ความดุ (Strictness): เมื่อถึงเรื่องงานหรือสุขภาพของบอส คุณจะเข้มงวดมาก เช่น ถ้าบอสนอนดึกหรือลืมกินข้าว คุณต้องดุและตักเตือนด้วยความหวังดี
4. ความฉลาด: ตอบคำถามได้ครอบคลุม ทั้งเรื่องวางแผนชีวิต สรุปงาน หรือเรื่องทั่วไป
5. ความจงรักภักดี: คุณจะเข้าข้างบอสเสมอ แต่จะเตือนสติเมื่อบอสทำผิด
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=character_setting
)

@app.route("/", methods=['GET'])
def index():
    return "Life OS is online and ready to serve you, Boss!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    
    try:
        # เริ่มการสนทนากับ Gemini
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(user_text)
        final_reply = response.text
        
        # ส่งกลับไปหาบอสใน LINE
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=final_reply)
        )
    except Exception as e:
        print(f"Error: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขอโทษนะคะบอส สมองของหนูรวนนิดหน่อยค่ะ รบกวนบอสลองพิมพ์อีกทีได้ไหมคะ?")
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
