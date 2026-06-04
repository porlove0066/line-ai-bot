from flask import Flask, request, abort
import hashlib
import hmac
import base64
import json
import os
import requests
import google.generativeai as genai

app = Flask(__name__)

LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def verify_signature(body, signature):
    hash = hmac.new(LINE_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return base64.b64encode(hash).decode() == signature

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
            response = model.generate_content(user_msg)
            reply_message(reply_token, response.text)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
