"""Tools the agent can call. Each tool = JSON schema (for the LLM) + Python function."""
import ast
import json
import operator
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

NOTES_DIR = Path("notes")

# ---------- tool implementations ----------

def get_today() -> str:
    return date.today().isoformat()


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.Mod: operator.mod}


def calculator(expression: str) -> str:
    """Safely evaluate arithmetic (no eval())."""
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        raise ValueError("unsupported expression")
    try:
        return str(ev(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"ERROR: {e}"


def search_wikipedia(query: str) -> str:
    """Fetch a short summary from Wikipedia's public REST API."""
    try:
        url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
               + urllib.parse.quote(query.replace(" ", "_")))
        req = urllib.request.Request(url, headers={"User-Agent": "study-agent/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.load(r)
        return data.get("extract", "No summary found.")
    except Exception as e:
        return f"ERROR: could not reach Wikipedia ({e}). Continue using own knowledge."


def create_study_plan(topic: str, days: int) -> str:
    """Split a topic into a day-by-day plan with revision and a mock test."""
    days = max(1, min(int(days), 30))
    phases = ["Core concepts & definitions", "Worked examples & algorithms",
              "Practice problems", "Previous-year questions", "Weak-spot revision"]
    start = date.today()
    lines = []
    for i in range(days):
        if i == days - 1 and days > 1:
            focus = "Mock test + final revision"
        else:
            focus = phases[i % len(phases)] if days > 2 else phases[i]
        lines.append(f"Day {i+1} ({(start + timedelta(days=i)).isoformat()}): {topic} - {focus}")
    return "\n".join(lines)


def save_note(title: str, content: str) -> str:
    NOTES_DIR.mkdir(exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title).strip().replace(" ", "_")
    path = NOTES_DIR / f"{safe}.md"
    path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
    return f"Saved note to {path}"


def recall_notes(query: str) -> str:
    """Long-term memory: keyword search over previously saved notes."""
    if not NOTES_DIR.exists():
        return "No notes saved yet."
    hits = []
    for p in NOTES_DIR.glob("*.md"):
        text = p.read_text(encoding="utf-8")
        if query.lower() in text.lower() or query.lower() in p.stem.lower():
            hits.append(f"[{p.name}] {text[:300]}")
    return "\n---\n".join(hits) or "No matching notes."


# ---------- registry (schemas follow the Anthropic tool-use format) ----------

def _schema(name, description, props, required):
    return {"name": name, "description": description,
            "input_schema": {"type": "object", "properties": props, "required": required}}

TOOL_SCHEMAS = [
    _schema("get_today", "Get today's date (ISO format).", {}, []),
    _schema("calculator", "Evaluate an arithmetic expression, e.g. '3*4+2'.",
            {"expression": {"type": "string"}}, ["expression"]),
    _schema("search_wikipedia", "Get a short factual summary of a topic from Wikipedia.",
            {"query": {"type": "string"}}, ["query"]),
    _schema("create_study_plan", "Create a day-by-day study plan for a topic.",
            {"topic": {"type": "string"}, "days": {"type": "integer"}}, ["topic", "days"]),
    _schema("save_note", "Save a markdown note to long-term memory.",
            {"title": {"type": "string"}, "content": {"type": "string"}}, ["title", "content"]),
    _schema("recall_notes", "Search previously saved notes by keyword.",
            {"query": {"type": "string"}}, ["query"]),
]

TOOL_FUNCS = {f.__name__: f for f in [get_today, calculator, search_wikipedia,
                                      create_study_plan, save_note, recall_notes]}


def run_tool(name: str, args: dict) -> str:
    if name not in TOOL_FUNCS:
        return f"ERROR: unknown tool {name}"
    try:
        return str(TOOL_FUNCS[name](**args))
    except Exception as e:  # the agent sees the error and can recover
        return f"ERROR: {type(e).__name__}: {e}"
