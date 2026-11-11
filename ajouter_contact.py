import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.types import User

load_dotenv()
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
FICHIER = Path(__file__).resolve().parent / "contacts.json"


def charger():
    try:
        return json.loads(FICHIER.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


alias = input("Nom court du contact (ex: maman) : ").strip().lower()
cible = input("Son @pseudo Telegram, son numéro (+225...) ou 'me' pour toi : ").strip()
if not alias or not cible:
    sys.exit("Rien saisi.")

with TelegramClient("agent", api_id, api_hash) as client:
    try:
        entite = client.get_entity(cible)
    except Exception:
        sys.exit("Contact introuvable. Vérifie le pseudo ou le numéro.")
    if not isinstance(entite, User) or entite.bot:
        sys.exit("Seules les personnes sont acceptées (pas de groupe, canal ou bot).")
    nom = " ".join(x for x in [entite.first_name, entite.last_name] if x)
    print(f"Trouvé : {nom}")
    if input("C'est bien lui ? (o/n) : ").strip().lower() not in ("o", "oui"):
        sys.exit("Annulé.")

contacts = charger()
contacts[alias] = {"id": entite.id, "nom": nom}
FICHIER.write_text(json.dumps(contacts, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Contact '{alias}' ajouté.")
