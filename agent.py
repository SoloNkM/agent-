from modele import demander


def main():
    print("Agent prêt. Tape 'quit' pour arrêter.")
    while True:
        message = input("\nToi : ").strip()
        if message.lower() in ("quit", "exit", "q"):
            print("À bientôt !")
            break
        if not message:
            continue
        try:
            reponse = demander(message)
            print(f"\nAgent : {reponse}")
        except Exception as e:
            print(f"\nErreur : {e}")


if __name__ == "__main__":
    main()