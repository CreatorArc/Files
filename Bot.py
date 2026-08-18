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
    return "Multi-File Store Bot is running!"

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

active_sessions = {}

# ----------------- DATABASE -----------------
conn = sqlite3.connect("batch_files.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, batch_id TEXT, file_type TEXT, file_id TEXT, caption TEXT)")
conn.commit()

# ----------------- COMMANDS -----------------
@bot.message_handler(commands=['upload'])
def start_upload(message):
    if message.from_user.id != ADMIN_ID:
        return
    batch_id = str(uuid.uuid4().hex[:8])
    active_sessions[message.from_user.id] = batch_id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏁 Finish & Generate Link", callback_data="finish_upload"))
    bot.reply_to(message, f"✅ *Upload Mode Started!*\nBatch: `{batch_id}`\n\nAb files bhejein. Finish karne ke liye button dabayein.", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_files(message):
    admin_id = message.from_user.id
    if admin_id not in active_sessions:
        return

    batch_id = active_sessions[admin_id]
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

    cursor.execute("INSERT INTO files (batch_id, file_type, file_id, caption) VALUES (?, ?, ?, ?)", (batch_id, file_type, file_id, message.caption))
    conn.commit()
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏁 Finish & Generate Link", callback_data="finish_upload"))
    bot.reply_to(message, "📂 File added! Aur bhejein ya Finish dabayein.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "finish_upload")
def finish_upload(call):
    admin_id = call.from_user.id
    if admin_id not in active_sessions:
        return
    batch_id = active_sessions.pop(admin_id)
    share_url = f"https://t.me/{BOT_USERNAME}?start={batch_id}"
    bot.edit_message_text(f"🎉 *Batch Finished!*\n\n🔗 *Single Link:*\n`{share_url}`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
    bot.answer_callback_query(call.id, "Done!")

@bot.message_handler(commands=['start'])
def handle_start(message):
    parts = message.text.split()
    if len(parts) > 1:
        batch_id = parts[1]
        cursor.execute("SELECT file_type, file_id, caption FROM files WHERE batch_id = ?", (batch_id,))
        files = cursor.fetchall()
        
        if not files:
            bot.reply_to(message, "❌ Invalid or expired link.")
            return

        bot.reply_to(message, f"📥 Sending {len(files)} files...")
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
                print(f"Error: {e}")
    else:
        if message.from_user.id == ADMIN_ID:
            bot.reply_to(message, "👋 Welcome Admin! `/upload` command se batch upload start karein.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "👋 Welcome! Files access karne ke liye link par click karein.")

if __name__ == '__main__':
    bot.infinity_polling()
