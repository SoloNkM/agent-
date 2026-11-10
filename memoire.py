import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent / "memoire.db"
MAX_NOTES = 50


def _ouvrir():
    c = sqlite3.connect(BASE)
    c.execute(
        "CREATE TABLE IF NOT EXISTS notes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, texte TEXT NOT NULL, date TEXT NOT NULL)"
    )
    return c


def ajouter(texte):
    with closing(_ouvrir()) as c:
        total = c.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        if total >= MAX_NOTES:
            raise ValueError(f"Mémoire pleine ({MAX_NOTES} notes). Supprime-en d'abord.")
        cur = c.execute(
            "INSERT INTO notes (texte, date) VALUES (?, ?)",
            (texte, datetime.now().strftime("%Y-%m-%d")),
        )
        c.commit()
        return cur.lastrowid


def lister():
    with closing(_ouvrir()) as c:
        return c.execute("SELECT id, texte, date FROM notes ORDER BY id").fetchall()


def supprimer(numero):
    with closing(_ouvrir()) as c:
        c.execute("DELETE FROM notes WHERE id = ?", (numero,))
        c.commit()


def notes_pour_prompt():
    texte = "\n".join(f"- {t}" for _, t, _ in lister())
    return texte[:2000]
