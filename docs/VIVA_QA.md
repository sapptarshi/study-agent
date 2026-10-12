# Viva cheat-sheet (read this before you meet sir)

**1. What is an AI agent?**
A system that perceives its environment, reasons, and takes actions through tools to achieve a goal - in a loop - rather than answering one prompt once. (Russell & Norvig: perceive -> act via sensors/actuators; here the "sensors" are tool observations, the "actuators" are tool calls.)

**2. Which agent type is this?**
A **goal-based, utility-aware agent with memory**. It has goals, internal state (messages + notes), and chooses actions to reach the goal. With the LLM backend it behaves like a **ReAct** agent (Reason + Act).

**3. PEAS description**
- **P**erformance: valid plan produced, note saved, goal finished within step limit
- **E**nvironment: user goal, Wikipedia API, local file system (notes)
- **A**ctuators: tool calls (create plan, save note)
- **S**ensors: tool observations, user input, past notes

**4. Environment properties**
Partially observable, single-agent, stochastic (network/LLM), sequential, dynamic (dates change), discrete.

**5. How does the loop work?**
Controller sends goal + tool schemas to the LLM -> LLM returns a tool call -> controller executes it -> result appended as an observation -> repeat until the LLM returns plain text (goal done) or `max_steps` is hit.

**6. How does it handle failure?**
Tools never raise; they return `ERROR: ...` strings. The model sees the error and adapts. In my demo, Wikipedia being unreachable did not crash the run; the plan was still produced. Also a hard step limit prevents infinite loops.

**7. Memory?**
Short-term: message list for the current run. Long-term: markdown notes on disk; relevant ones (keyword-scored) are injected into the system prompt on the next run.

**8. Why an offline mode?**
Reproducible demos and unit tests without an API key or network; also shows the agent *architecture* is independent of the LLM (Strategy pattern: `ClaudeLLM` / `OfflineLLM` share one `step()` interface).

**9. Security choices**
Calculator parses the AST and whitelists operators (no `eval`); API key from environment variable, `.env` is git-ignored; bounded steps.

**10. Limitations / future work**
Keyword memory (upgrade to embeddings/vector DB), single agent (upgrade to planner + critic multi-agent), no UI yet (Streamlit), no guardrail on note size.

**Demo script (2 minutes):**
1. Show the Mermaid architecture on GitHub.
2. Run `python main.py "Help me study Neural Networks in 5 days"` and point at each step line.
3. Run it again with "revise Neural Networks" - show it recalls the saved note (long-term memory).
4. Run `pytest -q` - 6 tests green.
5. Open `logs/trace.jsonl` to show full transparency.
