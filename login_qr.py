import os
import qrcode
from dotenv import load_dotenv
from telethon import TelegramClient

ENV_FILE = ".env"

if not os.path.exists(ENV_FILE):
    print("==================================================")
    print("🚀 Welcome to Xant Setup (QR Login)!")
    print("Get your API credentials from https://my.telegram.org")
    print("==================================================\n")

    api_id_input = input("Enter your TELEGRAM_API_ID: ").strip()
    api_hash_input = input("Enter your TELEGRAM_API_HASH: ").strip()

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(f"TELEGRAM_API_ID={api_id_input}\n")
        f.write(f"TELEGRAM_API_HASH={api_hash_input}\n")

    print("\n✅ Configuration saved to .env file!\n")

load_dotenv()

try:
    API_ID = int(os.getenv("TELEGRAM_API_ID"))
    API_HASH = os.getenv("TELEGRAM_API_HASH")
except (TypeError, ValueError):
    print("❌ Error: Invalid TELEGRAM_API_ID in .env file (must contain only digits).")
    print("Please delete the .env file and restart the script.")
    exit(1)

client = TelegramClient("user_session", API_ID, API_HASH)


async def main():
    await client.connect()
    if not await client.is_user_authorized():
        print("⏳ Generating QR code...")
        qr_login = await client.qr_login()

        qr = qrcode.QRCode()
        qr.add_data(qr_login.url)
        qr.print_ascii(invert=True)

        print(
            "\n📱 Open Telegram on your phone ➔ Settings ➔ Devices ➔ Link Desktop Device and scan the QR code above."
        )
        await qr_login.wait()

    print("\n✅ Authorization successful! user_session.session created.")


if __name__ == "__main__":
    client.loop.run_until_complete(main())
