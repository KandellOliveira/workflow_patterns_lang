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


def test_screen_starts_and_exits(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: ":sair")
    exit_code = main(["screen", "--session", "test-ui"])
    assert exit_code == 0


def test_dynamic_workflow_builds_langgraph_like_graph():
    result = run_dynamic_workflow(
        prompt="Explique a causa de um erro de execução.",
        model="openrouter/anthropic/claude-3.5-sonnet",
        api_key="demo-key",
    )
    assert result["workflow"] == "dynamic"
    assert result["model"]["provider"] == "openrouter"
    assert set(result["graph"]["nodes"].keys()) >= {"planner", "subagent", "synthesizer", "verify", "evaluate"}
    assert result["stage_models"]["planner_model"]
    assert result["stage_models"]["subagent_model"]
    assert result["status"] == "completed"


def test_dynamic_workflow_loads_models_from_config_file(tmp_path):
    config = tmp_path / "models.env"
    config.write_text(
        "\n".join(
            [
                "PLANNER_MODEL=openrouter/test/planner",
                "SUBAGENT_MODEL=openrouter/test/subagent",
                "SUBAGENT_VERIFIER_MODEL=openrouter/test/verifier",
                "GLOBAL_EVALUATOR_MODEL=openrouter/test/eval",
                "SYNTHESIZER_MODEL=openrouter/test/synth",
            ]
        )
    )
    result = run_dynamic_workflow(
        prompt="Teste",
        model="openrouter/test/router",
        config_path=str(config),
    )
    assert result["stage_models"]["planner_model"] == "openrouter/test/planner"
    assert result["stage_models"]["global_evaluator_model"] == "openrouter/test/eval"
