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
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [{"role": "user", "content": message}]
    }
    res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                        headers=headers, json=data)
    return res.json()["choices"][0]["message"]["content"]

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
