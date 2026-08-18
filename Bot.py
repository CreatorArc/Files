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

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()

keep_alive()

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = "8299811786:AAEUq54FjadME9v1Nf6Xc_pwLPRn0eF7wPA"
BOT_USERNAME = "Study_documentsbot"
ADMIN_ID = 8800158361
# ----------------- -----------------

bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

# Session tracking
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

# ----------------- COMMANDS -----------------

@bot.message_handler(commands=['upload'])
def start_upload(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    batch_id = str(uuid.uuid4().hex[:8])
    active_sessions[message.from_user.id] = batch_id
    
    bot.reply_to(
        message, 
        f"✅ *Upload Mode Started!*\nBatch ID: `{batch_id}`\n\nAb aap files bhejein. Finish karne ke liye neeche button dabayein.", 
        parse_mode="Markdown", 
        reply_markup=get_finish_markup()
    )

def get_finish_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏁 Finish & Generate Link", callback_data="finish_upload"))
    return markup

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_files(message):
    admin_id = message.from_user.id
    if admin_id not in active_sessions:
        bot.reply_to(message, "❌ Pehle /upload command use karein.")
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
        file_id = None
    
    cursor.execute("INSERT INTO files (batch_id, file_type, file_id, caption) VALUES (?, ?, ?, ?)",
                   (batch_id, file_type, file_id, message.caption))
    conn.commit()
    
    bot.reply_to(message, "📂 File added to batch! Send more or click Finish.", reply_markup=get_finish_markup())

@bot.callback_query_handler(func=lambda call: call.data == "finish_upload")
def finish_upload(call):
    admin_id = call.from_user.id
    if admin_id not in active_sessions:
        return
    
    batch_id = active_sessions.pop(admin_id)
    share_url = f"https://t.me/{BOT_USERNAME}?start={batch_id}"
    
    bot.edit_message_text(
        f"🎉 *Batch Finished!*\n\n🔗 *Single Link:*\n`{share_url}`", 
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id, "Link Generated!")

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
                print(f"Error sending file: {e}")
    else:
        if message.from_user.id == ADMIN_ID:
            bot.reply_to(message, "👋 Welcome Admin! /upload command use karke batch upload start karein.")
        else:
            bot.reply_to(message, "👋 Welcome! Files access karne ke liye valid link par click karein.")

if __name__ == '__main__':
    bot.infinity_polling()
        caption TEXT
    )
