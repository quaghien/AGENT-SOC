from __future__ import annotations

from agent_soc.config import get_settings
from agent_soc.llm import MockNCEClient, create_nce_client
from agent_soc.perception import PerceptionEngine


def test_mock_nce_returns_paper_hypotheses(paper_alert, knowledge_store):
    incident = PerceptionEngine().enrich(paper_alert, knowledge_store)
    output = MockNCEClient().generate_hypotheses(incident)
    assert [item.hypothesis_id for item in output.hypotheses] == ["H1", "H2", "H3"]
    assert output.backend == "mock"


def test_auto_without_key_uses_mock(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    settings = get_settings(llm_mode="auto")
    client = create_nce_client(settings)
    assert client.primary.backend == "mock"


def test_budget_falls_back_to_mock_after_limit(paper_alert, knowledge_store):
    incident = PerceptionEngine().enrich(paper_alert, knowledge_store)
    client = create_nce_client(get_settings(llm_mode="mock"))
    client.max_calls = 0
    output = client.generate_hypotheses(incident)
    assert output.backend == "mock"
