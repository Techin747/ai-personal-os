from flask import Flask, request, jsonify

app = Flask(__name__)

# 1. ระบบกันบอทหลับ (Anti-Sleep)
@app.route('/ping', methods=['GET'])
def ping():
    return "Boss, I am awake and ready!", 200

# 2. ระบบรับคำสั่ง (Webhook)
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received message from Boss:", data)
    return jsonify({"status": "received", "message": "Roger that!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
