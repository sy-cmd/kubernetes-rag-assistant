#!/usr/bin/env python3

import sys
import argparse

from app.query import query_rag


def main():
    parser = argparse.ArgumentParser(description="k3s RAG CLI Chatbot")
    parser.add_argument("question", nargs="*", help="Question to ask")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    if args.interactive:
        print("k3s RAG Knowledge Base - Interactive Mode")
        print("Type 'exit' or 'quit' to end session")
        print("-" * 50)

        while True:
            try:
                question = input("\nYou: ").strip()
                if question.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                if not question:
                    continue

                answer, sources, chunks = query_rag(question)
                print(f"\nAnswer:\n{answer}")
                print(f"\nSources: {sources}")
                print(f"Chunks used: {chunks}")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    elif args.question:
        question = " ".join(args.question)
        try:
            answer, sources, chunks = query_rag(question)
            print(f"\nAnswer:\n{answer}")
            print(f"\nSources: {sources}")
            print(f"Chunks used: {chunks}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()