import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
import outils

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=30000),  # 30 secondes max par essai
)

MODELE = "gemini-3.5-flash-lite"

CONFIG = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="low"),
    tools=[outils.lister_dossier, outils.lire_fichier, outils.ecrire_fichier],
)


def demander(message, essais=4):
    for i in range(essais):
        try:
            reponse = client.models.generate_content(
                model=MODELE,
                contents=message,
                config=CONFIG,
            )
            return reponse.text
        except errors.ServerError as e:
            attente = 3 * (i + 1)
            print(f"Google est surchargé (essai {i + 1}/{essais}). Nouvel essai dans {attente}s...")
            if i == essais - 1:
                raise
            time.sleep(attente)