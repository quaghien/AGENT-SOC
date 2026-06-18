from __future__ import annotations

from datetime import datetime, timezone

from agent_soc.schemas import ActionMode, ExecutionRecord, Incident, Playbook, PlaybookStep, RankedAction


class PlaybookBuilder:
    def build(self, incident: Incident, ranked_actions: list[RankedAction], *, max_steps: int = 3) -> Playbook:
        steps: list[PlaybookStep] = []
        for idx, ranked in enumerate(ranked_actions[:max_steps], start=1):
            steps.append(
                PlaybookStep(
                    step_id=f"PB-{idx:02d}",
                    action=ranked,
                    instruction=f"DRY-RUN simulate {ranked.action.action_id} on {ranked.action.target_entity}",
                    approval_required=ranked.action.requires_approval,
                )
            )
        return Playbook(
            playbook_id=f"PB-{incident.incident_id}",
            incident_id=incident.incident_id,
            mode="dry-run",
            steps=steps,
        )


class DryRunExecutor:
    def execute(self, playbook: Playbook, *, mode: ActionMode = "dry-run") -> ExecutionRecord:
        if mode != "dry-run" or playbook.mode != "dry-run":
            return ExecutionRecord(
                execution_id=f"EX-{playbook.playbook_id}",
                playbook_id=playbook.playbook_id,
                status="blocked",
                dry_run=True,
                executed_steps=[
                    {
                        "status": "blocked",
                        "reason": "AgentSOC POC only supports dry-run execution",
                    }
                ],
            )
        started = datetime.now(timezone.utc)
        executed = []
        for step in playbook.steps:
            executed.append(
                {
                    "step_id": step.step_id,
                    "action_id": step.action.action.action_id,
                    "target": step.action.action.target_entity,
                    "status": "simulated",
                    "approval_required": step.approval_required,
                    "command": f"DRY_RUN:{step.action.action.action_id}({step.action.action.target_entity})",
                    "rollback": step.action.action.rollback_steps,
                }
            )
        return ExecutionRecord(
            execution_id=f"EX-{playbook.playbook_id}",
            playbook_id=playbook.playbook_id,
            status="simulated",
            dry_run=True,
            executed_steps=executed,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
        )
