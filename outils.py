import difflib
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

DOSSIER_TRAVAIL = Path.cwd().resolve()
DOSSIERS_IGNORES = {"venv", ".git", "__pycache__", "node_modules", ".sauvegardes"}
FICHIERS_PROTEGES = {"agent.py", "modele.py", "outils.py", ".gitignore", "journal.log"}
LIMITE_CARACTERES = 20000
LIMITE_ECRITURE = 100000
DOSSIER_SAUVEGARDES = DOSSIER_TRAVAIL / ".sauvegardes"
DELAI_COMMANDE = 30
LIMITE_SORTIE = 5000

# Commandes refusées d'office, même si l'utilisateur dit "go".
MOTS_INTERDITS = [
    "del", "erase", "rmdir", "rd", "rm", "format", "shutdown", "diskpart",
    "taskkill", "reg", "powershell", "pwsh", "curl", "wget", "move", "ren",
    "rename", "copy", "xcopy", "robocopy",
]
FRAGMENTS_INTERDITS = [
    ".env", "api_key", "gemini", "git reset", "git clean", "--force", ">",
]


def chemin_sur(chemin):
    """Transforme un chemin en chemin complet, ou refuse s'il est interdit."""
    complet = (DOSSIER_TRAVAIL / chemin).resolve()
    if not complet.is_relative_to(DOSSIER_TRAVAIL):
        raise ValueError("Accès refusé : ce chemin est en dehors du dossier de travail.")
    if complet.name.lower().startswith(".env"):
        raise ValueError("Accès refusé : ce fichier est protégé (secrets).")
    return complet


def chemin_ecriture(chemin):
    """Comme chemin_sur, avec des interdictions en plus pour l'écriture."""
    complet = chemin_sur(chemin)
    if complet.is_dir():
        raise ValueError(f"'{chemin}' est un dossier, pas un fichier.")
    relatif = complet.relative_to(DOSSIER_TRAVAIL)
    protege_dossiers = {d.lower() for d in DOSSIERS_IGNORES}
    protege_fichiers = {f.lower() for f in FICHIERS_PROTEGES}
    if relatif.parts[0].lower() in protege_dossiers:
        raise ValueError("Accès refusé : ce dossier est protégé.")
    if len(relatif.parts) == 1 and relatif.name.lower() in protege_fichiers:
        raise ValueError("Accès refusé : ce fichier fait partie du code de l'agent.")
    return complet


def lister_dossier(chemin: str = "."):
    """Liste le contenu d'un dossier (les dossiers finissent par /)."""
    dossier = chemin_sur(chemin)
    if not dossier.is_dir():
        raise ValueError(f"'{chemin}' n'est pas un dossier.")
    lignes = []
    for element in sorted(dossier.iterdir()):
        if element.name in DOSSIERS_IGNORES:
            continue
        lignes.append(element.name + ("/" if element.is_dir() else ""))
    return "\n".join(lignes) if lignes else "(dossier vide)"


def lire_fichier(chemin: str):
    """Lit un fichier texte (tronqué s'il est très long)."""
    fichier = chemin_sur(chemin)
    if not fichier.is_file():
        raise ValueError(f"'{chemin}' n'est pas un fichier.")
    texte = fichier.read_text(encoding="utf-8", errors="replace")
    if len(texte) > LIMITE_CARACTERES:
        texte = texte[:LIMITE_CARACTERES] + "\n[... fichier tronqué ...]"
    return texte


FICHIER_JOURNAL = DOSSIER_TRAVAIL / "journal.log"


def noter(action, cible, decision):
    """Ajoute une ligne au journal : date | action | cible | décision."""
    cible = " ".join(str(cible).split())
    ligne = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {action} | {cible} | {decision}\n"
    try:
        with open(FICHIER_JOURNAL, "a", encoding="utf-8") as f:
            f.write(ligne)
    except OSError:
        pass


def confirmer(question):
    """Pose une question à l'utilisateur ; tout ce qui n'est pas un oui clair = non."""
    reponse = input(f"\n{question} (go / non) : ").strip().lower()
    return reponse in ("go", "ok", "oui", "o", "ouais", "yes", "vas-y")


