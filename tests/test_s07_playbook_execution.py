from __future__ import annotations

from agent_soc.actions import DryRunExecutor, PlaybookBuilder
from agent_soc.llm import MockNCEClient
from agent_soc.perception import PerceptionEngine
from agent_soc.reasoning import RSEMEngine, SemanticSimulationEngine


def test_playbook_and_executor_are_dry_run_only(paper_alert, knowledge_store):
    incident = PerceptionEngine().enrich(paper_alert, knowledge_store)
    hypotheses = MockNCEClient().generate_hypotheses(incident).hypotheses
    feasibility = SemanticSimulationEngine().evaluate(incident, hypotheses, knowledge_store)
    ranked = RSEMEngine().rank(incident, feasibility)
    playbook = PlaybookBuilder().build(incident, ranked)
    execution = DryRunExecutor().execute(playbook)
    assert playbook.mode == "dry-run"
    assert execution.status == "simulated"
    assert execution.dry_run is True
    assert execution.executed_steps[0]["command"] == "DRY_RUN:ISOLATE_HOST(ws-fin-27)"
