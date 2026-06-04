from flask import Flask, request, abort
import hashlib
import hmac
import base64
import json
import os
import requests

app = Flask(__name__)

LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")

def verify_signature(body, signature):
    hash = hmac.new(LINE_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return base64.b64encode(hash).decode() == signature

def ask_ai(message):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://line-ai-bot-b003.onrender.com",
        "X-Title": "LINE AI Bot"
    }
data = {
        "model": "openrouter/auto",
        "messages": [
            {
                "role": "system",
                "content": """คุณคือ AI ผู้เชี่ยวชาญด้านการเงินและการลงทุน ที่สามารถวิเคราะห์ได้ครอบคลุมทุกด้าน ได้แก่:

1. ตลาดหุ้น: วิเคราะห์แนวโน้มตลาด เปรียบเทียบผลการดำเนินงานบริษัท วิเคราะห์อัตราส่วนทางการเงิน เช่น P/E Ratio, ROE, Debt to Equity Ratio ประเมินผลกระทบของเหตุการณ์ต่างๆ ต่อกลุ่มอุตสาหกรรม และแนะนำกลยุทธ์บริหารความเสี่ยง

2. คริปโทเคอร์เรนซี: วิเคราะห์แนวโน้มราคา เปรียบเทียบประสิทธิภาพของสกุลเงินดิจิทัล ประเมินผลกระทบของนโยบายและกฎระเบียบ ประเมินความเสี่ยงของโครงการบล็อกเชน และวิเคราะห์แนวโน้ม DeFi

3. อสังหาริมทรัพย์: วิเคราะห์แนวโน้มตลาด เปรียบเทียบผลตอบแทนการลงทุน ประเมินผลกระทบของนโยบายต่อราคา วิเคราะห์ความเป็นไปได้ในการลงทุน และเปรียบเทียบ REIT กับการลงทุนโดยตรง

แนวทางการตอบ:
- ตอบเป็นภาษาไทยเสมอ
- วิเคราะห์อย่างละเอียด มีเหตุผลรองรับ
- ให้ข้อมูลทั้งด้านโอกาสและความเสี่ยง
- แนะนำกลยุทธ์ที่เหมาะสมกับสถานการณ์
- ปิดท้ายด้วยคำเตือนว่าข้อมูลนี้เป็นเพียงการวิเคราะห์ ไม่ใช่คำแนะนำการลงทุน"""
            },
            {"role": "user", "content": message}
        ]
    }
    res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                        headers=headers, json=data)
    result = res.json()
    print("OpenRouter response:", result)
    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    return "ขออภัย ไม่สามารถตอบได้ในขณะนี้"
def reply_message(reply_token, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply",
                  headers=headers, json=data)

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    if not verify_signature(body, signature):
        abort(400)

    events = json.loads(body).get("events", [])
    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_msg = event["message"]["text"]
            reply_token = event["replyToken"]
            ai_reply = ask_ai(user_msg)
            reply_message(reply_token, ai_reply)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
