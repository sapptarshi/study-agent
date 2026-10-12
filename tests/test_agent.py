import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import tools
import memory
import agent as agent_mod
from agent import Agent
from llm import OfflineLLM


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Run every test in a temp dir so notes/ and logs/ don't pollute the repo."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tools, "NOTES_DIR", Path("notes"))
    monkeypatch.setattr(memory, "NOTES_DIR", Path("notes"))
    monkeypatch.setattr(agent_mod, "LOG_FILE", Path("logs/trace.jsonl"))
    # avoid real network calls in tests
    monkeypatch.setitem(tools.TOOL_FUNCS, "search_wikipedia", lambda query: f"Summary of {query}.")


def test_calculator_safe():
    assert tools.calculator("3*4+2") == "14"
    assert tools.calculator("__import__('os').system('ls')").startswith("ERROR")


def test_study_plan_length():
    plan = tools.create_study_plan("Graphs", 5).splitlines()
    assert len(plan) == 5 and "Mock test" in plan[-1]


def test_unknown_tool_returns_error():
    assert tools.run_tool("nope", {}).startswith("ERROR")


def test_agent_completes_goal_and_saves_note():
    result = Agent(OfflineLLM(), verbose=False).run("Help me study Neural Networks in 4 days")
    assert "Neural Networks" in result
    assert list(Path("notes").glob("*.md")), "agent should have saved a note"
    assert Path("logs/trace.jsonl").exists()


def test_long_term_memory_recall():
    Agent(OfflineLLM(), verbose=False).run("Help me study Neural Networks in 3 days")
    assert "Neural Networks" in tools.recall_notes("Neural")
    assert "Neural" in memory.load_relevant_notes("revise Neural Networks")


def test_max_steps_guard():
    class Looper:
        def step(self, system, messages, tools_):
            return {"text": "", "tool_calls": [{"id": "x", "name": "get_today", "input": {}}]}
    assert "maximum" in Agent(Looper(), max_steps=3, verbose=False).run("loop forever")
