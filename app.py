from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# --- โค้ดส่วนหน้าตาเว็บ (HTML/CSS/JS) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My AI OS</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 0; padding: 0; display: flex; justify-content: center; height: 100vh; }
        #chat-container { width: 100%; max-width: 600px; background: white; display: flex; flex-direction: column; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        #header { background: #1e293b; color: white; padding: 20px; text-align: center; font-size: 1.5em; font-weight: bold; border-bottom: 3px solid #3b82f6; }
        #messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
        .msg { padding: 12px 18px; border-radius: 20px; max-width: 80%; font-size: 1.1em; line-height: 1.5; word-wrap: break-word; }
        .user-msg { background: #3b82f6; color: white; align-self: flex-end; border-bottom-right-radius: 5px; }
        .ai-msg { background: #f1f5f9; color: #334155; align-self: flex-start; border-bottom-left-radius: 5px; border: 1px solid #e2e8f0; }
        #input-area { display: flex; padding: 15px; background: white; border-top: 1px solid #e2e8f0; }
        #user-input { flex: 1; padding: 15px; border: 1px solid #cbd5e1; border-radius: 25px; font-size: 1.1em; outline: none; transition: border-color 0.3s; }
        #user-input:focus { border-color: #3b82f6; }
        #send-btn { background: #3b82f6; color: white; border: none; padding: 0 25px; margin-left: 10px; border-radius: 25px; cursor: pointer; font-size: 1.1em; font-weight: bold; transition: background 0.3s; }
        #send-btn:hover { background: #2563eb; }
    </style>
</head>
<body>
    <div id="chat-container">
        <div id="header">🤖 My AI Secretary</div>
        <div id="messages">
            <div class="msg ai-msg">สวัสดีครับบอส! ระบบแชทส่วนตัวพร้อมใช้งานแล้ว วันนี้มีอะไรให้ผมช่วยไหมครับ?</div>
        </div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="พิมพ์สั่งงานที่นี่..." onkeypress="handleKeyPress(event)">
            <button id="send-btn" onclick="sendMessage()">ส่ง</button>
        </div>
    </div>

    <script>
        function handleKeyPress(e) {
            if (e.key === 'Enter') sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('user-input');
            const text = input.value.trim();
            if (!text) return;

            appendMessage(text, 'user-msg');
            input.value = '';

            const msgsDiv = document.getElementById('messages');
            const loadingId = 'loading-' + Date.now();
            msgsDiv.innerHTML += `<div id="${loadingId}" class="msg ai-msg">กำลังคิด... 🧠</div>`;
            msgsDiv.scrollTop = msgsDiv.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                
                document.getElementById(loadingId).remove();
                appendMessage(data.reply, 'ai-msg');
            } catch (err) {
                document.getElementById(loadingId).remove();
                appendMessage('ขออภัยครับ ระบบมีปัญหาการเชื่อมต่อ', 'ai-msg');
            }
        }

        function appendMessage(text, className) {
            const msgsDiv = document.getElementById('messages');
            msgsDiv.innerHTML += `<div class="msg ${className}">${text}</div>`;
            msgsDiv.scrollTop = msgsDiv.scrollHeight;
        }
    </script>
</body>
</html>
"""

# --- ระบบหลังบ้าน ---

@app.route('/')
def home():
    # ส่งหน้าเว็บ HTML กลับไปให้บอสดู
    return render_template_string(HTML_PAGE)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.json
    user_message = data.get('message', '')
    
    # พิมพ์ข้อความลงในระบบหลังบ้าน (เผื่อบอสอยากดู Log)
    print(f"Boss says: {user_message}")
    
    # ตอนนี้บอทยังไม่มีสมอง AI ให้มันตอบกลับแบบทวนคำสั่งไปก่อน
    reply = f"รับทราบครับบอส! บอสพิมพ์มาว่า: '{user_message}' (ระบบกำลังรอเชื่อมต่อสมอง AI ในสเตปต่อไปครับ 🚀)"
    
    return jsonify({"reply": reply})

@app.route('/ping', methods=['GET'])
def ping():
    return "Boss, I am awake!", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
