from __future__ import annotations

import os

import pytest

from agent_soc.config import get_settings
from agent_soc.llm import create_nce_client
from agent_soc.perception import PerceptionEngine


@pytest.mark.llm
def test_openai_nce_structured_output_under_budget(paper_alert, knowledge_store):
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not configured")
    settings = get_settings(llm_mode="openai")
    assert settings.llm_model == "gpt-5.4-nano"
    client = create_nce_client(settings)
    incident = PerceptionEngine().enrich(paper_alert, knowledge_store)
    output = client.generate_hypotheses(incident)
    assert len(output.hypotheses) == 3
    assert client.calls <= settings.max_llm_calls
