"""Event listener para feedback de progresso em tempo real."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum

from crewai.events.base_event_listener import BaseEventListener
from crewai.events.event_types import (
    AgentExecutionCompletedEvent,
    AgentExecutionErrorEvent,
    AgentExecutionStartedEvent,
    CrewKickoffCompletedEvent,
    CrewKickoffFailedEvent,
    CrewKickoffStartedEvent,
    TaskCompletedEvent,
    TaskStartedEvent,
    ToolUsageErrorEvent,
    ToolUsageFinishedEvent,
    ToolUsageStartedEvent,
)


class StepType(Enum):
    CREW = "crew"
    AGENT = "agent"
    TASK = "task"
    TOOL = "tool"


@dataclass
class ProgressStep:
    step_type: StepType
    message: str
    status: str = "running"  # running, done, error


@dataclass
class ProgressState:
    """Estado compartilhado de progresso entre listener e UI."""

    steps: list[ProgressStep] = field(default_factory=list)
    is_running: bool = False
    is_complete: bool = False
    has_error: bool = False
    error_message: str = ""
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add_step(self, step: ProgressStep) -> None:
        with self._lock:
            self.steps.append(step)

    def complete_last_of_type(self, step_type: StepType) -> None:
        with self._lock:
            for step in reversed(self.steps):
                if step.step_type == step_type and step.status == "running":
                    step.status = "done"
                    break

    def error_last_of_type(self, step_type: StepType) -> None:
        with self._lock:
            for step in reversed(self.steps):
                if step.step_type == step_type and step.status == "running":
                    step.status = "error"
                    break

    def reset(self) -> None:
        with self._lock:
            self.steps.clear()
            self.is_running = False
            self.is_complete = False
            self.has_error = False
            self.error_message = ""


# Estado global de progresso — compartilhado entre listener e Streamlit
progress_state = ProgressState()


class ProgressListener(BaseEventListener):
    """Listener que captura eventos do CrewAI e atualiza o estado de progresso."""

    def setup_listeners(self, crewai_event_bus) -> None:
        @crewai_event_bus.on(CrewKickoffStartedEvent)
        def on_crew_started(source, event: CrewKickoffStartedEvent):
            progress_state.reset()
            progress_state.is_running = True
            progress_state.add_step(
                ProgressStep(StepType.CREW, "Crew de planejamento iniciado")
            )

        @crewai_event_bus.on(CrewKickoffCompletedEvent)
        def on_crew_completed(source, event: CrewKickoffCompletedEvent):
            progress_state.complete_last_of_type(StepType.CREW)
            progress_state.is_running = False
            progress_state.is_complete = True

        @crewai_event_bus.on(CrewKickoffFailedEvent)
        def on_crew_failed(source, event: CrewKickoffFailedEvent):
            progress_state.error_last_of_type(StepType.CREW)
            progress_state.is_running = False
            progress_state.has_error = True
            progress_state.error_message = str(getattr(event, "error", "Erro desconhecido"))

        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_started(source, event: AgentExecutionStartedEvent):
            role = getattr(event.agent, "role", "Agente")
            progress_state.add_step(
                ProgressStep(StepType.AGENT, f"Agente '{role}' em acao")
            )

        @crewai_event_bus.on(AgentExecutionCompletedEvent)
        def on_agent_completed(source, event: AgentExecutionCompletedEvent):
            progress_state.complete_last_of_type(StepType.AGENT)

        @crewai_event_bus.on(AgentExecutionErrorEvent)
        def on_agent_error(source, event: AgentExecutionErrorEvent):
            progress_state.error_last_of_type(StepType.AGENT)

        @crewai_event_bus.on(TaskStartedEvent)
        def on_task_started(source, event: TaskStartedEvent):
            task = getattr(event, "task", None)
            desc = ""
            if task:
                desc = getattr(task, "description", "") or ""
            label = desc[:80] + "..." if len(desc) > 80 else desc
            progress_state.add_step(
                ProgressStep(StepType.TASK, f"Task iniciada: {label}" if label else "Task iniciada")
            )

        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event: TaskCompletedEvent):
            progress_state.complete_last_of_type(StepType.TASK)

        @crewai_event_bus.on(ToolUsageStartedEvent)
        def on_tool_started(source, event: ToolUsageStartedEvent):
            tool = getattr(event, "tool_name", "ferramenta")
            progress_state.add_step(
                ProgressStep(StepType.TOOL, f"Usando ferramenta: {tool}")
            )

        @crewai_event_bus.on(ToolUsageFinishedEvent)
        def on_tool_finished(source, event: ToolUsageFinishedEvent):
            progress_state.complete_last_of_type(StepType.TOOL)

        @crewai_event_bus.on(ToolUsageErrorEvent)
        def on_tool_error(source, event: ToolUsageErrorEvent):
            progress_state.error_last_of_type(StepType.TOOL)


# Instanciar para registrar automaticamente no event bus
progress_listener = ProgressListener()
