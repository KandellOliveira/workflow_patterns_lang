from __future__ import annotations

from typing import Any


WORKFLOW_PATTERNS = [
    {"name": "sequential", "description": "Workflow em sequência simples", "confidence": 0.86, "latency": 0.7, "cost": 0.4},
    {"name": "fanout", "description": "Distribui tarefas para múltiplos nós", "confidence": 0.78, "latency": 0.9, "cost": 0.6},
    {"name": "routing", "description": "Encaminha com base em regras", "confidence": 0.82, "latency": 0.6, "cost": 0.5},
    {"name": "human", "description": "Inclui um checkpoint humano", "confidence": 0.91, "latency": 1.0, "cost": 0.8},
    {"name": "parallel", "description": "Executa branches em paralelo", "confidence": 0.80, "latency": 0.8, "cost": 0.7},
    {"name": "branching", "description": "Escolhe entre caminhos alternativos", "confidence": 0.74, "latency": 0.75, "cost": 0.55},
]


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
