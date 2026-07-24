from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from workflow_patterns_lang.engine import load_stage_models, run_dynamic_workflow

BANNER = r"""
  _   _   _   _   _   _   _   _   _   _
 / \ / \ / \ / \ / \ / \ / \ / \ / \ / \
( H | A | W | K | - | C | L | I | - | UI )
 \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/
"""

HELP_LINES = [
    "/pesquisar <missao>  investiga fontes locais",
    "/auditar <missao>    verifica claims e consistencia",
    ":ajuda              mostra comandos",
    ":fontes             mostra corpus local",
    ":modelos            mostra modelos por etapa",
    ":sair               encerra",
]

PROGRESS_STEPS = [
    "Interpretar missao",
    "Criar WorkflowSpec",
    "Montar harness",
    "Executar subagentes",
    "Avaliar cobertura",
    "Sintetizar resposta",
]


@dataclass
class HarnessState:
    history: List[str] = field(default_factory=list)
    progress_index: int = 0


def _clear_screen() -> None:
    print("\033[2J\033[H", end="")


def _render_progress(progress_index: int) -> str:
    lines: List[str] = ["Progress"]
    for index, step in enumerate(PROGRESS_STEPS):
        if index < progress_index:
            marker = "[x]"
        elif index == progress_index:
            marker = "[>]"
        else:
            marker = "[ ]"
        lines.append(f"{marker} {step}")
    return "\n".join(lines)


def _render_screen(state: HarnessState, prompt_name: str) -> None:
    _clear_screen()
    print(BANNER)
    print("Dynamic Workflows Harness")
    print("LangGraph + LangChain + OpenRouter")
    print("=" * 72)
    print("Ask anything... ex: /pesquisar comparar as fontes")
    print("Build: Dynamic Workflows / LangGraph / OpenRouter")
    print("=" * 72)
    print("Digite um comando ou cole uma missao para comecar.")
    print(" /pesquisar | /auditar | :ajuda | :fontes | :modelos | :sair")
    print("-" * 72)

    recent = state.history[-10:]
    if recent:
        for line in recent:
            print(line)
    else:
        print("Nenhuma execucao ainda.")

    print("-" * 72)
    print(_render_progress(state.progress_index))
    print("=" * 72)
    print(f"Sessao: {prompt_name}")


def _append(state: HarnessState, message: str) -> None:
    state.history.append(message)


def _run_mission(state: HarnessState, mission: str, mode: str) -> None:
    models = load_stage_models(config_path=".env.models")
    router_model = models["planner_model"]
    state.progress_index = 0
    _append(state, f"{mode} {mission}")

    state.progress_index = 1
    _append(state, "> Executando workflow")

    state.progress_index = 2
    _append(state, f"> planner: {models['planner_model']}")

    state.progress_index = 3
    _append(state, f"> subagent: {models['subagent_model']}")

    state.progress_index = 4
    _append(state, f"> verifier: {models['subagent_verifier_model']}")

    payload = run_dynamic_workflow(
        prompt=mission,
        model=router_model,
        config_path=".env.models",
    )

    state.progress_index = 5
    _append(state, f"> evaluator: {models['global_evaluator_model']}")
    _append(state, f"> synthesizer: {models['synthesizer_model']}")

    summary = f"Resposta pronta com {len(payload['graph']['nodes'])} nos e status {payload['status']}"
    _append(state, summary)

    state.progress_index = len(PROGRESS_STEPS)


def run_harness_ui(prompt_name: str = "hawk-dynamic") -> int:
    state = HarnessState()

    while True:
        _render_screen(state, prompt_name)
        try:
            raw = input(f"{prompt_name}: ").strip()
        except EOFError:
            print("")
            return 0

        if not raw:
            continue

        if raw == ":sair":
            return 0

        if raw == ":ajuda":
            for line in HELP_LINES:
                _append(state, line)
            continue

        if raw == ":fontes":
            _append(state, "Fontes locais: docs, resultados de testes e arquivos do projeto.")
            continue

        if raw == ":modelos":
            models = load_stage_models(config_path=".env.models")
            _append(state, "Modelos por etapa:")
            _append(state, f"- planner: {models['planner_model']}")
            _append(state, f"- subagent: {models['subagent_model']}")
            _append(state, f"- verifier: {models['subagent_verifier_model']}")
            _append(state, f"- evaluator: {models['global_evaluator_model']}")
            _append(state, f"- synthesizer: {models['synthesizer_model']}")
            continue

        if raw.startswith("/pesquisar "):
            mission = raw[len("/pesquisar "):].strip()
            _run_mission(state, mission, mode="/pesquisar")
            continue

        if raw.startswith("/auditar "):
            mission = raw[len("/auditar "):].strip()
            _run_mission(state, mission, mode="/auditar")
            continue

        _run_mission(state, raw, mode="/missao")
