from __future__ import annotations

import json

from agent_soc.config import get_settings
from agent_soc.llm import BudgetedNCEClient, MockNCEClient
from agent_soc.pipeline import AgentSOCPipeline


def test_e2e_paper_poc_writes_expected_artifacts(paper_alert, knowledge_store, tmp_path):
    settings = get_settings(llm_mode="mock", artifacts_dir=tmp_path)
    pipeline = AgentSOCPipeline(
        settings=settings,
        store=knowledge_store,
        nce_client=BudgetedNCEClient(MockNCEClient(), max_calls=0),
    )
    result = pipeline.run_alert(paper_alert, artifacts_dir=tmp_path)
    assert result.incident.incident_id == "INC-POC-001"
    assert result.ranked_actions[0].action.action_id == "ISOLATE_HOST"
    for name in [
        "incident.json",
        "hypotheses.json",
        "feasibility.json",
        "ranked_actions.json",
        "playbook.json",
        "execution.json",
        "monitoring.json",
        "cycle_result.json",
    ]:
        assert (tmp_path / name).exists(), name
    payload = json.loads((tmp_path / "cycle_result.json").read_text(encoding="utf-8"))
    assert payload["llm_usage"]["backend"] == "mock"
