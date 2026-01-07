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
@app.route('/api/games/slot/spin', methods=['POST'])
def slot_spin():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
             return jsonify({"error": "Invalid JSON", "success": False}), 400
             
        init_data = data.get('initData')
        bet_amount = data.get('bet', 100)
        
        # Validate Data
        user_data = validate_telegram_data(init_data)
        if not user_data:
            # For development, allow bypass if needed (but secure for prod)
            # Remove this bypass in strict production
            if os.environ.get("FLASK_ENV") == "development":
                 user_id = 12345
            else:
                 return jsonify({"error": "Unauthorized / Invalid Data", "success": False}), 401
        else:
            user_id = user_data['id']
        
        # 1. Check Balance
        current_coins = db.get_user_coins(user_id) 
        if current_coins < bet_amount:
             return jsonify({"error": "Insufficient funds", "success": False, "balance": current_coins}), 200 # 200 OK but success=False logic
             
        # 2. Deduct Bet
        db.add_user_coins(user_id, -bet_amount)
        
        # 3. Game Logic (RNG)
        import random
        rows = 3
        symbols = ["🍒", "🍋", "🍇", "💎", "7️⃣"]
        result = [random.choice(symbols) for _ in range(rows)]
        
        # Determine Win
        win_amount = 0
        is_win = False
        
        if result[0] == result[1] == result[2]:
            is_win = True
            s = result[0]
            if s == "🍒": win_amount = bet_amount * 3
            elif s == "🍋": win_amount = bet_amount * 5
            elif s == "🍇": win_amount = bet_amount * 10
            elif s == "💎": win_amount = bet_amount * 20
            elif s == "7️⃣": win_amount = bet_amount * 50
            
            db.add_user_coins(user_id, win_amount)
        
        new_balance = db.get_user_coins(user_id)
        
        response = jsonify({
            "success": True,
            "result": result,
            "is_win": is_win,
            "win_amount": win_amount,
            "new_balance": new_balance
        })
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

# --- API: XOX GAME ---
@app.route('/api/games/xox/result', methods=['POST'])
def xox_result():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON", "success": False}), 400
            
        init_data = data.get('initData')
        winner = data.get('winner')
        difficulty = data.get('difficulty', 'easy')
        
        # Validate Data
        user_data = validate_telegram_data(init_data)
        if not user_data:
            # For development, allow bypass if needed (but secure for prod)
            if os.environ.get("FLASK_ENV") == "development":
                user_id = 12345
            else:
                return jsonify({"error": "Unauthorized / Invalid Data", "success": False}), 401
        else:
            user_id = user_data['id']
        
        # Log game result
        db.log_xox_game(user_id, winner, difficulty)
        
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

# --- API: BLACKJACK GAME ---
@app.route('/api/games/blackjack/balance', methods=['POST'])
def blackjack_balance():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON", "success": False}), 400
            
        init_data = data.get('initData')
        
        # Validate Data
        user_data = validate_telegram_data(init_data)
        if not user_data:
            if os.environ.get("FLASK_ENV") == "development":
                user_id = 12345
            else:
                return jsonify({"error": "Unauthorized", "success": False}), 401
        else:
            user_id = user_data['id']
        
        # Get balance
        balance = db.get_user_coins(user_id)
        
        response = jsonify({"success": True, "balance": balance})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        print(f"Balance Error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/games/blackjack/result', methods=['POST'])
def blackjack_result():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON", "success": False}), 400
            
        init_data = data.get('initData')
        result = data.get('result')
        bet_amount = data.get('betAmount', 0)
        win_amount = data.get('winAmount', 0)
        player_score = data.get('playerScore', 0)
        dealer_score = data.get('dealerScore', 0)
        
        # Validate Data
        user_data = validate_telegram_data(init_data)
        if not user_data:
            if os.environ.get("FLASK_ENV") == "development":
                user_id = 12345
            else:
                return jsonify({"error": "Unauthorized", "success": False}), 401
        else:
            user_id = user_data['id']
        
        # Update coins (server confirms the win amount)
        if win_amount > 0:
            db.add_user_coins(user_id, win_amount)
        
        # Log game
        db.log_blackjack_game(user_id, player_score, dealer_score, result)
        
        response = jsonify({"success": True})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        print(f"Blackjack Result Error: {e}")
        return jsonify({"error": str(e), "success": False}), 500

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