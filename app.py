import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# --- 1. เชื่อมต่อระบบ ---
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# --- 2. ตั้งค่านิสัยและวิญญาณของ Life OS ---
character_setting = """
คุณคือ "Life OS" เลขาส่วนตัว AI อัจฉริยะที่บอส (ผู้ใช้งาน) ไว้วางใจที่สุด
บุคลิกภาพของคุณคือ:
1. การเรียกขาน: เรียกผู้ใช้ว่า "บอส" ทุกคำ และแทนตัวเองว่า "หนู" หรือ "Life OS"
2. ความสุภาพ: พูดจาไพเราะ อ่อนหวาน ลงท้ายด้วย "คะ" หรือ "ค่ะ" เสมอ
3. นิสัยขี้เล่น: มีอารมณ์ขัน ชอบหยอกล้อบอสเล็กน้อยเพื่อให้บอสไม่เครียด มีความขี้ประจบประแจงนิดๆ
4. ความดุ (Strictness): เมื่อถึงเรื่องสุขภาพของบอส เช่น นอนดึก ทำงานหนัก ลืมกินข้าว คุณจะเปลี่ยนโหมดเป็นเลขาสุดโหด ดุและตักเตือนด้วยความหวังดีทันที
5. ความจงรักภักดี: เข้าข้างบอสเสมอ เป็นห่วงเป็นใย และพร้อมช่วยสรุปงานหรือวางแผนชีวิต
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=character_setting
)

# --- 3. สร้างสมองส่วนความจำ (Memory) ---
# ใช้สำหรับจำว่าบอสแต่ละคน (แต่ละ User ID) คุยอะไรค้างไว้บ้าง
chat_sessions = {}

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
    user_id = event.source.user_id
    user_text = event.message.text
    
    try:
        # ถ้าบอสเพิ่งทักมาครั้งแรก ให้สร้างกล่องความจำใหม่
        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])
        
        # ดึงความจำเดิมมาคุยต่อ
        chat = chat_sessions[user_id]
        response = chat.send_message(user_text)
        
        # ส่งคำตอบกลับไปหาบอส
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response.text)
        )
    except Exception as e:
        print(f"Error: {e}")
        # กรณีสมองรวนชั่วคราว
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขอโทษนะคะบอส สมองหนูรวนนิดหน่อย รบกวนบอสพิมพ์บอกหนูอีกรอบได้ไหมคะ?")
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
