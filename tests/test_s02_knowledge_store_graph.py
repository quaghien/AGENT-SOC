from __future__ import annotations

from agent_soc.knowledge import EnterpriseKnowledgeStore


def test_synthetic_graph_has_50_nodes():
    store = EnterpriseKnowledgeStore.synthetic_poc(node_count=50)
    assert store.graph.number_of_nodes() == 50
    assert store.entity_exists("user123")
    assert store.entity_exists("ws-fin-27")
    assert store.entity_exists("srv-fin-03")


def test_entity_context_contains_relationships(knowledge_store):
    context = knowledge_store.entity_context("ws-fin-27")
    assert context.entity_type == "host"
    assert any("CAN_CONNECT:srv-fin-03" == relation for relation in context.relationships)


def test_lateral_movement_path_for_paper_entities(knowledge_store):
    path = knowledge_store.lateral_movement_path("user123", "ws-fin-27", "srv-fin-03")
    assert path == ["user123", "ws-fin-27", "srv-fin-03"]


def test_graph_save_load_roundtrip(tmp_path):
    path = tmp_path / "graph.json"
    store = EnterpriseKnowledgeStore.synthetic_poc(node_count=50)
    store.save_json(path)
    loaded = EnterpriseKnowledgeStore.load_json(path)
    assert loaded.graph.number_of_nodes() == 50
    assert loaded.lateral_movement_path("user123", "ws-fin-27", "srv-fin-03")
