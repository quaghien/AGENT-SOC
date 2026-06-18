from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agent_soc.schemas import CycleResult


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_jsonable(value), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_cycle_artifacts(result: CycleResult, artifacts_dir: Path) -> None:
    write_json(artifacts_dir / "incident.json", result.incident)
    write_json(artifacts_dir / "hypotheses.json", result.hypotheses)
    write_json(artifacts_dir / "feasibility.json", result.feasibility)
    write_json(artifacts_dir / "ranked_actions.json", result.ranked_actions)
    write_json(artifacts_dir / "playbook.json", result.playbook)
    write_json(artifacts_dir / "execution.json", result.execution)
    write_json(artifacts_dir / "monitoring.json", result.monitoring)
    write_json(artifacts_dir / "cycle_result.json", result)
