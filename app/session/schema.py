from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class LoopRun:
    state: str
    agent: str
    result: str  # success | failed | timeout
    detail: str = ""


@dataclass
class SessionState:
    project_dir: str = ""
    current_state: str = "DISCOVERY"
    loops_completed: int = 0
    max_loops: int = 10
    goal: str = ""
    runs: list = field(default_factory=list)
    features_done: list = field(default_factory=list)
    features_total: int = 0
    last_error: str = ""

    def to_dict(self):
        return asdict(self)
