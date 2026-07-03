from typing import Optional
from app.providers import BaseLLMProvider, LLMMessage
from app.supervisor.state_machine import StateMachine
from app.schemas.task import Task, TaskStatus
from app.schemas.artifact import Artifact


class SupervisedRuntime:
    def __init__(self, provider: BaseLLMProvider, sm: Optional[StateMachine] = None):
        self.provider = provider
        self.sm = sm or StateMachine()
        self.state: dict = {}
        self.artifacts: list[Artifact] = []

    def record_artifact(self, path: str, content: str, type: str, agent: str) -> Artifact:
        a = Artifact(path=path, content=content, type=type, agent=agent)
        self.artifacts.append(a)
        return a
