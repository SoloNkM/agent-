# Agent IA personnel

Un agent en Python, branché à l'API Gemini, qui travaille dans un dossier de projet : il peut lister, lire et écrire des fichiers, et lancer des commandes. Il ne fait jamais rien sans mon accord. Je peux le piloter dans le terminal ou depuis Telegram.

## Ce qu'il sait faire

- Lister un dossier et lire des fichiers du projet
- Écrire ou modifier un fichier, avec un aperçu des changements
- Lancer une commande dans le dossier du projet
- Se souvenir de la conversation en cours
- Suivre des consignes et un profil de projet (`profil.txt`)
- Répondre sur Telegram, avec deux boutons « go / non »

## Sécurité

- **Confirmation « go / non »** avant toute écriture et avant toute commande, avec le texte exact affiché. Tout ce qui n'est pas un oui clair est un non, et sans réponse sur Telegram au bout de 2 minutes, c'est un non.
- **Dossier du projet seulement** : il ne lit ni n'écrit en dehors.
- **Secrets protégés** : il ne lit jamais `.env`, et les variables contenant KEY, TOKEN, SECRET ou PASSWORD sont retirées avant chaque commande.
- **Sauvegarde automatique** de l'original dans `.sauvegardes/` avant chaque modification.
- **Fichiers de l'agent protégés** : il ne peut pas réécrire son propre code ni son journal.
- **Refus d'office** de commandes dangereuses (suppression, copie, réseau, PowerShell...) même après un « go ». C'est un filet de sécurité, pas un mur : la vraie protection est de relire chaque commande avant de répondre « go ».
- **Délai maximum de 30 secondes** par commande, qui arrête tout le processus.
- **Arrêt après 3 échecs de suite** : l'agent s'arrête et explique le problème.
- **Journal** de chaque action (`journal.log`, ignoré par Git) : date, action, cible, et ma réponse.
- **Bot Telegram** réservé à mon identifiant : les autres comptes sont ignorés.

## Installation (Windows)

```
git clone https://github.com/SoloNkM/agent-.git
cd agent-
python -m venv venv
venv\Scripts\activate
pip install google-genai python-dotenv python-telegram-bot
copy .env.example .env
```

Puis ouvre `.env` et remplis les valeurs :

- `GEMINI_API_KEY` : une clé gratuite sur aistudio.google.com
- `TELEGRAM_TOKEN` : le token donné par @BotFather (seulement pour Telegram)
- `TELEGRAM_ID` : ton identifiant Telegram, que `python id_telegram.py` affiche après avoir écrit à ton bot

## Utilisation

Lance toujours l'agent depuis le dossier du projet, car c'est son dossier de travail.

- Dans le terminal : `python agent.py` (tape `quit` pour sortir)
- Sur Telegram : `python bot_telegram.py` (le PC doit rester allumé)

## Fichiers

| Fichier | Rôle |
|---|---|
| `agent.py` | boucle de discussion dans le terminal |
| `bot_telegram.py` | bot Telegram, accès réservé à mon identifiant |
| `modele.py` | appels à Gemini, consignes, essais en cas de saturation |
| `outils.py` | les outils et toutes les protections |
| `profil.txt` | description du projet donnée à l'agent |
| `id_telegram.py` | affiche ton identifiant Telegram |

## Limites

- Le bot ne marche que si mon PC est allumé et que le script tourne.
- Pas de tests automatiques : je teste à la main, y compris les cas de sécurité.
- Projet personnel, en construction.