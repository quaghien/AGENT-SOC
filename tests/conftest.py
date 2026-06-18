from __future__ import annotations

from pathlib import Path

import pytest

from agent_soc.config import PROJECT_DIR
from agent_soc.knowledge import EnterpriseKnowledgeStore
from agent_soc.pipeline import load_alert


@pytest.fixture
def project_dir() -> Path:
    return PROJECT_DIR


@pytest.fixture
def paper_alert():
    return load_alert(PROJECT_DIR / "fixtures" / "paper_alert.json")


@pytest.fixture
def knowledge_store():
    return EnterpriseKnowledgeStore.synthetic_poc()
