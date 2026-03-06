"""Definicao do Crew de Planejamento de Viagem."""

import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM
from crewai_tools import SerperDevTool

CONFIG_DIR = Path(__file__).parent / "config"


def _load_yaml(filename: str) -> dict:
    with open(CONFIG_DIR / filename, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_crew() -> Crew:
    """Constroi e retorna o Crew de planejamento de viagem."""
    agents_cfg = _load_yaml("agents.yaml")
    tasks_cfg = _load_yaml("tasks.yaml")

    llm = LLM(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        temperature=0.7,
    )

    search_tool = SerperDevTool()

    # --- Agentes ---
    researcher = Agent(
        **agents_cfg["destination_researcher"],
        llm=llm,
        tools=[search_tool],
    )

    curator = Agent(
        **agents_cfg["experience_curator"],
        llm=llm,
    )

    writer = Agent(
        **agents_cfg["itinerary_writer"],
        llm=llm,
    )

    # --- Tasks ---
    # Remover campo 'agent' do YAML (e' apenas referencia, passamos o objeto)
    for task_cfg in tasks_cfg.values():
        task_cfg.pop("agent", None)

    research_task = Task(
        **tasks_cfg["research_task"],
        agent=researcher,
    )

    curation_task = Task(
        **tasks_cfg["curation_task"],
        agent=curator,
        context=[research_task],
    )

    itinerary_task = Task(
        **tasks_cfg["itinerary_task"],
        agent=writer,
        context=[research_task, curation_task],
    )

    return Crew(
        agents=[researcher, curator, writer],
        tasks=[research_task, curation_task, itinerary_task],
        process=Process.sequential,
        verbose=True,
        language="pt-BR",
    )
