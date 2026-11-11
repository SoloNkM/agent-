import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from telethon.sync import TelegramClient

DOSSIER = Path(__file__).resolve().parent
load_dotenv(DOSSIER / ".env")


def fin(message):
    print(json.dumps({"erreur": message}, ensure_ascii=True))
    sys.exit(1)


def main():
    try:
        donnees = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        noms = donnees["destinataires"]
        texte = str(donnees["texte"]).strip()
        contacts = json.loads((DOSSIER / "contacts.json").read_text(encoding="utf-8"))
        api_id = int(os.getenv("TELEGRAM_API_ID"))
        api_hash = os.getenv("TELEGRAM_API_HASH")
    except Exception:
        fin("Données d'envoi invalides ou clés Telegram manquantes.")

    if not 1 <= len(noms) <= 5 or not texte or len(texte) > 1000:
        fin("Destinataires ou texte invalides.")
    if any(n not in contacts for n in noms):
        fin("Contact absent du carnet.")

    client = TelegramClient(str(DOSSIER / "agent"), api_id, api_hash)
    client.connect()
    try:
        if not client.is_user_authorized():
            fin("Session expirée : relance connexion_telethon.py.")
        resultats = {}
        for i, nom in enumerate(noms):
            try:
                client.send_message(int(contacts[nom]["id"]), texte)
                resultats[nom] = "ok"
            except Exception as e:
                resultats[nom] = "erreur : " + type(e).__name__
            if i < len(noms) - 1:
                time.sleep(2)
        print(json.dumps(resultats, ensure_ascii=True))
    finally:
        client.disconnect()


main()