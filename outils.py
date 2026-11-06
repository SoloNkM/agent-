import difflib
from datetime import datetime
from pathlib import Path

DOSSIER_TRAVAIL = Path.cwd().resolve()
DOSSIERS_IGNORES = {"venv", ".git", "__pycache__", "node_modules", ".sauvegardes"}
FICHIERS_PROTEGES = {"agent.py", "modele.py", "outils.py", ".gitignore"}
LIMITE_CARACTERES = 20000
LIMITE_ECRITURE = 100000
DOSSIER_SAUVEGARDES = DOSSIER_TRAVAIL / ".sauvegardes"


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
        return "Écriture refusée par l'utilisateur : rien n'a été modifié."

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