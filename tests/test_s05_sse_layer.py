from __future__ import annotations

from agent_soc.llm import MockNCEClient
from agent_soc.perception import PerceptionEngine
from agent_soc.reasoning import SemanticSimulationEngine


def test_sse_accepts_conditional_and_rejects_paper_hypotheses(paper_alert, knowledge_store):
    incident = PerceptionEngine().enrich(paper_alert, knowledge_store)
    hypotheses = MockNCEClient().generate_hypotheses(incident).hypotheses
    results = SemanticSimulationEngine().evaluate(incident, hypotheses, knowledge_store)
    by_id = {result.hypothesis_id: result for result in results}
    assert by_id["H1"].status == "accepted"
    assert by_id["H2"].status == "conditional"
    assert by_id["H3"].status == "rejected"
    assert by_id["H3"].feasible is False
