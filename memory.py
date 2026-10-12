"""Memory for the agent.

Short-term memory : the running message list for the current goal (managed in agent.py).
Long-term memory  : markdown notes on disk (written by the save_note tool).
                    Relevant notes are retrieved at the start of every run and
                    injected into the system prompt, so the agent "remembers"
                    what it did in earlier sessions.
"""
from pathlib import Path

NOTES_DIR = Path("notes")


def load_relevant_notes(goal: str, limit: int = 3, max_chars: int = 400) -> str:
    if not NOTES_DIR.exists():
        return ""
    words = {w.lower() for w in goal.replace(",", " ").split() if len(w) > 3}
    scored = []
    for p in NOTES_DIR.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        score = sum(1 for w in words if w in text.lower() or w in p.stem.lower())
        if score:
            scored.append((score, p.name, text[:max_chars]))
    scored.sort(reverse=True)
    return "\n---\n".join(f"[{name}]\n{snippet}" for _, name, snippet in scored[:limit])
