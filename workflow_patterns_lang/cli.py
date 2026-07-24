import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from workflow_patterns_lang.engine import run_workflow_suite, generate_analysis_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Executa padrões de workflow e gera relatório")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Executa os workflows")
    run_parser.add_argument("--pattern", choices=["all", "sequential", "fanout", "routing", "human", "parallel", "branching"], default="all")
    run_parser.add_argument("--output", type=Path, default=None)
    run_parser.add_argument("--threshold", type=float, default=0.8)

    report_parser = subparsers.add_parser("report", help="Gera um relatório de análise")
    report_parser.add_argument("--output", type=Path, default=Path("analysis.md"))
    report_parser.add_argument("--threshold", type=float, default=0.8)
    report_parser.add_argument("--tradeoff", choices=["latency", "cost", "accuracy", "all"], default="all")
    return parser


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

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
