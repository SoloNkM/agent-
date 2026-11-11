import os

from dotenv import load_dotenv
from telethon.sync import TelegramClient

load_dotenv()
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")

with TelegramClient("agent", api_id, api_hash) as client:
    moi = client.get_me()
    print("Connecté en tant que :", moi.first_name)