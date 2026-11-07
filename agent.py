from google.genai import types

import outils
from modele import demander


def main():
    print("Agent prêt. Tape 'quit' pour arrêter.")
    historique = []
    while True:
        message = input("\nToi : ").strip()
        if message.lower() in ("quit", "exit", "q"):
            print("À bientôt !")
            break
        if not message:
            continue
        outils.reinitialiser_echecs()
        historique.append(
            types.Content(role="user", parts=[types.Part.from_text(text=message)])
        )
        try:
            reponse = demander(historique)
            historique.append(
                types.Content(role="model", parts=[types.Part.from_text(text=reponse)])
            )
            print(f"\nAgent : {reponse}")
        except Exception as e:
            historique.pop()
            print(f"\nErreur : {e}")


if __name__ == "__main__":
    main()