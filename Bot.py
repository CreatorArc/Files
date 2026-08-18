import os
import sqlite3
import threading
import uuid
from flask import Flask
import telebot
from telebot import types

# ----------------- FLASK SERVER -----------------
app = Flask('')

@app.route('/')
def home():
    return "Study Documents Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask).start()

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8299811786:AAEUq54FjadME9v1Nf6Xc_pwLPRn0eF7wPA"
BOT_USERNAME = "Study_documentsbot"
ADMIN_ID = 8800158361

bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

# Active sessions store: {admin_id: {"batch_id": "...", "count": 0}}
active_sessions = {}

# ----------------- DATABASE -----------------
conn = sqlite3.connect("batch_files.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT,
        file_type TEXT,
        file_id TEXT,
        caption TEXT
    )
""")
conn.commit()

# ----------------- 1. START UPLOAD MODE -----------------
@bot.message_handler(commands=['upload'])
def start_upload(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    batch_id = str(uuid.uuid4().hex[:8])
    active_sessions[message.from_user.id] = {"batch_id": batch_id, "count": 0}
    
    # Bottom Screen Keyboard Button
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.add(types.KeyboardButton("🏁 Finish Upload"))
    
    bot.reply_to(
        message, 
        f"✅ *Upload Mode Started!*\nBatch ID: `{batch_id}`\n\n"
        "👉 Ab aap ek-ek karke ya ek sath saari photos/videos/files bhejte rahein.\n"
        "👉 Upload khatam hone ke baad neeche **'🏁 Finish Upload'** button dabayein.", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

# ----------------- 2. RECEIVE MEDIA FILES -----------------
@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_files(message):
    admin_id = message.from_user.id
    if admin_id not in active_sessions:
        bot.reply_to(message, "⚠️ Pehle `/upload` command bhej kar session start karein.", parse_mode="Markdown")
        return

    batch_id = active_sessions[admin_id]["batch_id"]
    file_type = message.content_type
    
    if file_type == 'photo':
        file_id = message.photo[-1].file_id
    elif file_type == 'video':
        file_id = message.video.file_id
    elif file_type == 'document':
        file_id = message.document.file_id
    elif file_type == 'audio':
        file_id = message.audio.file_id
    else:
        return

    cursor.execute(
        "INSERT INTO files (batch_id, file_type, file_id, caption) VALUES (?, ?, ?, ?)", 
        (batch_id, file_type, file_id, message.caption)
    )
    conn.commit()
    
    active_sessions[admin_id]["count"] += 1
    total_saved = active_sessions[admin_id]["count"]
    
    bot.reply_to(message, f"📥 File #{total_saved} Saved! Aur bhejte rahein ya neeche **'🏁 Finish Upload'** dabayein.", parse_mode="Markdown")

# ----------------- 3. FINISH UPLOAD HANDLER -----------------
@bot.message_handler(func=lambda msg: msg.text == "🏁 Finish Upload" or msg.text == "/finish")
def finish_upload_action(message):
    admin_id = message.from_user.id
    if admin_id not in active_sessions:
        bot.reply_to(message, "⚠️ Koi active upload session nahi hai. Naya start karne ke liye `/upload` likhein.", parse_mode="Markdown")
        return
    
    session_data = active_sessions.pop(admin_id)
    batch_id = session_data["batch_id"]
    total_files = session_data["count"]
    
    share_url = f"https://t.me/{BOT_USERNAME}?start={batch_id}"
    
    # Keyboard hatane ke liye RemoveKeyboard
    remove_markup = types.ReplyKeyboardRemove()
    
    response_text = (
        "🎉 *Batch Upload Successfully Completed!*\n\n"
        f"📦 *Total Files:* {total_files}\n"
        f"🔗 *Single Access Link:*\n`{share_url}`\n\n"
        "_(Upar diye link par tap karke copy karein aur share karein)_"
    )
    
    bot.send_message(message.chat.id, response_text, parse_mode="Markdown", reply_markup=remove_markup)

# ----------------- 4. USER /START LINK HANDLER -----------------
@bot.message_handler(commands=['start'])
def handle_start(message):
    parts = message.text.split()
    if len(parts) > 1:
        batch_id = parts[1]
        cursor.execute("SELECT file_type, file_id, caption FROM files WHERE batch_id = ?", (batch_id,))
        files = cursor.fetchall()
        
        if not files:
            bot.reply_to(message, "❌ Link invalid ya expire ho chuka hai.")
            return

        bot.reply_to(message, f"📥 Loading {len(files)} files, kripya intezar karein...")
        for f_type, f_id, cap in files:
            try:
                if f_type == 'photo':
                    bot.send_photo(message.chat.id, f_id, caption=cap)
                elif f_type == 'video':
                    bot.send_video(message.chat.id, f_id, caption=cap)
                elif f_type == 'document':
                    bot.send_document(message.chat.id, f_id, caption=cap)
                elif f_type == 'audio':
                    bot.send_audio(message.chat.id, f_id, caption=cap)
            except Exception as e:
                print(f"Error sending file: {e}")
    else:
        if message.from_user.id == ADMIN_ID:
            bot.reply_to(message, "👋 Welcome Admin! `/upload` bhej kar batch upload shuru karein.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "👋 Welcome! Files access karne ke liye valid link par click karein.")

if __name__ == '__main__':
    bot.infinity_polling()
