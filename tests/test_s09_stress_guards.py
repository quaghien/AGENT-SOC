from __future__ import annotations

import csv

import pytest

from agent_soc.config import get_settings
from agent_soc.pipeline import benchmark


@pytest.mark.stress
def test_benchmark_uses_mock_for_high_volume(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-should-not-be-used")
    events_path = tmp_path / "events.csv"
    with events_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["event_id", "timestamp", "source_user", "source_host", "target_host", "event_type", "outcome"]
        )
        for idx in range(5000):
            writer.writerow(
                [
                    f"evt-{idx:05d}",
                    "2023-11-14T13:22:41Z",
                    "user123",
                    "ws-fin-27",
                    "srv-fin-03",
                    "Kerberos TGT Request",
                    "Success",
                ]
            )
    summary = benchmark(
        events_path,
        limit=5000,
        concurrency=8,
        artifacts_dir=tmp_path / "artifacts",
        settings=get_settings(llm_mode="mock"),
        requested_llm_mode="mock",
    )
    assert summary.events_processed == 5000
    assert summary.llm_backend == "mock"
    assert summary.llm_calls == 0


def test_openai_benchmark_is_blocked_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-should-not-be-used")
    events_path = tmp_path / "events.csv"
    events_path.write_text(
        "event_id,timestamp,source_user,source_host,target_host,event_type,outcome\n"
        "evt-1,2023-11-14T13:22:41Z,user123,ws-fin-27,srv-fin-03,Kerberos TGT Request,Success\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="OpenAI is disabled for benchmark"):
        benchmark(
            events_path,
            limit=1,
            concurrency=1,
            artifacts_dir=tmp_path / "artifacts",
            settings=get_settings(llm_mode="openai"),
            requested_llm_mode="openai",
        )
