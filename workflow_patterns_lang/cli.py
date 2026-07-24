import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from workflow_patterns_lang.engine import run_dynamic_workflow, run_workflow_suite, generate_analysis_report

AVAILABLE_PATTERNS = ["all", "sequential", "fanout", "routing", "human", "parallel", "branching"]
AVAILABLE_MODELS = ["pla", "sub", "verify", "eval", "synth"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa padrões de workflow e gera relatório")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Executa os workflows")
    run_parser.add_argument("--pattern", choices=AVAILABLE_PATTERNS, default="all")
    run_parser.add_argument("--output", type=Path, default=None)
    run_parser.add_argument("--threshold", type=float, default=0.8)

    report_parser = subparsers.add_parser("report", help="Gera um relatório de análise")
    report_parser.add_argument("--output", type=Path, default=Path("analysis.md"))
    report_parser.add_argument("--threshold", type=float, default=0.8)
    report_parser.add_argument("--tradeoff", choices=["latency", "cost", "accuracy", "all"], default="all")

    dynamic_parser = subparsers.add_parser("dynamic", help="Executa um workflow dinâmico com configuração LangGraph + LangChain + OpenRouter")
    dynamic_parser.add_argument("--prompt", required=True)
    dynamic_parser.add_argument("--model", default="openrouter/anthropic/claude-3.5-sonnet")
    dynamic_parser.add_argument("--api-key", default=None)
    dynamic_parser.add_argument("--output", type=Path, default=None)

    shell_parser = subparsers.add_parser("shell", help="Abre um terminal interativo com comandos e modelos")
    shell_parser.add_argument("--prompt", default="workflow>")
    return parser


def print_help_banner() -> None:
    print("Available workflow commands:")
    for pattern in AVAILABLE_PATTERNS:
        print(f"  - {pattern}")
    print("\nAvailable models:")
    for model in AVAILABLE_MODELS:
        print(f"  - {model}")
    print("\nExamples:")
    print("  run --pattern sequential --threshold 0.8")
    print("  report --tradeoff latency")
    print("  shell")


def run_shell(prompt: str) -> None:
    print("Interactive workflow shell")
    print("Type 'help' to list commands, 'exit' to quit.")
    while True:
        try:
            raw = input(f"{prompt} ")
        except EOFError:
            print("")
            break

        command = raw.strip()
        if not command:
            continue
        if command in {"exit", "quit"}:
            break
        if command == "help":
            print_help_banner()
            continue

        parts = command.split()
        if parts[0] == "run":
            pattern = "all"
            threshold = 0.8
            output = None
            for index, token in enumerate(parts[1:], start=1):
                if token == "--pattern" and index + 1 < len(parts):
                    pattern = parts[index + 1]
                elif token == "--threshold" and index + 1 < len(parts):
                    threshold = float(parts[index + 1])
                elif token == "--output" and index + 1 < len(parts):
                    output = Path(parts[index + 1])
            payload = run_workflow_suite(pattern=pattern, threshold=threshold)
            if output is not None:
                output.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            for workflow in payload["patterns"]:
                print(f"- {workflow['name']}: {workflow['threshold_status']}")
            continue

        if parts[0] == "report":
            tradeoff = "all"
            threshold = 0.8
            output = Path("analysis.md")
            for index, token in enumerate(parts[1:], start=1):
                if token == "--tradeoff" and index + 1 < len(parts):
                    tradeoff = parts[index + 1]
                elif token == "--threshold" and index + 1 < len(parts):
                    threshold = float(parts[index + 1])
                elif token == "--output" and index + 1 < len(parts):
                    output = Path(parts[index + 1])
            report = generate_analysis_report(threshold=threshold, tradeoff=tradeoff)
            output.write_text(report)
            print(f"Wrote report to {output}")
            continue

        if parts[0] in AVAILABLE_MODELS:
            print(f"Model {parts[0]} selected")
            continue

        print(f"Unknown command: {parts[0]}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        payload = run_workflow_suite(pattern=args.pattern, threshold=args.threshold)
        if args.output is not None:
            args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"Executed {payload['count']} patterns")
        for pattern in payload["patterns"]:
            print(f"- {pattern['name']}: {pattern['threshold_status']}")
        return 0

    if args.command == "report":
        report = generate_analysis_report(threshold=args.threshold, tradeoff=args.tradeoff)
        args.output.write_text(report)
        print(f"Wrote analysis report to {args.output}")
        return 0

    if args.command == "dynamic":
        payload = run_dynamic_workflow(prompt=args.prompt, model=args.model, api_key=args.api_key)
        if args.output is not None:
            args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"Dynamic workflow executed with model {payload['model']['name']}")
        print(f"Graph nodes: {', '.join(payload['graph']['nodes'].keys())}")
        return 0

    if args.command == "shell":
        run_shell(args.prompt)
        return 0

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
