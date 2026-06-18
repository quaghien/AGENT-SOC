from __future__ import annotations

import csv
import time
from pathlib import Path

from agent_soc.actions import DryRunExecutor, PlaybookBuilder
from agent_soc.artifacts import write_cycle_artifacts, write_json
from agent_soc.config import AgentSOCSettings, get_settings
from agent_soc.knowledge import EnterpriseKnowledgeStore
from agent_soc.llm import BudgetedNCEClient, MockNCEClient, create_nce_client
from agent_soc.monitoring import Monitor
from agent_soc.perception import PerceptionEngine
from agent_soc.reasoning import RSEMEngine, SemanticSimulationEngine
from agent_soc.schemas import BenchmarkSummary, CycleResult, LLMMode, RawAlert


def load_alert(path: Path) -> RawAlert:
    return RawAlert.model_validate_json(path.read_text(encoding="utf-8"))


def load_events_csv(path: Path, *, limit: int | None = None) -> list[RawAlert]:
    alerts: list[RawAlert] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            alerts.append(
                RawAlert(
                    event_id=row.get("event_id") or f"evt-{len(alerts) + 1:05d}",
                    timestamp=row["timestamp"],
                    source_user=row["source_user"],
                    source_host=row["source_host"],
                    target_host=row.get("target_host") or None,
                    event_type=row["event_type"],
                    outcome=row["outcome"],
                    source_ip=row.get("source_ip") or None,
                    target_ip=row.get("target_ip") or None,
                    raw=row,
                )
            )
            if limit is not None and len(alerts) >= limit:
                break
    return alerts


class AgentSOCPipeline:
    def __init__(
        self,
        *,
        settings: AgentSOCSettings | None = None,
        store: EnterpriseKnowledgeStore | None = None,
        nce_client: BudgetedNCEClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.store = store or EnterpriseKnowledgeStore.synthetic_poc()
        self.nce_client = nce_client or create_nce_client(self.settings)
        self.perception = PerceptionEngine()
        self.sse = SemanticSimulationEngine()
        self.rsem = RSEMEngine()
        self.playbooks = PlaybookBuilder()
        self.executor = DryRunExecutor()
        self.monitor = Monitor()

    def run_alert(self, alert: RawAlert, *, artifacts_dir: Path | None = None) -> CycleResult:
        timings: dict[str, float] = {}

        start = time.perf_counter()
        incident = self.perception.enrich(alert, self.store)
        timings["perception"] = round((time.perf_counter() - start) * 1000, 3)

        start = time.perf_counter()
        nce_output = self.nce_client.generate_hypotheses(incident)
        hypotheses = nce_output.hypotheses
        timings["nce"] = round((time.perf_counter() - start) * 1000, 3)

        start = time.perf_counter()
        feasibility = self.sse.evaluate(incident, hypotheses, self.store)
        timings["sse"] = round((time.perf_counter() - start) * 1000, 3)

        start = time.perf_counter()
        ranked_actions = self.rsem.rank(incident, feasibility)
        timings["rsem"] = round((time.perf_counter() - start) * 1000, 3)

        start = time.perf_counter()
        playbook = self.playbooks.build(incident, ranked_actions)
        execution = self.executor.execute(playbook, mode="dry-run")
        timings["act"] = round((time.perf_counter() - start) * 1000, 3)

        start = time.perf_counter()
        monitoring = self.monitor.observe(incident, execution, self.store)
        timings["monitoring"] = round((time.perf_counter() - start) * 1000, 3)
        timings["total"] = round(sum(timings.values()), 3)

        result = CycleResult(
            incident=incident,
            hypotheses=hypotheses,
            feasibility=feasibility,
            ranked_actions=ranked_actions,
            playbook=playbook,
            execution=execution,
            monitoring=monitoring,
            timings_ms=timings,
            llm_usage=self.nce_client.usage(),
            artifacts_dir=str(artifacts_dir) if artifacts_dir else None,
        )
        if artifacts_dir:
            write_cycle_artifacts(result, artifacts_dir)
        return result


def benchmark(
    events_path: Path,
    *,
    limit: int,
    concurrency: int,
    artifacts_dir: Path,
    settings: AgentSOCSettings | None = None,
    requested_llm_mode: LLMMode = "mock",
) -> BenchmarkSummary:
    settings = settings or get_settings(llm_mode=requested_llm_mode)
    if requested_llm_mode == "openai" and not settings.allow_stress_llm:
        raise RuntimeError("OpenAI is disabled for benchmark/stress unless AGENTSOC_ALLOW_STRESS_LLM=true")
    if requested_llm_mode == "openai" and limit > settings.max_llm_calls:
        raise RuntimeError("Benchmark would exceed AGENTSOC_MAX_LLM_CALLS; use mock")
    alerts = load_events_csv(events_path, limit=limit)
    nce = create_nce_client(settings) if requested_llm_mode == "openai" else BudgetedNCEClient(MockNCEClient(), max_calls=0)
    pipeline = AgentSOCPipeline(settings=settings, nce_client=nce)
    start = time.perf_counter()
    sample = None
    for alert in alerts:
        result = pipeline.run_alert(alert)
        sample = sample or result
    duration = round((time.perf_counter() - start) * 1000, 3)
    summary = BenchmarkSummary(
        events_seen=len(alerts),
        events_processed=len(alerts),
        llm_backend=nce.primary.backend,
        llm_calls=nce.calls,
        concurrency=concurrency,
        stress_guard="openai-blocked-by-default",
        duration_ms=duration,
        sample_incident_id=sample.incident.incident_id if sample else None,
    )
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    write_json(artifacts_dir / "benchmark_summary.json", summary)
    if sample:
        write_cycle_artifacts(sample, artifacts_dir / "sample_cycle")
    return summary
