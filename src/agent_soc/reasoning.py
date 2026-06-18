from __future__ import annotations

from agent_soc.knowledge import EnterpriseKnowledgeStore
from agent_soc.schemas import AttackHypothesis, DefensiveAction, FeasibilityResult, Incident, RankedAction


class SemanticSimulationEngine:
    def evaluate(
        self,
        incident: Incident,
        hypotheses: list[AttackHypothesis],
        store: EnterpriseKnowledgeStore,
    ) -> list[FeasibilityResult]:
        results: list[FeasibilityResult] = []
        alert = incident.source_alert
        for hypothesis in hypotheses:
            missing_entities = [entity for entity in hypothesis.required_entities if entity and not store.entity_exists(entity)]
            path = store.lateral_movement_path(alert.source_user, alert.source_host, alert.target_host)
            if hypothesis.hypothesis_id == "H1" and path:
                results.append(
                    FeasibilityResult(
                        hypothesis_id="H1",
                        status="accepted",
                        feasible=True,
                        evidence=["Graph confirms a reachable path from source workstation to target server"],
                        graph_paths=[path],
                    )
                )
            elif hypothesis.hypothesis_id == "H2" and "baseline-auth-finance" in store.graph:
                results.append(
                    FeasibilityResult(
                        hypothesis_id="H2",
                        status="conditional",
                        feasible=True,
                        evidence=["User and partial authentication baseline are present"],
                        conditions=["Requires recent baseline comparison before live containment"],
                        graph_paths=[[alert.source_user, "baseline-auth-finance"]],
                    )
                )
            elif missing_entities:
                results.append(
                    FeasibilityResult(
                        hypothesis_id=hypothesis.hypothesis_id,
                        status="rejected",
                        feasible=False,
                        rejected_reason=f"Missing required entities: {', '.join(missing_entities)}",
                        evidence=["Knowledge graph does not support this scenario"],
                    )
                )
            else:
                results.append(
                    FeasibilityResult(
                        hypothesis_id=hypothesis.hypothesis_id,
                        status="conditional",
                        feasible=True,
                        conditions=["Feasible but requires analyst validation"],
                        evidence=["No contradiction found in graph"],
                    )
                )
        return results


def default_action_catalog(incident: Incident) -> list[DefensiveAction]:
    alert = incident.source_alert
    host = alert.source_host
    user = alert.source_user
    target = alert.target_host or "unknown-target"
    return [
        DefensiveAction(
            action_id="ISOLATE_HOST",
            name=f"Isolate {host}",
            target_entity=host,
            action_type="containment",
            containment=0.97,
            business_impact=0.267,
            requires_approval=True,
            prerequisites=["Confirm host is not a domain controller", "Notify analyst for dry-run approval"],
            rollback_steps=["Remove host from isolation policy", "Validate EDR heartbeat"],
        ),
        DefensiveAction(
            action_id="RESET_USER_PASSWORD",
            name=f"Reset password for {user}",
            target_entity=user,
            action_type="identity",
            containment=0.72,
            business_impact=0.10,
            requires_approval=False,
            prerequisites=["Confirm user identity owner"],
            rollback_steps=["Force password reset flow for user", "Close temporary helpdesk ticket"],
        ),
        DefensiveAction(
            action_id="DISABLE_ACCOUNT",
            name=f"Disable {user}",
            target_entity=user,
            action_type="identity",
            containment=0.85,
            business_impact=0.55,
            requires_approval=True,
            prerequisites=["Analyst approval required due to business impact"],
            rollback_steps=["Re-enable account", "Rotate credentials"],
        ),
        DefensiveAction(
            action_id="RESTRICT_SERVER_ACCESS",
            name=f"Restrict access to {target}",
            target_entity=target,
            action_type="network",
            containment=0.65,
            business_impact=0.35,
            requires_approval=True,
            prerequisites=["Confirm no critical finance batch window"],
            rollback_steps=["Restore previous access control list"],
        ),
    ]


class RSEMEngine:
    def __init__(self, containment_weight: float = 0.7, business_impact_weight: float = 0.3) -> None:
        self.containment_weight = containment_weight
        self.business_impact_weight = business_impact_weight

    def score_action(self, action: DefensiveAction) -> float:
        score = self.containment_weight * action.containment - self.business_impact_weight * action.business_impact
        return round(score, 3)

    def rank(
        self,
        incident: Incident,
        feasibility: list[FeasibilityResult],
        actions: list[DefensiveAction] | None = None,
    ) -> list[RankedAction]:
        viable_hypotheses = [item.hypothesis_id for item in feasibility if item.status in {"accepted", "conditional"}]
        catalog = actions or default_action_catalog(incident)
        ranked = [
            RankedAction(
                action=action,
                score=self.score_action(action),
                rank=0,
                hypothesis_ids=viable_hypotheses,
                rationale=(
                    f"score = 0.7 * containment({action.containment}) "
                    f"- 0.3 * business_impact({action.business_impact})"
                ),
            )
            for action in catalog
        ]
        ranked.sort(key=lambda item: item.score, reverse=True)
        for idx, item in enumerate(ranked, start=1):
            item.rank = idx
        return ranked
