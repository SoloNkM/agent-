from pathlib import Path

DOSSIER_TRAVAIL = Path.cwd().resolve()
DOSSIERS_IGNORES = {"venv", ".git", "__pycache__", "node_modules"}
LIMITE_CARACTERES = 20000


def chemin_sur(chemin):
    """Transforme un chemin en chemin complet, ou refuse s'il est interdit."""
    complet = (DOSSIER_TRAVAIL / chemin).resolve()
    if not complet.is_relative_to(DOSSIER_TRAVAIL):
        raise ValueError("Accès refusé : ce chemin est en dehors du dossier de travail.")
    if complet.name.startswith(".env"):
        raise ValueError("Accès refusé : ce fichier est protégé (secrets).")
    return complet


def lister_dossier(chemin="."):
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


def lire_fichier(chemin):
    """Lit un fichier texte (tronqué s'il est très long)."""
    fichier = chemin_sur(chemin)
    if not fichier.is_file():
        raise ValueError(f"'{chemin}' n'est pas un fichier.")
    texte = fichier.read_text(encoding="utf-8", errors="replace")
    if len(texte) > LIMITE_CARACTERES:
        texte = texte[:LIMITE_CARACTERES] + "\n[... fichier tronqué ...]"
    return texte