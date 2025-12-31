import os
from threading import Thread
from flask import Flask
from config import supabase

app = Flask('')

@app.route('/')
def home():
    # Supabase'i uyanık tutmak için basit bir ping (veri yazmaz)
    if supabase:
        try:
            supabase.table("users").select("user_id").limit(1).execute()
        except Exception:
            pass  # Hata olsa bile botun çalışmasını engelleme
    return "Bot is alive and running with Supabase!"

def run_flask():
    # Render gibi platformlar PORT env değişkenini otomatik atar
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()