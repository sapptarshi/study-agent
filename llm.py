"""LLM backends. Both expose the same interface:

    backend.step(system, messages, tools) -> {"text": str, "tool_calls": [{"id","name","input"}]}

* ClaudeLLM  - real reasoning via the Anthropic Messages API (tool use).
* OfflineLLM - deterministic rule-based "brain" so the project runs and is
               testable with no API key (useful for demos and unit tests).
"""
import os
import re


class ClaudeLLM:
    def __init__(self, model: str | None = None):
        import anthropic  # imported lazily so offline mode needs no dependency
        self.client = anthropic.Anthropic()
        self.model = model or os.getenv("AGENT_MODEL", "claude-sonnet-5-5")

    def step(self, system, messages, tools):
        resp = self.client.messages.create(
            model=self.model, max_tokens=1500, system=system,
            messages=messages, tools=tools)
        text, calls = "", []
        for block in resp.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                calls.append({"id": block.id, "name": block.name, "input": block.input})
        return {"text": text, "tool_calls": calls}


class OfflineLLM:
    """Fixed plan: date -> research -> study plan -> save note -> final answer."""

    def step(self, system, messages, tools):
        goal = messages[0]["content"]
        topic = self._topic(goal)
        days = self._days(goal)
        results = self._tool_results(messages)
        n = len(results)

        if n == 0:
            return self._call("get_today", {})
        if n == 1:
            return self._call("search_wikipedia", {"query": topic})
        if n == 2:
            return self._call("create_study_plan", {"topic": topic, "days": days})
        if n == 3:
            summary, plan = results[1], results[2]
            if summary.startswith("ERROR"):  # research failed -> recover gracefully
                summary = f"(Online research unavailable; plan generated from general knowledge of {topic}.)"
            return self._call("save_note", {
                "title": f"{topic} study plan",
                "content": f"## Overview\n{summary}\n\n## Plan ({days} days)\n{plan}"})
        return {"text": (f"Done. I researched '{topic}', built a {days}-day plan and saved it "
                         f"to notes/. Plan:\n{results[2]}"), "tool_calls": []}

    @staticmethod
    def _call(name, args):
        return {"text": f"Calling {name}", "tool_calls": [
            {"id": f"offline_{name}", "name": name, "input": args}]}

    @staticmethod
    def _tool_results(messages):
        out = []
        for m in messages:
            if m["role"] == "user" and isinstance(m["content"], list):
                out += [b["content"] for b in m["content"] if b.get("type") == "tool_result"]
        return out

    @staticmethod
    def _days(goal):
        m = re.search(r"(\d+)\s*[- ]?\s*day", goal, re.I)
        return int(m.group(1)) if m else 7

    @staticmethod
    def _topic(goal):
        m = re.search(r"(?:study|learn|prepare(?: for)?|revise|master)\s+(.+?)(?:\s+in\s+\d+|\s+for\s+\d+|[.,]|$)",
                      goal, re.I)
        return (m.group(1) if m else goal).strip()


def get_llm(offline: bool = False):
    if offline or not os.getenv("ANTHROPIC_API_KEY"):
        return OfflineLLM()
    return ClaudeLLM()
