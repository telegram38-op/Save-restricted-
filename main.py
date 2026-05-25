import os
import asyncio
from flask import Flask
from threading import Thread

# --- FAKE WEB SERVER FOR RENDER BYPASS ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running 24/7!"

def run_web():
    # Render hamesha port 10000 ya environment variable PORT deta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Background thread me web server shuru karna
Thread(target=run_web).start()

# --- CODES FOR EVENT LOOP PATCH ---
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# --- CONFIGURATION ---
API_ID = 32156800
API_HASH = "73fbf3673dd59fd129a9937ca11c00d2"
BOT_TOKEN = "8920256142:AAFSmSbEr64A-Pyr_iEAreah_Whd3r9OI9M"
STRING_SESSION = "BQHqrIAAAuk1Fe5vh8Po6simtUnWpzeWfq4slr8Z8qpHIWYJ2UYursoiGMFNZpKd4In18wOYnAQ2PiU2LD9wssxdXlq3HPnze4bohCSXvUR1X7a-l6Im1CYrDVLqLxgPfzS5Mp3i73DXIqo917N9EYdn4l9GkfGM4twHz4Wdv3ShJirABf73nlxpVfD8eDc7logD0eE9RHDOiX_BXKE_mXib-F9TCHGRdu9G8zrvDKr748PGocaXBFr184J1S-ByX5eNbbtU1Mcux8-ffxqlb_DUKg7SqZj904uAOZ77tr2ie2RKFAsepTKEGWFFBUE3C3abqOmUALUdXt3w2RGqyoIU4t9aIAAAAAHMLobqAA" # <-- Apna naya wala valid string session yahan daalna

bot = Client("restricted_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

IS_PROCESSING = False 

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 **Welcome to Bulk Save Restricted Bot!**\n\n"
        "▶️ **Single Post:** Bas post ka link bhejein.\n"
        "▶️ **Bulk / Full Channel Clone:** Format:\n"
        "`/clone source_id target_id`\n\n"
        "**Example:** `/clone -100123456789 -100987654321`"
    )

@bot.on_message(filters.command("clone") & filters.private)
async def bulk_clone(client, message):
    global IS_PROCESSING
    if IS_PROCESSING:
        await message.reply_text("⚠️ Ek bulk process pehle se chal rahi hai...")
        return

    if len(message.command) < 3:
        await message.reply_text("❌ Format: `/clone [Source_ID] [Target_ID]`")
        return

    source_chat = message.command[1]
    target_chat = message.command[2]

    try:
        if source_chat.startswith("-100") or source_chat.isdigit():
            source_chat = int(source_chat)
        if target_chat.startswith("-100") or target_chat.isdigit():
            target_chat = int(target_chat)
    except ValueError:
        pass

    status = await message.reply_text("🔄 **Bulk Forwarding Shuru...**")
    IS_PROCESSING = True
    success_count = 0

    try:
        async with user:
            async for msg in user.get_chat_history(source_chat, reverse=True):
                if not IS_PROCESSING:
                    break
                if msg.empty:
                    continue

                try:
                    if msg.text:
                        await bot.send_message(chat_id=target_chat, text=msg.text, entities=msg.entities)
                        success_count += 1
                    elif msg.media:
                        file_path = await user.download_media(msg)
                        caption = msg.caption if msg.caption else ""
                        caption_entities = msg.caption_entities if msg.caption_entities else None

                        await bot.send_document(
                            chat_id=target_chat,
                            document=file_path,
                            caption=caption,
                            caption_entities=caption_entities
                        )
                        success_count += 1
                        if os.path.exists(file_path):
                            os.remove(file_path)

                    await status.edit(f"▓ Progress: **{success_count}** posts forward ho chuki hain...")
                    await asyncio.sleep(3) 

                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception as e:
                    continue

        await status.edit(f"✅ **Bulk Forwarding Complete!** Total: {success_count}")
    except Exception as e:
        await status.edit(f"❌ **Error:** {str(e)}")
    finally:
        IS_PROCESSING = False

async def main():
    await user.start()
    await bot.start()
    print("🤖 Bulk Restricted Bot Online With Web-Bypass!")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Bot stopped.")

