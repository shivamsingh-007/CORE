import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.session.schema import SessionState, LoopRun


class SessionManager:
    FILE = ".loop-session.json"

    def __init__(self, project_dir: str):
        self.path = Path(project_dir).resolve() / self.FILE

    def load(self) -> SessionState:
        if not self.path.exists():
            return SessionState()
        try:
            data = json.loads(self.path.read_text())
            s = SessionState(**{k: data[k] for k in SessionState.__dataclass_fields__ if k in data})
            s.runs = [LoopRun(**r) for r in data.get("runs", [])]
            return s
        except Exception:
            return SessionState()

    def save(self, state: SessionState):
        d = state.to_dict()
        d["updated"] = datetime.utcnow().isoformat()
        try:
            self.path.write_text(json.dumps(d, indent=2, default=str))
        except OSError:
            pass

    def record_run(self, state: SessionState, run: LoopRun) -> SessionState:
        state.runs.append(run)
        state.current_state = run.state
        self.save(state)
        return state

    def clear(self):
        if self.path.exists():
            self.path.unlink()
