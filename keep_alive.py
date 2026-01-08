import os
import hmac
import hashlib
import json
import time
from urllib.parse import unquote
from threading import Thread
from flask import Flask, send_from_directory, request, jsonify
from config import supabase, BOT_TOKEN
import database as db

# Configure Flask to serve static files from 'web' directory
app = Flask(__name__, static_folder='web', static_url_path='/web')

@app.route('/')
def home():
    # Keep-alive check
    if supabase:
        try:
            supabase.table("users").select("user_id").limit(1).execute()
        except Exception:
            pass
    return "ViraBot Web App Server is Running! 🚀"

# --- STATIC FILE SERVING ---
@app.route('/web/<path:path>')
def serve_web_files(path):
    return send_from_directory('web', path)

# --- API HELPER: VALIDATE TELEGRAM WEBAPP DATA ---
def validate_telegram_data(init_data):
    """
    Validates the data received from the Telegram Web App.
    Returns the user data if valid, None otherwise.
    """
    if not init_data:
        return None
        
    try:
        parsed_data = {}
        for key_value in init_data.split('&'):
            key, value = key_value.split('=', 1)
            parsed_data[unquote(key)] = unquote(value)
            
        hash_value = parsed_data.pop('hash', None)
        if not hash_value:
            return None
            
        # Sort keys alphabetically
        data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(parsed_data.items()))
        
        # Calculate HMAC-SHA256 signature
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash == hash_value:
            # Data is valid, parse 'user' JSON
            user_json = parsed_data.get('user')
            if user_json:
                return json.loads(user_json)
    except Exception as e:
        print(f"Validation Error: {e}")
    return None

# --- API: SLOT GAME ---
# Slot API Removed for Vira Production

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({"status": "ok", "message": "API is reachable"})


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    # Threaded=True for better handling in dev
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()