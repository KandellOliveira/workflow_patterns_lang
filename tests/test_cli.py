import json
from pathlib import Path

from workflow_patterns_lang.cli import main


def test_run_all_patterns(tmp_path, capsys):
    output_path = tmp_path / "results.json"
    main(["run", "--pattern", "all", "--output", str(output_path), "--threshold", "0.8"])
    captured = capsys.readouterr()
    assert "sequential" in captured.out.lower()

    data = json.loads(output_path.read_text())
    assert len(data["patterns"]) == 6
    first_pattern = data["patterns"][0]
    assert "metrics" in first_pattern
    assert first_pattern["threshold_status"] in {"meets-threshold", "below-threshold"}
    assert first_pattern["metrics"]["confidence"] >= 0.0


def test_generate_report(tmp_path):
    output_path = tmp_path / "analysis.md"
    main(["report", "--output", str(output_path), "--threshold", "0.8", "--tradeoff", "latency"])
    assert output_path.exists()
    content = output_path.read_text()
    assert "Threshold Analysis" in content
    assert "Tradeoff Analysis" in content
    assert "latency" in content.lower()
