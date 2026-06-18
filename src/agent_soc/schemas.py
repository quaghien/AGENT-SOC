from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


LLMMode = Literal["auto", "mock", "openai"]
ActionMode = Literal["dry-run"]
FeasibilityStatus = Literal["accepted", "conditional", "rejected"]


class RawAlert(BaseModel):
    event_id: str = "evt-poc-001"
    timestamp: datetime
    source_user: str
    source_host: str
    target_host: str | None = None
    event_type: str
    outcome: str
    source_ip: str | None = None
    target_ip: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_user", "source_host", "event_type", "outcome")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("required alert string fields cannot be empty")
        return value


class EntityContext(BaseModel):
    entity_id: str
    entity_type: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    relationships: list[str] = Field(default_factory=list)


class Incident(BaseModel):
    incident_id: str
    source_alert: RawAlert
    severity: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str
    signals: list[str] = Field(default_factory=list)
    contexts: dict[str, EntityContext] = Field(default_factory=dict)
    dedupe_count: int = Field(default=1, ge=1)
    enriched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AttackHypothesis(BaseModel):
    hypothesis_id: str
    title: str
    description: str
    tactic: str
    technique_id: str
    technique_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    required_entities: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    llm_backend: str = "mock"
    model: str = "mock"


class NCEOutput(BaseModel):
    hypotheses: list[AttackHypothesis]
    backend: str
    model: str


class FeasibilityResult(BaseModel):
    hypothesis_id: str
    status: FeasibilityStatus
    feasible: bool
    evidence: list[str] = Field(default_factory=list)
    graph_paths: list[list[str]] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    rejected_reason: str | None = None


class DefensiveAction(BaseModel):
    action_id: str
    name: str
    target_entity: str
    action_type: str
    containment: float = Field(ge=0.0, le=1.0)
    business_impact: float = Field(ge=0.0, le=1.0)
    requires_approval: bool = True
    dry_run_only: bool = True
    prerequisites: list[str] = Field(default_factory=list)
    rollback_steps: list[str] = Field(default_factory=list)


class RankedAction(BaseModel):
    action: DefensiveAction
    score: float
    rank: int
    hypothesis_ids: list[str] = Field(default_factory=list)
    rationale: str


class PlaybookStep(BaseModel):
    step_id: str
    action: RankedAction
    instruction: str
    approval_required: bool


class Playbook(BaseModel):
    playbook_id: str
    incident_id: str
    mode: ActionMode = "dry-run"
    steps: list[PlaybookStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionRecord(BaseModel):
    execution_id: str
    playbook_id: str
    mode: ActionMode = "dry-run"
    status: Literal["simulated", "blocked", "failed"]
    dry_run: bool = True
    executed_steps: list[dict[str, Any]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MonitoringResult(BaseModel):
    monitoring_id: str
    incident_id: str
    status: Literal["stable", "needs_review", "failed"]
    deviations: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    knowledge_updates: list[str] = Field(default_factory=list)


class CycleResult(BaseModel):
    incident: Incident
    hypotheses: list[AttackHypothesis]
    feasibility: list[FeasibilityResult]
    ranked_actions: list[RankedAction]
    playbook: Playbook
    execution: ExecutionRecord
    monitoring: MonitoringResult
    timings_ms: dict[str, float] = Field(default_factory=dict)
    llm_usage: dict[str, Any] = Field(default_factory=dict)
    artifacts_dir: str | None = None


class BenchmarkSummary(BaseModel):
    events_seen: int
    events_processed: int
    llm_backend: str
    llm_calls: int
    concurrency: int
    stress_guard: str
    duration_ms: float
    sample_incident_id: str | None = None
