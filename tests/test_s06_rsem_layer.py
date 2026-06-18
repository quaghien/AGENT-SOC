from __future__ import annotations

from agent_soc.llm import MockNCEClient
from agent_soc.perception import PerceptionEngine
from agent_soc.reasoning import RSEMEngine, SemanticSimulationEngine


def test_rsem_reproduces_top_paper_action_score(paper_alert, knowledge_store):
    incident = PerceptionEngine().enrich(paper_alert, knowledge_store)
    hypotheses = MockNCEClient().generate_hypotheses(incident).hypotheses
    feasibility = SemanticSimulationEngine().evaluate(incident, hypotheses, knowledge_store)
    ranked = RSEMEngine().rank(incident, feasibility)
    assert ranked[0].action.name == "Isolate ws-fin-27"
    assert ranked[0].action.action_id == "ISOLATE_HOST"
    assert ranked[0].score == 0.599
    assert [item.rank for item in ranked] == [1, 2, 3, 4]
