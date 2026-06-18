from __future__ import annotations

from agent_soc.knowledge import EnterpriseKnowledgeStore
from agent_soc.schemas import ExecutionRecord, Incident, MonitoringResult


class Monitor:
    def observe(
        self,
        incident: Incident,
        execution: ExecutionRecord,
        store: EnterpriseKnowledgeStore,
    ) -> MonitoringResult:
        deviations: list[str] = []
        if not execution.dry_run:
            deviations.append("non_dry_run_execution_detected")
        if execution.status != "simulated":
            deviations.append(f"execution_status_{execution.status}")
        update = f"Recorded {execution.status} dry-run playbook for {incident.incident_id}"
        store.record_knowledge_update(incident.incident_id, update)
        return MonitoringResult(
            monitoring_id=f"MON-{incident.incident_id}",
            incident_id=incident.incident_id,
            status="needs_review" if deviations else "stable",
            deviations=deviations,
            metrics={
                "steps_observed": len(execution.executed_steps),
                "dry_run": execution.dry_run,
            },
            knowledge_updates=[update],
        )
