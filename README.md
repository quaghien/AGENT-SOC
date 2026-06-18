# AgentSOC

AgentSOC POC reconstruction from `agent_soc.pdf`.

The implementation is intentionally safe:

- SOC actions are always dry-run simulations.
- Single/small runs may call OpenAI with `gpt-5.4-nano` when `OPENAI_API_KEY` is configured.
- Benchmark, stress, fuzz, concurrency, and retry-heavy paths do not call OpenAI by default.

Run deterministic tests:

```powershell
cd C:\Users\hienhq\Documents\ai-lab\AGENT-SOC
uv run --project C:\Users\hienhq\Documents\ai-lab --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe pytest -m "not llm and not stress"
```

Run the paper POC with mock NCE:

```powershell
cd C:\Users\hienhq\Documents\ai-lab\AGENT-SOC
uv run --project C:\Users\hienhq\Documents\ai-lab --package agent-soc --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe python -m agent_soc.cli run --input fixtures\paper_alert.json --llm mock --artifacts output\paper_mock
```

Run with real OpenAI for a small case after filling `.env`:

```powershell
cd C:\Users\hienhq\Documents\ai-lab\AGENT-SOC
uv run --project C:\Users\hienhq\Documents\ai-lab --package agent-soc --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe python -m agent_soc.cli run --input fixtures\paper_alert.json --llm openai --artifacts output\paper_openai
```
