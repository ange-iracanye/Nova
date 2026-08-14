from backend.engine import NovaEngine


def main():
    print("=" * 40)
    print("        NOVA Student AI")
    print("=" * 40)
    print()

    engine = NovaEngine()

    print("Nova is ready.")
    print()

    while True:

        user = input("You: ")

        if user.lower() in ["exit", "quit"]:
            print("\nNova: Goodbye!")
            break

        answer = engine.reply(user)

        print(f"\nNova: {answer}\n")


if __name__ == "__main__":
    main()