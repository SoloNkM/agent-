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


def enregistrer(nom, msg_id, texte):
    try:
        fichier = DOSSIER / "envois.json"
        try:
            liste = json.loads(fichier.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            liste = []
        numero = max([e.get("n", 0) for e in liste], default=0) + 1
        liste.append({
            "n": numero,
            "alias": nom,
            "msg_id": msg_id,
            "date": time.strftime("%Y-%m-%d %H:%M"),
            "apercu": " ".join(texte.split())[:200],
            "supprime": False,
        })
        fichier.write_text(json.dumps(liste[-200:], ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


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
                m = client.send_message(int(contacts[nom]["id"]), texte)
                enregistrer(nom, m.id, texte)
                resultats[nom] = "ok"
            except Exception as e:
                resultats[nom] = "erreur : " + type(e).__name__
            if i < len(noms) - 1:
                time.sleep(2)
        print(json.dumps(resultats, ensure_ascii=True))
    finally:
        client.disconnect()


main()