import os
import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# -----------------------------
# 1. เชื่อมต่อระบบ
# -----------------------------

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# -----------------------------
# 2. ตั้งค่านิสัย Life OS
# -----------------------------

character_setting = """
คุณคือ "Life OS" เลขาส่วนตัว AI อัจฉริยะของบอส

บุคลิกภาพ:
- เรียกผู้ใช้ว่า "บอส"
- แทนตัวเองว่า "หนู"
- สุภาพ ลงท้ายด้วย คะ/ค่ะ
- มีความขี้เล่น อ่อนหวาน
- ถ้าเกี่ยวกับสุขภาพให้ดุจริงจัง
- พร้อมช่วยวางแผนชีวิตและสรุปงาน
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=character_setting
)

# -----------------------------
# 3. Memory System
# -----------------------------

chat_sessions = {}

# -----------------------------
# 4. ระบบ To-do
# -----------------------------

todo_database = {}

def add_todo(user_id, task):
    if user_id not in todo_database:
        todo_database[user_id] = []
    todo_database[user_id].append({
        "task": task,
        "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    })

def list_todo(user_id):
    if user_id not in todo_database or not todo_database[user_id]:
        return "วันนี้บอสยังไม่มีงานเลยค่ะ 🥹"

    text = "📋 งานของบอส:\n"
    for i, item in enumerate(todo_database[user_id], 1):
        text += f"{i}. {item['task']} (เพิ่มเมื่อ {item['created']})\n"
    return text

def clear_todo(user_id):
    todo_database[user_id] = []

def remove_todo(user_id, index):
    if user_id in todo_database and 0 <= index < len(todo_database[user_id]):
        todo_database[user_id].pop(index)
        return True
    return False

# -----------------------------
# 5. Health Strict Mode
# -----------------------------

def health_check(text):
    keywords = ["นอนดึก", "อดนอน", "ทำงานหนัก", "ลืมกินข้าว", "ไม่พัก"]
    for word in keywords:
        if word in text:
            return True
    return False

# -----------------------------
# 6. Routes
# -----------------------------

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

# -----------------------------
# 7. Main Brain
# -----------------------------

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text.strip()
    lower_text = user_text.lower()

    try:

        # -------- Special Commands --------

        if lower_text.startswith("/add "):
            task = user_text[5:]
            add_todo(user_id, task)
            reply = f"รับทราบค่ะบอส ✍️ หนูเพิ่มงาน '{task}' แล้วนะคะ"

        elif lower_text == "/list":
            reply = list_todo(user_id)

        elif lower_text.startswith("/remove "):
            try:
                index = int(lower_text.replace("/remove ", "")) - 1
                if remove_todo(user_id, index):
                    reply = "หนูลบงานให้แล้วค่ะบอส ✨"
                else:
                    reply = "ลำดับไม่ถูกต้องนะคะบอส 🥺"
            except:
                reply = "บอสพิมพ์ลำดับงานไม่ถูกต้องค่ะ"

        elif lower_text == "/clear":
            clear_todo(user_id)
            reply = "หนูล้างงานทั้งหมดแล้วค่ะบอส ✨"

        elif lower_text == "/today":
            today = datetime.datetime.now().strftime("%A %d %B %Y")
            reply = f"วันนี้คือ {today} ค่ะบอส 🌤️\n" + list_todo(user_id)

        # -------- Health Strict Mode --------

        elif health_check(lower_text):
            reply = "บอสคะ 😠 สุขภาพสำคัญที่สุดนะคะ! ไปพักเดี๋ยวนี้เลยค่ะ!"

        # -------- AI Chat Mode --------

        else:
            if user_id not in chat_sessions:
                chat_sessions[user_id] = model.start_chat(history=[])

            chat = chat_sessions[user_id]
            response = chat.send_message(user_text)
            reply = response.text

        # -------- Reply --------

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )

    except Exception as e:
        print("Error:", e)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขอโทษนะคะบอส สมองหนูรวนนิดหน่อย 🥺")
        )

# -----------------------------
# 8. Run Server
# -----------------------------

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)