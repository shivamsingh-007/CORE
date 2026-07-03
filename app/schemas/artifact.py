from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Artifact:
    path: str
    content: str
    type: str
    agent: str
    created_at: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
