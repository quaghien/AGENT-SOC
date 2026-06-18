from __future__ import annotations

from agent_soc.perception import PerceptionEngine


def test_paper_alert_enriches_to_expected_incident(paper_alert, knowledge_store):
    incident = PerceptionEngine().enrich(paper_alert, knowledge_store)
    assert incident.incident_id == "INC-POC-001"
    assert incident.severity == "high"
    assert "kerberos_tgt_activity" in incident.signals
    assert "critical_target" in incident.signals
    assert "reachable_target_path" in incident.signals
    assert set(incident.contexts) >= {"user123", "ws-fin-27", "srv-fin-03"}


def test_dedupe_removes_duplicate_alerts(paper_alert):
    alerts = [paper_alert, paper_alert.model_copy(update={"event_id": "evt-duplicate"})]
    unique = PerceptionEngine().dedupe(alerts)
    assert len(unique) == 1
