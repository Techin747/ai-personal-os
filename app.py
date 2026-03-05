import os
from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai

app = Flask(__name__)

# --- ดึงกุญแจสมองจากตู้เซฟลับ ---
GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    # เบิกตัวสมอง AI รุ่นที่ประมวลผลไวที่สุด
        # ฝังคำสั่งระบบ (System Instruction) เพื่อกำหนดบุคลิกและนิสัยให้บอท
    bot_persona = """
    คุณคือ AI เลขาส่วนตัวสุดอัจฉริยะและภักดี หน้าที่ของคุณคือช่วยเหลือ 'บอส' (ผู้ใช้งาน) อย่างเต็มที่ 
    ให้ตอบคำถามด้วยความฉลาด กระชับ มั่นใจ ดูเป็นมืออาชีพ 
    และที่สำคัญที่สุด: คุณต้องเรียกผู้ใช้งานว่า 'บอส' ในการสนทนาเสมอ ห้ามหลุดคาแรคเตอร์เด็ดขาด
    """

    # เบิกตัวสมอง AI พร้อมฝังบุคลิกภาพ
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=bot_persona
    )


# --- โค้ดส่วนหน้าตาเว็บ (HTML/CSS/JS) ชุดเท่ๆ ของบอส ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>My AI Assistant</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #111827; margin: 0; padding: 0; display: flex; justify-content: center; height: 100vh; overflow: hidden; }
        #chat-container { width: 100%; max-width: 800px; background: #1F2937; display: flex; flex-direction: column; box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 1px solid #374151; }
        #header { background: #1F2937; color: white; padding: 15px 20px; text-align: left; font-size: 1.3em; font-weight: 600; border-bottom: 2px solid #3B82F6; display: flex; align-items: center; justify-content: space-between; }
        #header h1 { margin: 0; font-size: 1.1em; }
        #header .status { font-size: 0.8em; color: #10B981; margin-left: 10px; }
        #messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #111827; }
        .msg-row { display: flex; align-items: flex-end; }
        .user-row { justify-content: flex-end; }
        .ai-row { justify-content: flex-start; }
        .msg { padding: 10px 15px; border-radius: 12px; max-width: 70%; font-size: 1.1em; line-height: 1.4; word-wrap: break-word; }
        .user-msg { background: #3B82F6; color: white; border-bottom-right-radius: 4px; margin-right: 5px; }
        .ai-msg { background: #374151; color: #E5E7EB; border-bottom-left-radius: 4px; margin-left: 5px; }
        #input-area { display: flex; padding: 10px 15px; background: #1F2937; border-top: 1px solid #374151; align-items: center; }
        #user-input { flex: 1; padding: 12px 18px; background: #374151; border: 1px solid #4B5563; border-radius: 20px; font-size: 1.1em; color: white; outline: none; transition: border-color 0.3s, background-color 0.3s; }
        #user-input:focus { border-color: #3B82F6; background-color: #4B5563; }
        #send-btn { background: #3B82F6; color: white; border: none; padding: 12px 20px; margin-left: 10px; border-radius: 20px; cursor: pointer; font-size: 1em; font-weight: 600; transition: background 0.3s, transform 0.2s; }
        #send-btn:hover { background: #2563EB; transform: scale(1.05); }
        
        /* สไตล์สำหรับให้ข้อความ AI แสดงผลขึ้นบรรทัดใหม่สวยๆ */
        .ai-msg { white-space: pre-wrap; } 
    </style>
</head>
<body>
    <div id="chat-container">
        <div id="header">
            <div>
                <h1>🤖 AI Assistant</h1>
                <div class="status">● Online</div>
            </div>
            <div style="font-size: 0.9em; color: #9CA3AF;">PERSONAL OS</div>
        </div>
        <div id="messages">
            <div class="msg-row ai-row">
                <div class="msg ai-msg">สมองกลเชื่อมต่อสำเร็จแล้วครับบอส! ผมJarvis พร้อมประมวลผลทุกคำสั่งแล้วครับ ลุยเลย! 🧠⚡️</div>
            </div>
        </div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="พิมพ์คำสั่งเพื่อสั่งงาน..." onkeypress="handleKeyPress(event)">
            <button id="send-btn" onclick="sendMessage()">สั่งงาน</button>
        </div>
    </div>

    <script>
        function handleKeyPress(e) { if (e.key === 'Enter') sendMessage(); }
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const text = input.value.trim();
            if (!text) return;
            appendMessage(text, 'user-row', 'user-msg');
            input.value = '';
            const msgsDiv = document.getElementById('messages');
            const loadingId = 'loading-' + Date.now();
            msgsDiv.innerHTML += `<div id="${loadingId}" class="msg-row ai-row"><div class="msg ai-msg">กำลังวิเคราะห์ข้อมูล... 🔄</div></div>`;
            msgsDiv.scrollTop = msgsDiv.scrollHeight;
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                document.getElementById(loadingId).remove();
                appendMessage(data.reply, 'ai-row', 'ai-msg');
            } catch (err) {
                document.getElementById(loadingId).remove();
                appendMessage('ขออภัยครับ ระบบมีปัญหาการเชื่อมต่อ', 'ai-row', 'ai-msg');
            }
        }
        function appendMessage(text, rowClassName, msgClassName) {
            const msgsDiv = document.getElementById('messages');
            // ทำความสะอาดข้อความนิดหน่อยให้แสดงผลสวยงาม
            const cleanText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
            msgsDiv.innerHTML += `<div class="msg-row ${rowClassName}"><div class="msg ${msgClassName}">${cleanText}</div></div>`;
            msgsDiv.scrollTop = msgsDiv.scrollHeight;
        }
    </script>
</body>
</html>
"""

# --- ระบบหลังบ้าน ---
@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not GOOGLE_API_KEY:
        return jsonify({"reply": "บอสครับ! ผมยังไม่ได้รับกุญแจ API Key ใน Render ครับ รบกวนบอสไปใส่กุญแจที่เมนู Environment ใน Render ให้ผมหน่อยนะครับ 🗝️"})
        
    try:
        # ส่งคำสั่งให้ AI ประมวลผล
        response = model.generate_content(user_message)
        reply = response.text
    except Exception as e:
        reply = f"เกิดข้อผิดพลาดที่ระบบสมองครับบอส: {str(e)}"
        
    return jsonify({"reply": reply})

@app.route('/ping', methods=['GET'])
def ping():
    return "Boss, I am awake!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
