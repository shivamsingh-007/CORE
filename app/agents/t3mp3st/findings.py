from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingKind(str, Enum):
    MISSING_ERROR_HANDLING = "missing_error_handling"
    TYPE_SAFETY = "type_safety"
    ENCODING = "encoding"
    UNREACHABLE = "unreachable"
    RACE_CONDITION = "race_condition"
    STATE_LEAK = "state_leak"
    IMPORT_CYCLE = "import_cycle"
    SECURITY = "security"
    LOGIC_BUG = "logic_bug"
    CODE_SMELL = "code_smell"
    PONYTALL_DEBT = "ponytail_debt"


@dataclass
class Finding:
    kind: FindingKind
    severity: Severity
    file: str
    line: int
    title: str
    detail: str
    evidence: str = ""
    fix: str = ""
    operator: str = "recon"
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "kind": self.kind.value,
            "severity": self.severity.value,
            "file": self.file,
            "line": self.line,
            "title": self.title,
            "detail": self.detail,
            "evidence": self.evidence,
            "fix": self.fix,
            "operator": self.operator,
        }
