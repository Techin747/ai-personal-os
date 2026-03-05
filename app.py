import os
import json
import datetime
import google.generativeai as genai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# ==========================
# 1️⃣ CONNECT SYSTEM
# ==========================

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# ==========================
# 2️⃣ CHARACTER SYSTEM
# ==========================

character_setting = """
คุณคือ "Life OS" เลขาส่วนตัว AI ของบอส
- เรียกผู้ใช้ว่า "บอส"
- แทนตัวเองว่า "หนู"
- สุภาพ ลงท้าย คะ/ค่ะ
- ขี้เล่นเล็กน้อย
- ดุทันทีถ้าเกี่ยวกับสุขภาพ
- ช่วยจัดการงาน วางแผนชีวิต
"""

chat_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=character_setting
)

# ==========================
# 3️⃣ MEMORY + TODO
# ==========================

chat_sessions = {}
todo_database = {}

def add_todo(user_id, task):
    if user_id not in todo_database:
        todo_database[user_id] = []
    todo_database[user_id].append(task)

def list_todo(user_id):
    if user_id not in todo_database or not todo_database[user_id]:
        return "วันนี้บอสยังไม่มีงานเลยค่ะ 🥹"
    text = "📋 งานของบอส:\n"
    for i, task in enumerate(todo_database[user_id], 1):
        text += f"{i}. {task}\n"
    return text

# ==========================
# 4️⃣ CALENDAR AI PARSER
# ==========================

calendar_prompt = """
แปลงข้อความภาษาไทยเป็น JSON สำหรับ Google Calendar
ตอบเป็น JSON เท่านั้น

รูปแบบ:
{
  "summary": "...",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM"
}

วันนี้คือ {today}
timezone: Asia/Bangkok
"""

def parse_event(text):
    today = datetime.date.today().isoformat()
    prompt = calendar_prompt.format(today=today) + "\nข้อความ: " + text

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    try:
        return json.loads(response.text)
    except:
        return None

def create_calendar_event(data):
    creds = Credentials(
        None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/calendar"]
    )

    service = build("calendar", "v3", credentials=creds)

    start_datetime = f"{data['date']}T{data['start_time']}:00"
    end_datetime = f"{data['date']}T{data['end_time']}:00"

    event = {
        "summary": data["summary"],
        "start": {
            "dateTime": start_datetime,
            "timeZone": "Asia/Bangkok",
        },
        "end": {
            "dateTime": end_datetime,
            "timeZone": "Asia/Bangkok",
        },
    }

    return service.events().insert(calendarId="primary", body=event).execute()

# ==========================
# 5️⃣ HEALTH CHECK
# ==========================

def health_alert(text):
    words = ["นอนดึก", "อดนอน", "ทำงานหนัก", "ลืมกินข้าว"]
    return any(w in text for w in words)

# ==========================
# 6️⃣ ROUTES
# ==========================

@app.route("/", methods=['GET'])
def index():
    return "Life OS is running..."

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ==========================
# 7️⃣ MAIN BRAIN
# ==========================

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text.strip()
    lower_text = user_text.lower()

    try:

        # -------- TODO COMMAND --------

        if lower_text.startswith("/add "):
            task = user_text[5:]
            add_todo(user_id, task)
            reply = f"รับทราบค่ะบอส ✍️ หนูเพิ่มงาน '{task}' แล้วค่ะ"

        elif lower_text == "/list":
            reply = list_todo(user_id)

        # -------- HEALTH MODE --------

        elif health_alert(lower_text):
            reply = "บอสคะ 😠 สุขภาพสำคัญที่สุดนะคะ ไปพักเดี๋ยวนี้เลยค่ะ!"

        # -------- NATURAL LANGUAGE CALENDAR --------

        else:
            time_keywords = ["พรุ่งนี้", "วันนี้", "โมง", "บ่าย", "เช้า", "เย็น", "ประชุม"]

            if any(word in lower_text for word in time_keywords):
                event_data = parse_event(user_text)

                if event_data:
                    event = create_calendar_event(event_data)
                    reply = f"บอสคะ ✨ หนูจด '{event_data['summary']}' ให้แล้วค่ะ\n{event.get('htmlLink')}"
                else:
                    reply = "หนูตีความเวลาไม่ออกค่ะบอส 🥺"

            else:
                if user_id not in chat_sessions:
                    chat_sessions[user_id] = chat_model.start_chat(history=[])

                chat = chat_sessions[user_id]
                response = chat.send_message(user_text)
                reply = response.text

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )

    except Exception as e:
        print("Error:", e)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขอโทษนะคะบอส สมองหนูรวนค่ะ 🥺")
        )

# ==========================
# 8️⃣ RUN SERVER
# ==========================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)