def apercu_modification(ancien, nouveau):
    """Texte montrant ce qui va changer."""
    if ancien is None:
        lignes = nouveau.splitlines()[:20]
        return "Nouveau fichier. Début du contenu :\n" + "\n".join(lignes)
    diff = list(
        difflib.unified_diff(
            ancien.splitlines(), nouveau.splitlines(), "avant", "après", lineterm=""
        )
    )
    if not diff:
        return "Aucun changement dans le contenu."
    if len(diff) > 40:
        diff = diff[:40] + ["[... aperçu tronqué ...]"]
    return "\n".join(diff)


def ecrire_fichier(chemin: str, contenu: str):
    """Crée ou remplace un fichier texte, après confirmation de l'utilisateur."""
    fichier = chemin_ecriture(chemin)
    if len(contenu) > LIMITE_ECRITURE:
        raise ValueError("Contenu trop long pour être écrit d'un coup.")
    existe = fichier.is_file()
    ancien = fichier.read_text(encoding="utf-8", errors="replace") if existe else None

    print("\n--- Demande de l'agent ---")
    print(f"Écrire dans : {chemin}")
    print(apercu_modification(ancien, contenu))

    if not confirmer("Alors, on y va ?"):
        noter("ecriture", chemin, "non")
        return "Écriture refusée par l'utilisateur : rien n'a été modifié."
    noter("ecriture", chemin, "go")

    nom_copie = None
    if existe:
        DOSSIER_SAUVEGARDES.mkdir(exist_ok=True)
        horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
        nom_base = "__".join(fichier.relative_to(DOSSIER_TRAVAIL).parts)
        nom_copie = f"{nom_base}.{horodatage}.bak"
        (DOSSIER_SAUVEGARDES / nom_copie).write_bytes(fichier.read_bytes())

    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text(contenu, encoding="utf-8")
    if nom_copie:
        return f"Fichier '{chemin}' écrit. Original sauvegardé dans .sauvegardes/{nom_copie}."
    return f"Fichier '{chemin}' créé."


def verifier_commande(commande):
    """Refuse d'office les commandes dangereuses (filet de sécurité)."""
    basse = commande.lower()
    for fragment in FRAGMENTS_INTERDITS:
        if fragment in basse:
            raise ValueError(f"Commande refusée d'office (contient '{fragment}').")
    for mot in MOTS_INTERDITS:
        if re.search(rf"(?<![\w-]){re.escape(mot)}(?![\w-])", basse):
            raise ValueError(f"Commande refusée d'office (contient '{mot}').")


def lancer_commande(commande: str):
    """Lance une commande dans le dossier de travail, après confirmation."""
    commande = commande.strip()
    if not commande:
        raise ValueError("Commande vide.")
    verifier_commande(commande)

    print("\n--- Demande de l'agent ---")
    print(f"Lancer la commande : {commande}")
    print(f"Dans le dossier : {DOSSIER_TRAVAIL}")
    if not confirmer("Alors, on y va ?"):
        noter("commande", commande, "non")
        return "Commande refusée par l'utilisateur : rien n'a été lancé."
    noter("commande", commande, "go")

    # On retire les variables secrètes pour que la commande ne puisse pas les lire.
    secrets = ("KEY", "TOKEN", "SECRET", "PASSWORD")
    environnement = {
        nom: valeur
        for nom, valeur in os.environ.items()
        if not any(s in nom.upper() for s in secrets)
    }

    processus = subprocess.Popen(
        commande,
        shell=True,
        cwd=DOSSIER_TRAVAIL,
        env=environnement,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    try:
        sortie, _ = processus.communicate(timeout=DELAI_COMMANDE)
    except subprocess.TimeoutExpired:
        # On tue tout l'arbre de processus (cmd + ce qu'il a lancé).
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(processus.pid)],
            capture_output=True,
        )
        try:
            processus.communicate(timeout=5)
        except Exception:
            pass
        return f"Commande arrêtée : elle dépassait {DELAI_COMMANDE} secondes."

    sortie = sortie or ""
    if len(sortie) > LIMITE_SORTIE:
        sortie = sortie[:LIMITE_SORTIE] + "\n[... sortie tronquée ...]"
    return f"Code de retour : {processus.returncode}\n{sortie.strip() or '(aucune sortie)'}"
