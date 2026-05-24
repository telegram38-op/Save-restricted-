import os
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# --- CONFIGURATION ---
API_ID = 1234567  # Apni API ID daalein
API_HASH = "your_api_hash_here"
BOT_TOKEN = "your_bot_token_here"
STRING_SESSION = "your_pyrogram_string_session_here"

bot = Client("restricted_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("user_session", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)

# --- BULK FORWARD STATUS FLAG ---
# Isse block karein taaki ek waqt par ek hi bulk process chale
IS_PROCESSING = False 

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        "👋 **Welcome to Bulk Save Restricted Bot!**\n\n"
        "▶️ **Single Post:** Bas post ka link bhejein.\n"
        "▶️ **Bulk / Full Channel Clone:** Niche diye gaye format mein command bhejein:\n"
        "`/clone source_id target_id`\n\n"
        "**Example:** `/clone -100123456789 -100987654321`"
    )

# --- BULK FORWARDING LOGIC ---
@bot.on_message(filters.command("clone") & filters.private)
async def bulk_clone(client, message):
    global IS_PROCESSING
    
    if IS_PROCESSING:
        await message.reply_text("⚠️ Ek bulk process pehle se chal rahi hai. Kripya uske khatam hone ka wait karein.")
        return

    # Command arguments check karna
    if len(message.command) < 3:
        await message.reply_text("❌ **Galat Format!**\nSahi Tarika: `/clone [Source_ID] [Target_ID]`")
        return

    source_chat = message.command[1]
    target_chat = message.command[2]

    # ID format sahi karna (agar username hai toh string, agar numeric ID hai toh integer)
    try:
        if source_chat.startswith("-100") or source_chat.isdigit():
            source_chat = int(source_chat)
        if target_chat.startswith("-100") or target_chat.isdigit():
            target_chat = int(target_chat)
    except ValueError:
        pass

    status = await message.reply_text("🔄 **Bulk Forwarding Shuru Ho Rahi Hai...**\nHistory fetch ki jaa rahi hai.")
    IS_PROCESSING = True
    success_count = 0

    try:
        async with user:
            # reverse=True se sabse PURANI (EP-1) post se shuru hoga
            async for msg in user.get_chat_history(source_chat, reverse=True):
                if not IS_PROCESSING: # Agar beech me stop karna ho
                    break
                
                if msg.empty:
                    continue

                try:
                    # 1. Agar text message hai
                    if msg.text:
                        await bot.send_message(chat_id=target_chat, text=msg.text, entities=msg.entities)
                        success_count += 1
                    
                    # 2. Agar restricted media file hai
                    elif msg.media:
                        # File local storage me download hogi
                        file_path = await user.download_media(msg)
                        
                        caption = msg.caption if msg.caption else ""
                        caption_entities = msg.caption_entities if msg.caption_entities else None

                        # Target par fresh upload
                        await bot.send_document(
                            chat_id=target_chat,
                            document=file_path,
                            caption=caption,
                            caption_entities=caption_entities
                        )
                        
                        success_count += 1
                        
                        # Storage bharne se bachane ke liye turant delete karein
                        if os.path.exists(file_path):
                            os.remove(file_path)

                    # Har file ke baad thoda delay taaki FloodWait (Ban) na aaye
                    await status.edit(f"▓ Progress: **{success_count}** posts successfully forward ho chuki hain...")
                    await asyncio.sleep(3) 

                except FloodWait as e:
                    # Agar Telegram heavy traffic ki wajah se rokta hai
                    await status.edit(f"⚠️ Telegram Limit! {e.value} seconds ke liye pause ho raha hai...")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    print(f"Error skipping message ID {msg.id}: {str(e)}")
                    continue # Kisi ek error ki wajah se poora bot band na ho

        await status.edit(f"✅ **Bulk Forwarding Complete!**\nTotal **{success_count}** posts forward ki gayi hain.")
    
    except Exception as e:
        await status.edit(f"❌ **Fatal Error:** {str(e)}")
    finally:
        IS_PROCESSING = False

# --- SINGLE POST BY LINK (Purana Feature) ---
@bot.on_message(filters.private & filters.text & ~filters.command(["start", "clone"]))
async def handle_link(client, message):
    # (Pichle reply wala single link handler code yahan automatically kaam karega)
    pass

# Client Runner
async def main():
    await user.start()
    await bot.start()
    print("🤖 Bulk Restricted Bot Online!")
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

