# AgentSOC POC Implementation Plan

## Summary

Phục chế AgentSOC POC theo paper `agent_soc.pdf` trong thư mục `AGENT-SOC`.
Mục tiêu là tái tạo pipeline Sense-Reason-Act an toàn, quan sát được, có test, và không
thực hiện hành động SOC thật trên máy hoặc hệ thống ngoài.

Pipeline:

```text
RawAlert
 -> Perception
 -> Incident
 -> Narrative Construction Engine
 -> Hypotheses
 -> Semantic Simulation Engine
 -> Feasible hypotheses
 -> Response Selection and Evaluation Module
 -> Ranked actions
 -> Dry-run playbook execution
 -> Monitoring
 -> Knowledge-store update
```

## Safety And Env Gate

- Mọi action SOC luôn là dry-run. Không gọi SIEM, EDR, IAM, SOAR, firewall, registry,
  service control, hoặc network command thật.
- OpenAI model mặc định là `gpt-5.4-nano`.
- Small run có thể gọi OpenAI thật khi có `OPENAI_API_KEY`.
- Benchmark, stress, fuzz, concurrency, retry-heavy path mặc định không gọi OpenAI.
- `.env.example` là hợp đồng env. Nếu sprint mới cần env thật, cập nhật file này và
  yêu cầu người dùng điền env trước khi chạy phần thật.

Env hiện có:

```text
OPENAI_API_KEY=
AGENTSOC_LLM_MODEL=gpt-5.4-nano
AGENTSOC_LLM_MODE=auto
AGENTSOC_MAX_LLM_CALLS=30
AGENTSOC_ALLOW_STRESS_LLM=false
AGENTSOC_ARTIFACTS_DIR=output
```

## Public Interfaces

Package: `AGENT-SOC/src/agent_soc`.

CLI:

```powershell
uv run --project C:\Users\hienhq\Documents\ai-lab --package agent-soc --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe python -m agent_soc.cli run --input fixtures\paper_alert.json --llm mock --artifacts output\paper_mock
uv run --project C:\Users\hienhq\Documents\ai-lab --package agent-soc --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe python -m agent_soc.cli run --input fixtures\paper_alert.json --llm openai --artifacts output\paper_openai
uv run --project C:\Users\hienhq\Documents\ai-lab --package agent-soc --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe python -m agent_soc.cli benchmark --events fixtures\lanl_sample.csv --limit 5000 --concurrency 8 --artifacts output\bench
```

Core contracts:

- `RawAlert`, `Incident`
- `AttackHypothesis`, `FeasibilityResult`
- `DefensiveAction`, `RankedAction`
- `Playbook`, `ExecutionRecord`
- `MonitoringResult`, `CycleResult`

## Paper POC Acceptance

The deterministic mock POC must reproduce the key paper-style flow:

- Alert: `user123`, `ws-fin-27`, `srv-fin-03`, `Kerberos TGT Request`, `Success`,
  `2023-11-14 13:22:41`.
- Incident: `INC-POC-001`.
- NCE hypotheses: `H1`, `H2`, `H3`.
- SSE: `H1` accepted, `H2` conditional, `H3` rejected.
- RSEM formula: `score = 0.7 * containment - 0.3 * business_impact`.
- Top action: `Isolate ws-fin-27` with score `0.599`.
- Artifacts: `incident.json`, `hypotheses.json`, `feasibility.json`,
  `ranked_actions.json`, `playbook.json`, `execution.json`, `monitoring.json`,
  `cycle_result.json`.

## Test Commands

Default deterministic suite, không gọi OpenAI:

```powershell
cd C:\Users\hienhq\Documents\ai-lab\AGENT-SOC
uv run --project C:\Users\hienhq\Documents\ai-lab --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe pytest -m "not llm and not stress"
```

LLM thật, chỉ chạy khi người dùng đã điền `OPENAI_API_KEY`:

```powershell
cd C:\Users\hienhq\Documents\ai-lab\AGENT-SOC
uv run --project C:\Users\hienhq\Documents\ai-lab --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe pytest -m llm
```

Stress mock-only:

```powershell
cd C:\Users\hienhq\Documents\ai-lab\AGENT-SOC
uv run --project C:\Users\hienhq\Documents\ai-lab --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe pytest -m stress
```

## Sprint Index

- `sprints/S00_paper_reverse_engineering.md`
- `sprints/S01_scaffold_contracts.md`
- `sprints/S02_knowledge_store_graph.md`
- `sprints/S03_perception_layer.md`
- `sprints/S04_nce_layer.md`
- `sprints/S05_sse_layer.md`
- `sprints/S06_rsem_layer.md`
- `sprints/S07_playbook_execution.md`
- `sprints/S08_monitoring_closed_loop.md`
- `sprints/S09_e2e_benchmark_hardening.md`
