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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()

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
STRING_SESSION = "BQHqrIAAAuk1Fe5vh8Po6simtUnWpzeWfq4slr8Z8qpHIWYJ2UYursoiGMFNZpKd4In18wOYnAQ2PiU2LD9wssxdXlq3HPnze4bohCSXvUR1X7a-l6Im1CYrDVLqLxgPfzS5Mp3i73DXIqo917N9EYdn4l9GkfGM4twHz4Wdv3ShJirABf73nlxpVfD8eDc7logD0eE9RHDOiX_BXKE_mXib-F9TCHGRdu9G8zrvDKr748PGocaXBFr184J1S-ByX5eNbbtU1Mcux8-ffxqlb_DUKg7SqZj904uAOZ77tr2ie2RKFAsepTKEGWFFBUE3C3abqOmUALUdXt3w2RGqyoIU4t9aIAAAAAHMLobqAA"

bot = Client("restricted_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

IS_PROCESSING = False 

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 **Welcome to Bulk Save Restricted Bot!**\n\n"
        "▶️ **Bulk / Full Channel Clone:** Format:\n"
        "`/clone source_id target_id`\n\n"
        "**Example:** `/clone -1003252713137 -1003819598497`"
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

    status = await message.reply_text("🔄 **Bulk Forwarding Shuru... Channels connect ho rahe hain...**")
    IS_PROCESSING = True
    success_count = 0

    try:
        # Step 1: Saari chat history ko fetch karna safely
        messages_list = []
        async for msg in user.get_chat_history(source_chat):
            if msg.service: # Service messages (like pinned logs) hatao
                continue
            messages_list.append(msg)
        
        # Step 2: Sabse purani post (EP-1) se shuru karne ke liye list ko ulti directional reverse karna
        messages_list.reverse()

        if not messages_list:
            await status.edit("❌ Source channel mein koi bhi valid message nahi mila ya account joined nahi hai.")
            IS_PROCESSING = False
            return

        await status.edit(f"📦 Total **{len(messages_list)}** posts mili hain. Forwarding shuru ho rahi hai...")

        # Step 3: Main Forwarding Loop
        for msg in messages_list:
            if not IS_PROCESSING:
                break

            try:
                # Text Messages handle karne ke liye
                if msg.text:
                    await bot.send_message(chat_id=target_chat, text=msg.text, entities=msg.entities)
                    success_count += 1
                
                # Media files (Audio, Video, Photo, Docs) handle karne ke liye
                elif msg.media:
                    # Direct userbot stream se ya local temp folder mein download karna
                    file_path = await user.download_media(msg)
                    if file_path:
                        caption = msg.caption if msg.caption else ""
                        caption_entities = msg.caption_entities if msg.caption_entities else None

                        # Har restricted file ko bot naye sire se naye server par post karega
                        await bot.send_document(
                            chat_id=target_chat,
                            document=file_path,
                            caption=caption,
                            caption_entities=caption_entities
                        )
                        success_count += 1
                        
                        # Storage bharne se bachane ke liye download ki gayi file delete karna
                        if os.path.exists(file_path):
                            os.remove(file_path)

                # Har post forward hote hi chat screen par instantaneous status update
                await status.edit(f"▓ Progress: **{success_count}** posts forward ho chuki hain...")
                
                # Telegram flood protection ke liye short 2-second gap
                await asyncio.sleep(2) 

            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                # Agar kisi ek post mein error aaye toh poora bot crash na ho, aage badhta rahe
                continue

        await status.edit(f"✅ **Bulk Forwarding Complete!** Total: {success_count} posts cloned successfully.")
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

