from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from agent_soc.schemas import EntityContext


class EnterpriseKnowledgeStore:
    """In-memory CMDB/IAM/topology/policy store for the AgentSOC POC."""

    def __init__(self, graph: nx.DiGraph | None = None) -> None:
        self.graph = graph or nx.DiGraph()
        self.incident_history: list[dict[str, Any]] = []
        self.attack_techniques = {
            "T1021": "Remote Services",
            "T1550": "Use Alternate Authentication Material",
            "T1110": "Brute Force",
            "T1558": "Steal or Forge Kerberos Tickets",
        }
        self.policies = {
            "dry_run_only": True,
            "requires_analyst_approval": ["ISOLATE_HOST", "DISABLE_ACCOUNT"],
            "blocked_live_actions": ["ISOLATE_HOST", "DISABLE_ACCOUNT", "BLOCK_IP"],
        }

    @classmethod
    def synthetic_poc(cls, node_count: int = 50) -> "EnterpriseKnowledgeStore":
        if node_count < 12:
            raise ValueError("node_count must be at least 12 for the POC graph")
        graph = nx.DiGraph()
        base_nodes: list[tuple[str, dict[str, Any]]] = [
            ("user123", {"entity_type": "user", "department": "finance", "risk": "medium"}),
            ("finance_admin", {"entity_type": "user", "department": "finance", "risk": "high"}),
            ("ws-fin-27", {"entity_type": "host", "role": "workstation", "criticality": "medium"}),
            ("srv-fin-03", {"entity_type": "host", "role": "finance-server", "criticality": "high"}),
            ("domain-controller-01", {"entity_type": "host", "role": "domain-controller", "criticality": "critical"}),
            ("finance_group", {"entity_type": "group", "department": "finance"}),
            ("kerberos", {"entity_type": "service", "protocol": "Kerberos"}),
            ("subnet-fin", {"entity_type": "network", "zone": "finance"}),
            ("edr-policy-default", {"entity_type": "policy", "mode": "dry-run"}),
            ("siem-rule-kerberos-tgt", {"entity_type": "rule", "category": "identity"}),
            ("ticket-cache-ws-fin-27", {"entity_type": "artifact", "host": "ws-fin-27"}),
            ("baseline-auth-finance", {"entity_type": "baseline", "coverage": "partial"}),
        ]
        for node_id, attrs in base_nodes:
            graph.add_node(node_id, **attrs)
        edges = [
            ("user123", "ws-fin-27", "USES"),
            ("finance_admin", "srv-fin-03", "ADMINISTERS"),
            ("user123", "finance_group", "MEMBER_OF"),
            ("finance_group", "srv-fin-03", "CAN_ACCESS"),
            ("ws-fin-27", "srv-fin-03", "CAN_CONNECT"),
            ("ws-fin-27", "domain-controller-01", "AUTHENTICATES_TO"),
            ("srv-fin-03", "domain-controller-01", "TRUSTS"),
            ("kerberos", "domain-controller-01", "RUNS_ON"),
            ("ws-fin-27", "subnet-fin", "IN_SUBNET"),
            ("srv-fin-03", "subnet-fin", "IN_SUBNET"),
            ("siem-rule-kerberos-tgt", "kerberos", "DETECTS"),
            ("edr-policy-default", "ws-fin-27", "COVERS"),
            ("ticket-cache-ws-fin-27", "ws-fin-27", "OBSERVED_ON"),
            ("baseline-auth-finance", "user123", "BASELINES"),
        ]
        for source, target, relation in edges:
            graph.add_edge(source, target, relation=relation)
        filler_idx = 0
        while graph.number_of_nodes() < node_count:
            filler_idx += 1
            host = f"ws-lab-{filler_idx:02d}"
            graph.add_node(host, entity_type="host", role="workstation", criticality="low")
            graph.add_edge(host, "domain-controller-01", relation="AUTHENTICATES_TO")
        return cls(graph)

    @classmethod
    def load_json(cls, path: Path) -> "EnterpriseKnowledgeStore":
        data = json.loads(path.read_text(encoding="utf-8"))
        graph = nx.node_link_graph(data, directed=True, edges="links")
        return cls(graph)

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = nx.node_link_data(self.graph, edges="links")
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def entity_exists(self, entity_id: str) -> bool:
        return self.graph.has_node(entity_id)

    def entity_context(self, entity_id: str) -> EntityContext:
        if not self.entity_exists(entity_id):
            return EntityContext(entity_id=entity_id, entity_type="unknown")
        attrs = dict(self.graph.nodes[entity_id])
        entity_type = attrs.pop("entity_type", "unknown")
        relationships: list[str] = []
        for _, target, edge in self.graph.out_edges(entity_id, data=True):
            relationships.append(f"{edge.get('relation', 'RELATED_TO')}:{target}")
        for source, _, edge in self.graph.in_edges(entity_id, data=True):
            relationships.append(f"{source}:{edge.get('relation', 'RELATED_TO')}")
        return EntityContext(
            entity_id=entity_id,
            entity_type=entity_type,
            attributes=attrs,
            relationships=sorted(relationships),
        )

    def shortest_path(self, source: str, target: str) -> list[str] | None:
        if not self.entity_exists(source) or not self.entity_exists(target):
            return None
        try:
            return nx.shortest_path(self.graph, source=source, target=target)
        except nx.NetworkXNoPath:
            return None

    def lateral_movement_path(self, user: str, source_host: str, target_host: str | None) -> list[str] | None:
        if not target_host:
            return None
        direct = self.shortest_path(source_host, target_host)
        if direct:
            return [user, *direct] if user != direct[0] else direct
        user_path = self.shortest_path(user, target_host)
        return user_path

    def policy_allows_live_action(self, action_id: str) -> bool:
        return action_id not in self.policies["blocked_live_actions"]

    def record_knowledge_update(self, incident_id: str, update: str) -> None:
        self.incident_history.append({"incident_id": incident_id, "update": update})
