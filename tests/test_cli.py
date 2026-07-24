import io
import json
from contextlib import redirect_stdout

from workflow_patterns_lang.cli import main
from workflow_patterns_lang.engine import run_dynamic_workflow


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


def test_shell_lists_commands_and_models(monkeypatch):
    inputs = iter(["help", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    output = io.StringIO()
    with redirect_stdout(output):
        main(["shell", "--prompt", "wf"])
    text = output.getvalue()
    assert "Available workflow commands:" in text
    assert "pla" in text
    assert "verify" in text
    assert "synth" in text


def test_dynamic_workflow_builds_langgraph_like_graph():
    result = run_dynamic_workflow(
        prompt="Explique a causa de um erro de execução.",
        model="openrouter/anthropic/claude-3.5-sonnet",
        api_key="demo-key",
    )
    assert result["workflow"] == "dynamic"
    assert result["model"]["provider"] == "openrouter"
    assert set(result["graph"]["nodes"].keys()) >= {"planner", "critic", "synthesizer", "verify"}
    assert result["status"] == "completed"
