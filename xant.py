import os
import re
import time
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events

ENV_FILE = ".env"

if not os.path.exists(ENV_FILE):
    print("==================================================")
    print("🚀 Welcome to Xant Userbot Setup!")
    print("Get your API credentials from https://my.telegram.org")
    print("==================================================\n")

    api_id_input = input("Enter your TELEGRAM_API_ID: ").strip()
    api_hash_input = input("Enter your TELEGRAM_API_HASH: ").strip()

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(f"TELEGRAM_API_ID={api_id_input}\n")
        f.write(f"TELEGRAM_API_HASH={api_hash_input}\n")

    print("\n✅ Configuration saved to .env file!\n")

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient(
    "user_session",
    API_ID,
    API_HASH,
    connection_retries=10,
    retry_delay=3,
    timeout=30
)

LINK_PATTERN = r"https://t\.me/(?:c/(\d+)|([\w_]+))/(\d+)"


def extract_all_links(text: str):
    matches = re.finditer(LINK_PATTERN, text)
    results = []

    for match in matches:
        full_link = match.group(0)
        channel_part, username, message_id = match.groups()

        if channel_part:
            chat_id = int(f"-100{channel_part}")
        else:
            chat_id = username

        results.append((chat_id, int(message_id), full_link))

    return results


async def download_with_retry(target_msg, progress_callback, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            return await client.download_media(
                target_msg, progress_callback=progress_callback
            )
        except Exception as e:
            if attempt == max_retries:
                raise e
            await asyncio.sleep(2 * attempt)


@client.on(events.NewMessage(chats="me"))
async def handle_saved_messages(event):
    text = event.raw_text

    if "t.me/" not in text:
        return

    links = extract_all_links(text)
    if not links:
        return

    total_count = len(links)
    status_msg = await event.respond(
        f"⏳ Found links: {total_count}. Starting processing..."
    )

    for index, (chat_id, msg_id, full_link) in enumerate(links, start=1):
        last_update_time = [0]

        async def progress_callback(current, total):
            now = time.time()
            if now - last_update_time[0] > 2 or current == total:
                last_update_time[0] = now
                percent = (current / total) * 100
                mb_current = current / (1024 * 1024)
                mb_total = total / (1024 * 1024)

                try:
                    await status_msg.edit(
                        f"⏳ **Processing [{index}/{total_count}]**\n"
                        f"🔗 `{full_link}`\n"
                        f"📥 Downloading: **{percent:.1f}%** ({mb_current:.1f} MB / {mb_total:.1f} MB)"
                    )
                except Exception:
                    pass

        try:
            await status_msg.edit(
                f"⏳ **Processing [{index}/{total_count}]**\n"
                f"🔗 `{full_link}`\n"
                f"🔎 Fetching message..."
            )

            target_msg = await client.get_messages(chat_id, ids=msg_id)

            if not target_msg or not target_msg.media:
                await event.respond(
                    f"⚠️ **[{index}/{total_count}]** No media found or message unavailable at `{full_link}`."
                )
                continue

            filename = await download_with_retry(target_msg, progress_callback)

            await status_msg.edit(
                f"📤 **[{index}/{total_count}]** Sending file to Saved Messages..."
            )

            await client.send_file("me", filename)

            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            await event.respond(
                f"❌ **[{index}/{total_count}]** Error processing `{full_link}`:\n`{e}`"
            )

    await status_msg.edit(
        f"✅ **All links processed! ({total_count}/{total_count})**"
    )


print("🚀 Xant started and ready to process links...")

with client:
    client.run_until_disconnected()
