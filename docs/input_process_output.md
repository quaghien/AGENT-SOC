# AgentSOC POC - Input, Xử Lý, Output

SVG kiến trúc: [`architecture_flow.svg`](architecture_flow.svg)

## 1. Input

| Nhóm | Nội dung |
|---|---|
| Alert | `RawAlert` JSON, ví dụ `fixtures/paper_alert.json`: `user123`, `ws-fin-27`, `srv-fin-03`, `Kerberos TGT Request`, `Success`, `2023-11-14T13:22:41Z`. |
| Knowledge | Synthetic enterprise graph 50 node: user, host, server, domain controller, finance group, Kerberos service, policy, baseline. |
| Env | `.env.example`: `OPENAI_API_KEY` nếu chạy LLM thật, model mặc định `gpt-5.4-nano`, budget `AGENTSOC_MAX_LLM_CALLS=30`. |
| Mode | `--llm mock`, `--llm auto`, hoặc `--llm openai`; action mode luôn `dry-run`. |

## 2. Xử Lý

| Bước | Làm gì |
|---|---|
| Perception | Chuẩn hóa alert, enrich bằng knowledge graph, dedupe, tạo `Incident`. Với POC tạo `INC-POC-001`. |
| NCE | Sinh giả thuyết tấn công `H1/H2/H3`. Mock dùng output deterministic; OpenAI dùng structured output cho run nhỏ. |
| SSE | Mô phỏng ngữ nghĩa trên graph: kiểm tra entity, path, policy, precondition. Kết quả POC: `H1` accepted, `H2` conditional, `H3` rejected. |
| RSEM | Chọn và xếp hạng action phòng thủ bằng công thức `0.7 * containment - 0.3 * business_impact`. |
| Playbook | Chuyển ranked actions thành các bước dry-run, kèm approval flag và rollback notes. |
| Execution | Chỉ mô phỏng action: không isolate host thật, không disable user thật, không gọi SIEM/EDR/IAM/SOAR thật. |
| Monitoring | Ghi kết quả thực thi, deviation nếu có, và update knowledge store trong memory. |

## 3. Output

| Output | Ý nghĩa |
|---|---|
| `incident.json` | Alert đã enrich thành incident. |
| `hypotheses.json` | Danh sách giả thuyết NCE. |
| `feasibility.json` | Kết quả SSE cho từng giả thuyết. |
| `ranked_actions.json` | Action đã chấm điểm và xếp hạng. Top POC: `ISOLATE_HOST / Isolate ws-fin-27`, score `0.599`. |
| `playbook.json` | Các bước phản ứng dry-run. |
| `execution.json` | Log mô phỏng thực thi. |
| `monitoring.json` | Kết quả quan sát sau execution. |
| `cycle_result.json` | Artifact tổng hợp toàn bộ vòng chạy. |

## 4. Lệnh Chạy Nhanh

Mock, không tốn API:

```powershell
cd C:\Users\hienhq\Documents\ai-lab\AGENT-SOC
uv run --project C:\Users\hienhq\Documents\ai-lab --package agent-soc --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe python -m agent_soc.cli run --input fixtures\paper_alert.json --llm mock --artifacts output\paper_mock
```

OpenAI thật cho một run nhỏ:

```powershell
cd C:\Users\hienhq\Documents\ai-lab\AGENT-SOC
uv run --project C:\Users\hienhq\Documents\ai-lab --package agent-soc --python C:\Users\hienhq\Documents\ai-lab\.venv\Scripts\python.exe python -m agent_soc.cli run --input fixtures\paper_alert.json --llm openai --artifacts output\paper_openai
```
