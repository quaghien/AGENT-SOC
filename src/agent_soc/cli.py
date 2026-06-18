from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agent_soc.config import get_settings
from agent_soc.knowledge import EnterpriseKnowledgeStore
from agent_soc.pipeline import AgentSOCPipeline, benchmark, load_alert
from agent_soc.schemas import LLMMode

app = typer.Typer(help="AgentSOC POC CLI. All SOC actions are dry-run simulations.")
console = Console()


@app.command()
def run(
    input: Path = typer.Option(..., "--input", "-i", exists=True, readable=True),
    graph: Optional[Path] = typer.Option(None, "--graph", exists=True, readable=True),
    mode: str = typer.Option("dry-run", "--mode"),
    llm: LLMMode = typer.Option("auto", "--llm"),
    artifacts: Optional[Path] = typer.Option(None, "--artifacts"),
) -> None:
    if mode != "dry-run":
        raise typer.BadParameter("AgentSOC POC only supports --mode dry-run")
    settings = get_settings(llm_mode=llm, artifacts_dir=artifacts)
    if llm == "openai" and not settings.has_openai_key:
        console.print("[red]OPENAI_API_KEY is required for --llm openai.[/red]")
        raise typer.Exit(2)
    store = EnterpriseKnowledgeStore.load_json(graph) if graph else EnterpriseKnowledgeStore.synthetic_poc()
    output_dir = artifacts or settings.artifacts_dir / "run"
    pipeline = AgentSOCPipeline(settings=settings, store=store)
    result = pipeline.run_alert(load_alert(input), artifacts_dir=output_dir)
    console.print(
        {
            "incident_id": result.incident.incident_id,
            "top_action": result.ranked_actions[0].action.name if result.ranked_actions else None,
            "top_score": result.ranked_actions[0].score if result.ranked_actions else None,
            "llm_usage": result.llm_usage,
            "artifacts_dir": str(output_dir),
        }
    )


@app.command(name="benchmark")
def benchmark_cmd(
    events: Path = typer.Option(..., "--events", exists=True, readable=True),
    limit: int = typer.Option(5000, "--limit", min=1),
    concurrency: int = typer.Option(1, "--concurrency", min=1),
    artifacts: Optional[Path] = typer.Option(None, "--artifacts"),
    llm: LLMMode = typer.Option("mock", "--llm"),
) -> None:
    settings = get_settings(llm_mode=llm, artifacts_dir=artifacts)
    output_dir = artifacts or settings.artifacts_dir / "benchmark"
    try:
        summary = benchmark(
            events,
            limit=limit,
            concurrency=concurrency,
            artifacts_dir=output_dir,
            settings=settings,
            requested_llm_mode=llm,
        )
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc
    console.print(summary.model_dump(mode="json"))


if __name__ == "__main__":
    app()
