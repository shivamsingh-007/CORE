from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    id: str
    description: str
    agent: str
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    result: Optional[str] = None
    error: Optional[str] = None
