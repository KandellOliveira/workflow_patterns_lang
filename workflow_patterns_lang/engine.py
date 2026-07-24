from __future__ import annotations

from pathlib import Path
from typing import Any


WORKFLOW_PATTERNS = [
    {"name": "sequential", "description": "Workflow em sequência simples", "confidence": 0.86, "latency": 0.7, "cost": 0.4},
    {"name": "fanout", "description": "Distribui tarefas para múltiplos nós", "confidence": 0.78, "latency": 0.9, "cost": 0.6},
    {"name": "routing", "description": "Encaminha com base em regras", "confidence": 0.82, "latency": 0.6, "cost": 0.5},
    {"name": "human", "description": "Inclui um checkpoint humano", "confidence": 0.91, "latency": 1.0, "cost": 0.8},
    {"name": "parallel", "description": "Executa branches em paralelo", "confidence": 0.80, "latency": 0.8, "cost": 0.7},
    {"name": "branching", "description": "Escolhe entre caminhos alternativos", "confidence": 0.74, "latency": 0.75, "cost": 0.55},
]

DEFAULT_MODEL_CONFIG = {
    "planner_model": "openrouter/openai/gpt-5.5",
    "subagent_model": "openrouter/openai/gpt-5.4-mini",
    "subagent_verifier_model": "openrouter/openai/gpt-oss-120b:nitro",
    "global_evaluator_model": "openrouter/moonshotai/kimi-k2.6:nitro",
    "synthesizer_model": "openrouter/qwen/qwen3.7-max",
}

ENV_KEY_TO_STAGE = {
    "PLANNER_MODEL": "planner_model",
    "SUBAGENT_MODEL": "subagent_model",
    "SUBAGENT_VERIFIER_MODEL": "subagent_verifier_model",
    "GLOBAL_EVALUATOR_MODEL": "global_evaluator_model",
    "SYNTHESIZER_MODEL": "synthesizer_model",
}


def run_workflow_suite(pattern: str = "all", threshold: float = 0.8) -> dict[str, Any]:
    selected = WORKFLOW_PATTERNS
    if pattern != "all":
        selected = [item for item in WORKFLOW_PATTERNS if item["name"] == pattern]

    patterns = []
    for workflow in selected:
        confidence = workflow["confidence"]
        metrics = {
            "confidence": confidence,
            "latency": workflow["latency"],
            "cost": workflow["cost"],
            "risk": round(max(0.0, 1.0 - confidence), 2),
        }
        threshold_status = "meets-threshold" if confidence >= threshold else "below-threshold"
        patterns.append(
            {
                "name": workflow["name"],
                "description": workflow["description"],
                "status": "completed",
                "threshold_status": threshold_status,
                "metrics": metrics,
            }
        )

    return {"pattern": pattern, "count": len(patterns), "threshold": threshold, "patterns": patterns}


def generate_analysis_report(threshold: float = 0.8, tradeoff: str = "all") -> str:
    workflows = run_workflow_suite(pattern="all", threshold=threshold)
    selected_patterns = workflows["patterns"]

    prioritized = sorted(selected_patterns, key=lambda item: item["metrics"]["confidence"], reverse=True)
    weak = [item["name"] for item in selected_patterns if item["threshold_status"] == "below-threshold"]

    analysis = [
        "# Threshold Analysis",
        "",
        f"- Target threshold: {threshold}",
        "- Patterns meeting the threshold:",
    ]
    for item in selected_patterns:
        if item["threshold_status"] == "meets-threshold":
            analysis.append(f"  - {item['name']}: confidence {item['metrics']['confidence']:.2f}")
    if weak:
        analysis.append("- Patterns below the threshold:")
        for name in weak:
            analysis.append(f"  - {name}")
    analysis.extend([
        "- Recommendation: route high-risk branches to a human review step when confidence is below the target threshold.",
        "",
        "# Tradeoff Analysis",
        "",
    ])
    if tradeoff in {"latency", "all"}:
        analysis.append("- Latency tradeoff: sequential and human workflows increase latency but improve reliability.")
    if tradeoff in {"cost", "all"}:
        analysis.append("- Cost tradeoff: human and fanout patterns increase operational cost.")
    if tradeoff in {"accuracy", "all"}:
        analysis.append("- Accuracy tradeoff: routing and branching improve responsiveness but may reduce confidence under ambiguity.")
    analysis.append("- Suggested strategy: balance throughput with human review for critical branches.")
    analysis.append("")
    analysis.append("## Highest confidence workflows")
    for item in prioritized[:3]:
        analysis.append(f"- {item['name']}: confidence {item['metrics']['confidence']:.2f}, latency {item['metrics']['latency']:.2f}")
    return "\n".join(analysis) + "\n"


def _parse_env_file(file_path: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    path = Path(file_path)
    if not path.exists():
        return parsed

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip().strip("\"'")
    return parsed


def load_stage_models(config_path: str | None = None) -> dict[str, str]:
    models = DEFAULT_MODEL_CONFIG.copy()
    if config_path:
        parsed = _parse_env_file(config_path)
        for env_key, stage_key in ENV_KEY_TO_STAGE.items():
            if parsed.get(env_key):
                models[stage_key] = parsed[env_key]
    return models


def run_dynamic_workflow(
    prompt: str,
    model: str,
    api_key: str | None = None,
    config_path: str | None = None,
) -> dict[str, Any]:
    stage_models = load_stage_models(config_path=config_path)
    provider = "openrouter" if model.startswith("openrouter/") else "custom"
    graph = {
        "nodes": {
            "planner": {"type": "llm", "role": "plan", "model": stage_models["planner_model"]},
            "subagent": {"type": "llm", "role": "execute", "model": stage_models["subagent_model"]},
            "verify": {"type": "llm", "role": "fact-check", "model": stage_models["subagent_verifier_model"]},
            "evaluate": {"type": "llm", "role": "global-eval", "model": stage_models["global_evaluator_model"]},
            "synthesizer": {"type": "llm", "role": "final-answer", "model": stage_models["synthesizer_model"]},
        },
        "edges": [
            ("planner", "subagent"),
            ("subagent", "verify"),
            ("verify", "evaluate"),
            ("evaluate", "synthesizer"),
        ],
    }

    config = {
        "langchain": {"provider": provider, "router_model": model, "stage_models": stage_models},
        "openrouter": {"api_key": api_key or "not-provided", "model": model},
        "langgraph": {"graph": graph, "entrypoint": "planner"},
    }

    return {
        "workflow": "dynamic",
        "prompt": prompt,
        "model": {"name": model, "provider": provider},
        "stage_models": stage_models,
        "graph": graph,
        "config": config,
        "status": "completed",
    }
