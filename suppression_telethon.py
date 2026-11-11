import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import MessageEmpty

DOSSIER = Path(__file__).resolve().parent
load_dotenv(DOSSIER / ".env")


def fin(message):
    print(json.dumps({"erreur": message}, ensure_ascii=True))
    sys.exit(1)


def main():
    try:
        donnees = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        numero = int(donnees["numero"])
        fichier = DOSSIER / "envois.json"
        envois = json.loads(fichier.read_text(encoding="utf-8"))
        contacts = json.loads((DOSSIER / "contacts.json").read_text(encoding="utf-8"))
        api_id = int(os.getenv("TELEGRAM_API_ID"))
        api_hash = os.getenv("TELEGRAM_API_HASH")
    except Exception:
        fin("Données invalides ou clés Telegram manquantes.")

    entree = next((e for e in envois if e.get("n") == numero), None)
    if entree is None or entree.get("supprime"):
        fin("Envoi introuvable ou déjà supprimé.")
    contact = contacts.get(entree["alias"])
    if contact is None:
        fin("Contact absent du carnet.")

    client = TelegramClient(str(DOSSIER / "agent"), api_id, api_hash)
    client.connect()
    try:
        if not client.is_user_authorized():
            fin("Session expirée : relance connexion_telethon.py.")
        cible = int(contact["id"])
        msg_id = int(entree["msg_id"])
        client.delete_messages(cible, [msg_id], revoke=True)
        reste = client.get_messages(cible, ids=msg_id)
        if reste is not None and not isinstance(reste, MessageEmpty):
            fin("Telegram n'a pas supprimé le message (délai dépassé ou droits insuffisants).")
        entree["supprime"] = True
        fichier.write_text(json.dumps(envois, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": True}))
    finally:
        client.disconnect()


main()
