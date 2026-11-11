import asyncio
import concurrent.futures
import contextlib
import os
import sys
import uuid

from dotenv import load_dotenv
from google.genai import types
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
try:
    MON_ID = int(os.getenv("TELEGRAM_ID", ""))
except ValueError:
    MON_ID = None
if not TOKEN or not MON_ID:
    print("Il manque TELEGRAM_TOKEN ou TELEGRAM_ID (un nombre) dans .env.")
    sys.exit(1)

import outils
from modele import demander, transcrire

DELAI_REPONSE = 120
historique = []
attente = {}
occupe = asyncio.Lock()
boucle = None
application = None


class Tampon:
    """Garde ce que l'agent affiche (aperçus, commandes) pour te l'envoyer."""
    encoding = "utf-8"

    def __init__(self, vrai):
        self.vrai = vrai
        self.texte = ""

    def write(self, s):
        self.texte += s
        try:
            self.vrai.write(s)
        except Exception:
            pass
        return len(s)

    def flush(self):
        try:
            self.vrai.flush()
        except Exception:
            pass

    def isatty(self):
        return False

    def prendre(self):
        t = self.texte.strip()
        self.texte = ""
        return t[-3000:]


TAMPON = Tampon(sys.stdout)


def confirmer_telegram(question):
    """Appelée par l'agent : envoie les boutons go / non et attend ta réponse."""
    detail = TAMPON.prendre() or "L'agent demande ton accord."
    cid = uuid.uuid4().hex[:8]
    futur = concurrent.futures.Future()
    attente[cid] = futur
    clavier = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ go", callback_data="go:" + cid),
        InlineKeyboardButton("❌ non", callback_data="non:" + cid),
    ]])
    texte = f"{detail}\n\n{question} (sans réponse en {DELAI_REPONSE} s = non)"
    try:
        asyncio.run_coroutine_threadsafe(
            application.bot.send_message(
                chat_id=MON_ID, text=texte[:4000], reply_markup=clavier
            ),
            boucle,
        ).result(timeout=30)
        return futur.result(timeout=DELAI_REPONSE)
    except Exception:
        return False
    finally:
        attente.pop(cid, None)


def travail(message):
    outils.reinitialiser_echecs()
    TAMPON.texte = ""
    historique.append(
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    )
    try:
        with contextlib.redirect_stdout(TAMPON):
            reponse = demander(historique)
        reponse = reponse or "(pas de réponse)"
        historique.append(
            types.Content(role="model", parts=[types.Part.from_text(text=reponse)])
        )
        return reponse
    except Exception as e:
        historique.pop()
        return f"Erreur : {type(e).__name__} : {str(e)[:300]}"


async def demarrer(update, context):
    await update.message.reply_text(
        "Agent prêt. Écris-moi ce que tu veux : je te demanderai ton accord "
        "(boutons go / non) avant toute action. /reset efface la mémoire."
    )


async def reset(update, context):
    historique.clear()
    outils.reinitialiser_echecs()
    await update.message.reply_text("Mémoire effacée.")


async def message(update, context):
    if occupe.locked():
        await update.message.reply_text("Je suis encore sur ta demande d'avant. Patiente un instant.")
        return
    async with occupe:
        await context.bot.send_chat_action(chat_id=MON_ID, action="typing")
        reponse = await asyncio.to_thread(travail, update.message.text.strip())
    for i in range(0, len(reponse), 4000):
        await update.message.reply_text(reponse[i:i + 4000])


DUREE_MAX_VOCAL = 120


async def vocal(update, context):
    v = update.message.voice
    if v.duration and v.duration > DUREE_MAX_VOCAL:
        await update.message.reply_text(f"Vocal trop long (maximum {DUREE_MAX_VOCAL} secondes).")
        return
    if occupe.locked():
        await update.message.reply_text("Je suis encore sur ta demande d'avant. Patiente un instant.")
        return
    async with occupe:
        try:
            fichier = await context.bot.get_file(v.file_id)
            octets = bytes(await fichier.download_as_bytearray())
            texte = await asyncio.to_thread(transcrire, octets, v.mime_type or "audio/ogg")
        except Exception as e:
            await update.message.reply_text(f"Je n'ai pas pu comprendre le vocal : {type(e).__name__}")
            return
        if not texte:
            await update.message.reply_text("Je n'ai rien compris dans ce vocal. Réessaie ou écris-moi.")
            return
        texte = texte[:1500]
        await update.message.reply_text("🎙️ J'ai compris : " + texte)
        reponse = await asyncio.to_thread(travail, texte)
    for i in range(0, len(reponse), 4000):
        await update.message.reply_text(reponse[i:i + 4000])


async def bouton(update, context):
    q = update.callback_query
    if q.from_user.id != MON_ID:
        return
    choix, _, cid = q.data.partition(":")
    futur = attente.get(cid)
    if futur is None or futur.done():
        await q.answer("Demande expirée.")
        return
    futur.set_result(choix == "go")
    await q.answer("Noté.")
    await q.edit_message_reply_markup(reply_markup=None)
    await context.bot.send_message(chat_id=MON_ID, text="→ " + ("go" if choix == "go" else "non"))


async def apres_demarrage(app):
    global boucle
    boucle = asyncio.get_running_loop()
    try:
        await app.bot.send_message(chat_id=MON_ID, text="Agent en ligne ✅")
        print("Bot en ligne. Écris-lui sur Telegram. Ctrl+C pour arrêter.")
    except Exception:
        print("Impossible d'écrire à TELEGRAM_ID : vérifie que c'est le numéro donné par id_telegram.py.")
        os._exit(1)


def main():
    global application
    application = (
        Application.builder()
        .token(TOKEN)
        .concurrent_updates(True)
        .post_init(apres_demarrage)
        .build()
    )
    seulement_moi = filters.User(user_id=MON_ID) & filters.ChatType.PRIVATE
    application.add_handler(CommandHandler("start", demarrer, filters=seulement_moi))
    application.add_handler(CommandHandler("reset", reset, filters=seulement_moi))
    application.add_handler(
        MessageHandler(seulement_moi & filters.TEXT & ~filters.COMMAND, message)
    )
    application.add_handler(MessageHandler(seulement_moi & filters.VOICE, vocal))
    application.add_handler(CallbackQueryHandler(bouton))
    outils.CONFIRMATEUR = confirmer_telegram
    application.run_polling()


if __name__ == "__main__":
    main()