""")
conn.commit()

# ----------------- COMMANDS -----------------

@bot.message_handler(commands=['upload'])
def start_upload(message):
    if message.from_user.id != ADMIN_ID: return
    
    batch_id = str(uuid.uuid4().hex[:8])
    active_sessions[message.from_user.id] = batch_id
    
    bot.reply_to(message, f"✅ *Upload Mode Started!*\nBatch ID: `{batch_id}`\n\nAb aap files bhejein. Finish karne ke liye neeche button dabayein.", 
                 parse_mode="Markdown", reply_markup=get_finish_markup())

def get_finish_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏁 Finish & Generate Link", callback_data="finish_upload"))
    return markup

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_files(message):
    admin_id = message.from_user.id
    if admin_id not in active_sessions:
        bot.reply_to(message, "❌ Pehle /upload command use karein.")
        return

    batch_id = active_sessions[admin_id]
    file_type = message.content_type
    
    if file_type == 'photo': file_id = message.photo[-1].file_id
    elif file_type == 'video': file_id = message.video.file_id
    elif file_type == 'document': file_id = message.document.file_id
    elif file_type == 'audio': file_id = message.audio.file_id
    
    cursor.execute("INSERT INTO files (batch_id, file_type, file_id, caption) VALUES (?, ?, ?, ?)",
                   (batch_id, file_type, file_id, message.caption))
    conn.commit()
    
    bot.reply_to(message, "📂 File added to batch! Send more or click Finish.", reply_markup=get_finish_markup())

@bot.callback_query_handler(func=lambda call: call.data == "finish_upload")
def finish_upload(call):
    admin_id = call.from_user.id
    if admin_id not in active_sessions: return
    
    batch_id = active_sessions.pop(admin_id)
    share_url = f"https://t.me/{BOT_USERNAME}?start={batch_id}"
    
    bot.edit_message_text(f"🎉 *Batch Finished!*\n\n🔗 *Single Link:*\n`{share_url}`", 
                          chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def handle_start(message):
    if len(message.text.split()) > 1:
        batch_id = message.text.split()[1]
        cursor.execute("SELECT file_type, file_id, caption FROM files WHERE batch_id = ?", (batch_id,))
        files = cursor.fetchall()
        
        if not files:
            bot.reply_to(message, "❌ Invalid link.")
            return

        bot.reply_to(message, f"📥 Sending {len(files)} files...")
        for f_type, f_id, cap in files:
            try:
                if f_type == 'photo': bot.send_photo(message.chat.id, f_id, caption=cap)
                elif f_type == 'video': bot.send_video(message.chat.id, f_id, caption=cap)
                elif f_type == 'document': bot.send_document(message.chat.id, f_id, caption=cap)
                elif f_type == 'audio': bot.send_audio(message.chat.id, f_id, caption=cap)
            except: pass
    else:
        bot.reply_to(message, "Welcome! Files access karne ke liye link ka use karein.")

bot.infinity_polling()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_key TEXT PRIMARY KEY,
            file_type TEXT,
            file_id TEXT,
            caption TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_file_to_db(file_key, file_type, file_id, caption):
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (file_key, file_type, file_id, caption) VALUES (?, ?, ?, ?)",
                   (file_key, file_type, file_id, caption))
    conn.commit()
    conn.close()

def get_file_from_db(file_key):
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_type, file_id, caption FROM files WHERE file_key = ?", (file_key,))
    result = cursor.fetchone()
    conn.close()
    return result
# --------------------------------------------------

# 1. /start command (Normal + Deep Linking Link Handler)
@bot.message_handler(commands=['start'])
def handle_start(message):
    text_parts = message.text.split()

    # Agar user shareable link se aaya hai (e.g., /start file_xxxx)
    if len(text_parts) > 1:
        file_key = text_parts[1]
        file_data = get_file_from_db(file_key)

        if file_data:
            file_type, file_id, caption = file_data
            caption_text = caption if caption else ""

            try:
                if file_type == 'photo':
                    bot.send_photo(message.chat.id, file_id, caption=caption_text)
                elif file_type == 'video':
                    bot.send_video(message.chat.id, file_id, caption=caption_text)
                elif file_type == 'document':
                    bot.send_document(message.chat.id, file_id, caption=caption_text)
                elif file_type == 'audio':
                    bot.send_audio(message.chat.id, file_id, caption=caption_text)
            except Exception as e:
                bot.reply_to(message, "❌ File send karne me error aaya.")
        else:
            bot.reply_to(message, "❌ Yeh link expire ya invalid hai.")
    else:
        # Normal /start command
        if message.from_user.id == ADMIN_ID:
            bot.reply_to(message, "👋 *Welcome Admin!*\n\nAap koi bhi Photo, Video ya Document bhejein, main uska shareable link generate kar dunga.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "👋 Welcome! Files access karne ke liye valid link par click karein.")

# 2. File Upload Handler (Sirf Admin ke liye)
@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_incoming_file(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Sirf Admin files upload kar sakta hai.")
        return

    file_key = f"file_{uuid.uuid4().hex[:8]}"
    caption = message.caption

    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        save_file_to_db(file_key, 'photo', file_id, caption)
    elif message.content_type == 'video':
        file_id = message.video.file_id
        save_file_to_db(file_key, 'video', file_id, caption)
    elif message.content_type == 'document':
        file_id = message.document.file_id
        save_file_to_db(file_key, 'document', file_id, caption)
    elif message.content_type == 'audio':
        file_id = message.audio.file_id
        save_file_to_db(file_key, 'audio', file_id, caption)

    # Shareable Deep Link
    share_url = f"https://t.me/{BOT_USERNAME}?start={file_key}"

    response_text = (
        "✅ *File Successfully Saved!*\n\n"
        f"🔗 *Shareable Link:*\n`{share_url}`\n\n"
        "_(Upar diye link par tap karke copy karein aur kisi ke sath bhi share karein)_"
    )
    bot.reply_to(message, response_text, parse_mode="Markdown")

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
