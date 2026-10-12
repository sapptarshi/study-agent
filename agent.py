"""The agent loop:  PLAN -> ACT (tool call) -> OBSERVE (tool result) -> repeat -> FINAL ANSWER.

The agent is *agentic* because the model, not the programmer, decides which tool
to call next and when the goal is complete. The loop is bounded by max_steps and
every step is written to logs/trace.jsonl for transparency.
"""
import json
from datetime import datetime
from pathlib import Path

from memory import load_relevant_notes
from tools import TOOL_SCHEMAS, run_tool

SYSTEM_PROMPT = """You are StudyBuddy, an autonomous study-planning agent.
Given a goal, break it into steps and use your tools to achieve it:
1. get_today for the date, 2. search_wikipedia to research the topic,
3. create_study_plan for a day-by-day schedule, 4. save_note to store the result.
Use recall_notes to check past work. Use calculator for any arithmetic.
If a tool returns an ERROR, adapt and continue. When the goal is complete, reply with a
short final answer and no tool call."""

LOG_FILE = Path("logs/trace.jsonl")


class Agent:
    def __init__(self, llm, max_steps: int = 8, verbose: bool = True):
        self.llm, self.max_steps, self.verbose = llm, max_steps, verbose

    def _log(self, record: dict):
        LOG_FILE.parent.mkdir(exist_ok=True)
        record["ts"] = datetime.now().isoformat(timespec="seconds")
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def run(self, goal: str) -> str:
        memory = load_relevant_notes(goal)
        system = SYSTEM_PROMPT + (f"\n\nRelevant past notes:\n{memory}" if memory else "")
        messages = [{"role": "user", "content": goal}]  # short-term memory

        for step in range(1, self.max_steps + 1):
            out = self.llm.step(system, messages, TOOL_SCHEMAS)

            blocks = []
            if out["text"]:
                blocks.append({"type": "text", "text": out["text"]})
            for c in out["tool_calls"]:
                blocks.append({"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["input"]})
            messages.append({"role": "assistant", "content": blocks})

            if not out["tool_calls"]:  # goal reached
                self._log({"step": step, "final": out["text"]})
                return out["text"]

            results = []
            for c in out["tool_calls"]:
                obs = run_tool(c["name"], c["input"])
                if self.verbose:
                    print(f"[step {step}] {c['name']}({c['input']}) -> {obs[:120]!r}")
                self._log({"step": step, "tool": c["name"], "input": c["input"], "observation": obs})
                results.append({"type": "tool_result", "tool_use_id": c["id"], "content": obs})
            messages.append({"role": "user", "content": results})

        return "Stopped: reached the maximum number of steps without finishing."
