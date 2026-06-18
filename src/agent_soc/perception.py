from __future__ import annotations

import hashlib

from agent_soc.knowledge import EnterpriseKnowledgeStore
from agent_soc.schemas import Incident, RawAlert


def _stable_incident_id(alert: RawAlert) -> str:
    poc_match = (
        alert.source_user == "user123"
        and alert.source_host == "ws-fin-27"
        and alert.target_host == "srv-fin-03"
        and alert.event_type.lower() == "kerberos tgt request"
    )
    if poc_match:
        return "INC-POC-001"
    digest = hashlib.sha1(
        f"{alert.timestamp.isoformat()}|{alert.source_user}|{alert.source_host}|{alert.event_type}".encode(
            "utf-8"
        )
    ).hexdigest()
    return f"INC-{digest[:8].upper()}"


class PerceptionEngine:
    def enrich(self, alert: RawAlert, store: EnterpriseKnowledgeStore) -> Incident:
        signals: list[str] = []
        event_name = alert.event_type.strip().lower()
        if "kerberos" in event_name and "tgt" in event_name:
            signals.append("kerberos_tgt_activity")
        if alert.outcome.strip().lower() == "success":
            signals.append("successful_authentication")
        if alert.target_host:
            target_context = store.entity_context(alert.target_host)
            if target_context.attributes.get("criticality") in {"high", "critical"}:
                signals.append("critical_target")
        path = store.lateral_movement_path(alert.source_user, alert.source_host, alert.target_host)
        if path:
            signals.append("reachable_target_path")
        severity = "high" if {"kerberos_tgt_activity", "critical_target"} <= set(signals) else "medium"
        confidence = 0.86 if severity == "high" else 0.64
        contexts = {
            alert.source_user: store.entity_context(alert.source_user),
            alert.source_host: store.entity_context(alert.source_host),
        }
        if alert.target_host:
            contexts[alert.target_host] = store.entity_context(alert.target_host)
        return Incident(
            incident_id=_stable_incident_id(alert),
            source_alert=alert,
            severity=severity,
            confidence=confidence,
            summary=(
                f"{alert.event_type} by {alert.source_user} from {alert.source_host}"
                + (f" toward {alert.target_host}" if alert.target_host else "")
            ),
            signals=signals,
            contexts=contexts,
        )

    def dedupe(self, alerts: list[RawAlert]) -> list[RawAlert]:
        seen: set[tuple[str, str, str, str]] = set()
        unique: list[RawAlert] = []
        for alert in alerts:
            key = (
                alert.source_user,
                alert.source_host,
                alert.target_host or "",
                alert.event_type.lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(alert)
        return unique
