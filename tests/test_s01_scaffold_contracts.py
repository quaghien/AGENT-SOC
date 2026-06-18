from __future__ import annotations

import importlib

from agent_soc.config import PROJECT_DIR, get_settings
from agent_soc.schemas import RawAlert


def test_core_modules_import():
    for module in [
        "agent_soc.schemas",
        "agent_soc.config",
        "agent_soc.knowledge",
        "agent_soc.perception",
        "agent_soc.llm.client",
        "agent_soc.reasoning",
        "agent_soc.actions",
        "agent_soc.monitoring",
        "agent_soc.artifacts",
        "agent_soc.pipeline",
        "agent_soc.cli",
    ]:
        importlib.import_module(module)


def test_env_example_contains_required_keys():
    text = (PROJECT_DIR / ".env.example").read_text(encoding="utf-8")
    for key in [
        "OPENAI_API_KEY=",
        "AGENTSOC_LLM_MODEL=gpt-5.4-nano",
        "AGENTSOC_LLM_MODE=auto",
        "AGENTSOC_MAX_LLM_CALLS=30",
        "AGENTSOC_ALLOW_STRESS_LLM=false",
        "AGENTSOC_ARTIFACTS_DIR=output",
    ]:
        assert key in text


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.delenv("AGENTSOC_LLM_MODEL", raising=False)
    settings = get_settings(llm_mode="mock")
    assert settings.llm_model == "gpt-5.4-nano"
    assert settings.max_llm_calls == 30
    assert settings.allow_stress_llm is False


def test_raw_alert_contract_parses_timestamp():
    alert = RawAlert(
        timestamp="2023-11-14T13:22:41Z",
        source_user="user123",
        source_host="ws-fin-27",
        target_host="srv-fin-03",
        event_type="Kerberos TGT Request",
        outcome="Success",
    )
    assert alert.timestamp.year == 2023
