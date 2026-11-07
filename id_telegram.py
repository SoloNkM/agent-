import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_TOKEN")

try:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.load(r)
except Exception:
    print("Erreur : impossible de joindre Telegram. Vérifie TELEGRAM_TOKEN dans .env.")
    raise SystemExit(1)

trouves = set()
for u in data.get("result", []):
    m = u.get("message")
    if m:
        trouves.add((m["from"]["id"], m["from"].get("first_name", "")))

if trouves:
    for identifiant, prenom in trouves:
        print(f"Identifiant Telegram : {identifiant} ({prenom})")
else:
    print("Aucun message trouvé. Écris d'abord « salut » à ton bot, puis relance.")