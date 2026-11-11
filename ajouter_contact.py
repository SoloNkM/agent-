import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon import utils
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


choix_type = input("Ajouter une personne (p) ou un groupe (g) ? ").strip().lower()
alias = input("Nom court (ex: nathan, cidteam) : ").strip().lower()
if choix_type not in ("p", "g") or not alias:
    sys.exit("Choix invalide ou nom vide.")

with TelegramClient("agent", api_id, api_hash) as client:
    if choix_type == "p":
        cible = input("Son @pseudo Telegram, son numéro (+225...) ou 'me' pour toi : ").strip()
        if not cible:
            sys.exit("Rien saisi.")
        try:
            entite = client.get_entity(cible)
        except Exception:
            sys.exit("Contact introuvable. Vérifie le pseudo ou le numéro.")
        if not isinstance(entite, User) or entite.bot:
            sys.exit("Seules les personnes sont acceptées ici.")
        nom = " ".join(x for x in [entite.first_name, entite.last_name] if x)
        print(f"Trouvé : {nom}")
        if input("C'est bien lui ? (o/n) : ").strip().lower() not in ("o", "oui"):
            sys.exit("Annulé.")
        entree = {"id": entite.id, "nom": nom}
    else:
        groupes = [d for d in client.iter_dialogs() if d.is_group]
        if not groupes:
            sys.exit("Aucun groupe trouvé dans tes conversations.")
        for i, d in enumerate(groupes, 1):
            print(f"{i}. {d.name}")
        choix = input("Numéro du groupe : ").strip()
        if not choix.isdigit() or not 1 <= int(choix) <= len(groupes):
            sys.exit("Choix invalide.")
        d = groupes[int(choix) - 1]
        try:
            membres = client.get_participants(d.entity, limit=0).total
        except Exception:
            membres = None
        print(f"Groupe : {d.name}" + (f" ({membres} membres)" if membres else ""))
        if input("C'est bien ce groupe ? (o/n) : ").strip().lower() not in ("o", "oui"):
            sys.exit("Annulé.")
        entree = {
            "id": utils.get_peer_id(d.entity),
            "nom": d.name,
            "type": "groupe",
            "membres": membres,
        }

contacts = charger()
contacts[alias] = entree
FICHIER.write_text(json.dumps(contacts, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"'{alias}' ajouté.")