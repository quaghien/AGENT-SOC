from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from agent_soc.schemas import LLMMode

PROJECT_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = PROJECT_DIR.parent


def _bool_env(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    parsed = int(value)
    if parsed < 0:
        raise ValueError("integer env values must be non-negative")
    return parsed


@dataclass(frozen=True)
class AgentSOCSettings:
    openai_api_key: str | None
    llm_model: str = "gpt-5.4-nano"
    llm_mode: LLMMode = "auto"
    max_llm_calls: int = 30
    allow_stress_llm: bool = False
    artifacts_dir: Path = PROJECT_DIR / "output"

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)


def load_env() -> None:
    load_dotenv(PROJECT_DIR / ".env", override=False)
    load_dotenv(WORKSPACE_DIR / ".env", override=False)


def get_settings(
    *,
    llm_mode: LLMMode | None = None,
    artifacts_dir: Path | None = None,
) -> AgentSOCSettings:
    load_env()
    mode = llm_mode or os.getenv("AGENTSOC_LLM_MODE", "auto").strip().lower()
    if mode not in {"auto", "mock", "openai"}:
        raise ValueError("AGENTSOC_LLM_MODE must be auto, mock, or openai")
    configured_artifacts = os.getenv("AGENTSOC_ARTIFACTS_DIR", "output")
    artifact_root = artifacts_dir or Path(configured_artifacts)
    if not artifact_root.is_absolute():
        artifact_root = PROJECT_DIR / artifact_root
    return AgentSOCSettings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        llm_model=os.getenv("AGENTSOC_LLM_MODEL", "gpt-5.4-nano"),
        llm_mode=mode,  # type: ignore[arg-type]
        max_llm_calls=_int_env(os.getenv("AGENTSOC_MAX_LLM_CALLS"), 30),
        allow_stress_llm=_bool_env(os.getenv("AGENTSOC_ALLOW_STRESS_LLM"), False),
        artifacts_dir=artifact_root,
    )
