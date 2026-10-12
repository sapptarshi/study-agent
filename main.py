"""CLI entry point.

    python main.py "Help me study Neural Networks in 5 days"
    python main.py --offline "Help me study Search Algorithms in 3 days"
    python main.py            # interactive mode
"""
import argparse

from agent import Agent
from llm import get_llm


def main():
    ap = argparse.ArgumentParser(description="StudyBuddy - an agentic AI study planner")
    ap.add_argument("goal", nargs="?", help="what you want the agent to do")
    ap.add_argument("--offline", action="store_true", help="use the rule-based brain (no API key)")
    ap.add_argument("--max-steps", type=int, default=8)
    args = ap.parse_args()

    llm = get_llm(args.offline)
    print(f"Backend: {type(llm).__name__}\n")
    agent = Agent(llm, max_steps=args.max_steps)

    if args.goal:
        print("\nFINAL ANSWER:\n" + agent.run(args.goal))
        return
    print("StudyBuddy ready. Type a goal (or 'quit').")
    while (goal := input("\n> ").strip()).lower() not in {"quit", "exit"}:
        if goal:
            print("\nFINAL ANSWER:\n" + agent.run(goal))


if __name__ == "__main__":
    main()
