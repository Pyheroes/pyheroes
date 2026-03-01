from db import connection, cursor, set_user_name, get_user_name, set_user_state, get_user_state, token, group_id, table
from flask import Flask, request, render_template, redirect, send_from_directory, jsonify
import requests
import time
import threading
import os
import db
import sqlite3 as sq


Telegram_API = f"https://api.telegram.org/bot{token}"

state_idle = "idle"
payer_id = 0

app = Flask(__name__, static_folder="webapp")


@app.route('/api/payment-intent', methods=['POST'])
def handle_intent():
    try:
        data = request.json
        email = data.get('email', 'Unknown Email')
        name = data.get('name', 'Interested Student')
        status = data.get('status', 'clicked')
        
        print(f"--- INTENT RECEIVED ---")
        print(f"User: {name} ({email}) | Action: {status}")
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        app.logger.error(f"Error in intent route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/payment-success', methods=['POST'])
def handle_success():
    try:
        data = request.json
        email = data.get('email', 'Unknown Email')
        ref = data.get('reference', 'No Ref')
        
        print(f"--- SUCCESS RECEIVED ---")
        print(f"User: {email} | Reference: {ref}")
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        app.logger.error(f"Error in success route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/webhook", methods = ["POST"])
def webhook():
    update = request.get_json()
    process_update(update)
    return "OK"

def process_update(update):
    """Internal function to handle both Webhook and Polling updates"""
    global payer_id
    table()
    
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        payer_id = chat_id
        text = message.get("text", "")
        
        if text == "/start":
            set_user_state(chat_id, "WAITING_NAME")
            send_message(chat_id, "👋 Hello! Welcome to the Base Bot. What is your name?")
            return
        
        user_state = get_user_state(chat_id)
        if user_state == "WAITING_NAME":
            print("Are you a developer? a message just dropped. Nothing to show you")
            name = text.strip()
            set_user_name(chat_id, name)
            set_user_state(chat_id, state_idle)
            send_button(chat_id, f"Welcome {get_user_name(chat_id)}! Feel free to explore the bot template.")
            return

    if "callback_query" in update:
        callback = update["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        data = callback["data"]
            
        if data == "ABOUT":
            func_about(chat_id)
        elif data == "HELP":
            send_button(chat_id, f"Help section: Add your instructions here.")
        elif data == "GAMES":
            send_button(chat_id, f"Games module coming soon to this template.")
        elif data == "EXPLORE":
            send_button(chat_id, "Explore module: Add your content here.")  

def run_polling():
    """Polling loop for local testing (bypasses webhooks)"""
    offset = 0
    # Clear any existing webhook so polling works
    requests.get(f"{Telegram_API}/deleteWebhook")
    print("--- POLLING STARTED (Local Testing Mode) ---")
    while True:
        try:
            response = requests.get(f"{Telegram_API}/getUpdates?offset={offset}&timeout=30").json()
            if response.get("ok"):
                for update in response.get("result", []):
                    process_update(update)
                    offset = update["update_id"] + 1
        except Exception as e:
            print(f"Polling error: {e}")
        time.sleep(1)

def keep_alive():
    # Placeholder URLs. Replace with your own production URLs.
    urls = ["https://www.vectorsauto.com","https://www.vectorstutor.com"]
    if not urls:
        return
        
    time.sleep(2)
    while True:
        for url in urls:
            try:
                requests.get(url, timeout=10)
            except Exception:
                pass
        print("clicked. Alhamdulillah!")
        time.sleep(180)

# Start background threads once (prevents double-start in debug mode)
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # Start Polling ONLY IF locally (not on Render)
    if not os.environ.get('RENDER'):
        threading.Thread(target=run_polling, daemon=True).start()


@app.route("/")
def webapp2():
    return render_template("index.html")

def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(f"{Telegram_API}/sendMessage", json = payload)
    print(response.text)
    
def func_about(chat_id):
    message = "🤖 This is a base Telegram Bot template built with Flask and Python. It is ready for customization and deployment on Render with persistent storage."
    payload = {"chat_id": chat_id, "text": message}
    requests.post(f"{Telegram_API}/sendMessage", json=payload)

def func_help(chat_id):
    message = "🤖 This is a template help message. You can customize it in app.py."
    payload = {"chat_id": chat_id, "text": message}
    requests.post(f"{Telegram_API}/sendMessage", json = payload)

def send_button(chat_id, text, image = None):
    print("Keyboard reached")
    keyboard = {"inline_keyboard": [
        [{"text": "Explore Template", "callback_data": "EXPLORE"}],
        [{"text": "Games Module", "callback_data": "GAMES"}],
        [{"text": "ℹ️ About Bot", "callback_data": "ABOUT"}],
        [{"text": "🆘 Help", "callback_data": "HELP"}],
        [{"text": "Web App Link", "web_app": {"url" : f"https://your-app-url.com/tg/{chat_id}"}}]
    ]}
    payload = {"chat_id": chat_id, "text": text, "reply_markup": keyboard}
    requests.post(f"{Telegram_API}/sendMessage", json = payload)
    
def invite_link(chat_id):
    api = f"{Telegram_API}/createChatInviteLink"
    payload = {
        "chat_id": chat_id,
        "member_limit": 1,
        "expire_date": int(time.time()) + 7200
    }
    response = requests.post(api, json = payload)
    return response.json()["result"]["invite_link"]

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
