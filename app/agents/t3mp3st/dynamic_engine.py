import importlib
import sys
import traceback
from pathlib import Path
from typing import Optional
from app.agents.t3mp3st.findings import Finding, Severity, FindingKind


class DynamicEngine:
    """Runtime testing with edge cases. T3MP3ST Exploiter operator."""

    def __init__(self, project_dir: str):
        self.root = Path(project_dir).resolve()
        self.findings: list[Finding] = []

    def run(self) -> list[Finding]:
        self.findings = []
        sys.path.insert(0, str(self.root))
        self._test_imports()
        self._test_state_machine()
        self._test_runtime_creation()
        self._test_session_load_failures()
        if "app" in sys.modules:
            del sys.modules["app"]
        for m in list(sys.modules.keys()):
            if m.startswith("app."):
                del sys.modules[m]
        sys.path.pop(0)
        return self.findings

    def _try_import(self, mod_path: str) -> Optional[object]:
        try:
            return importlib.import_module(mod_path)
        except Exception as e:
            self.findings.append(Finding(
                kind=FindingKind.IMPORT_CYCLE,
                severity=Severity.HIGH,
                file=mod_path, line=0,
                title=f"Module import failed: {mod_path}",
                detail=f"{type(e).__name__}: {e}",
                evidence=traceback.format_exc()[-500:],
                operator="dynamic"))
            return None

    def _test_imports(self):
        modules = [
            "app.providers", "app.providers.base", "app.providers.openai_compat",
            "app.schemas", "app.schemas.state", "app.schemas.task", "app.schemas.artifact",
            "app.supervisor", "app.supervisor.state_machine", "app.supervisor.runtime",
            "app.workspace", "app.workspace.artifact_store",
            "app.session", "app.session.schema", "app.session.manager",
            "app.agents.harness", "app.agents.coding", "app.agents.initializer",
            "app.agents.verifying", "app.agents.loop.orchestrator",
        ]
        for mod_name in modules:
            mod = self._try_import(mod_name)
            if mod is None:
                continue
            expected = {
                "app.providers": ["BaseLLMProvider", "LLMMessage", "LLMResponse", "provider_from_config"],
                "app.schemas": ["LoopState", "Task", "TaskStatus", "Artifact"],
                "app.supervisor": ["StateMachine", "TRANSITIONS", "SupervisedRuntime"],
                "app.session": ["SessionManager", "SessionState", "LoopRun"],
                "app.agents.initializer": ["InitializerAgent"],
                "app.agents.harness": ["HarnessAgent"],
                "app.agents.coding": ["CodingAgent"],
                "app.agents.verifying": ["VerifyingAgent"],
            }
            for prefix, names in expected.items():
                if mod.__name__ == prefix:
                    for name in names:
                        if not hasattr(mod, name):
                            self.findings.append(Finding(
                                kind=FindingKind.IMPORT_CYCLE,
                                severity=Severity.MEDIUM,
                                file=mod.__name__, line=0,
                                title=f"Missing expected export: {name}",
                                detail=f"Module {mod.__name__} should export {name}",
                                operator="dynamic"))

    def _test_state_machine(self):
        from app.supervisor.state_machine import StateMachine, TRANSITIONS
        from app.schemas.state import LoopState

        sm = StateMachine()
        assert sm.current == LoopState.DISCOVERY, "Initial state should be DISCOVERY"

        # Verify all TRANSITIONS keys are valid LoopStates
        for state in TRANSITIONS:
            try:
                LoopState(state)
            except ValueError:
                self.findings.append(Finding(
                    kind=FindingKind.TYPE_SAFETY,
                    severity=Severity.HIGH,
                    file="app/supervisor/state_machine.py", line=0,
                    title=f"Invalid state in TRANSITIONS: {state}",
                    detail=f"'{state}' is not a valid LoopState",
                    operator="dynamic"))

        # Verify terminal states (READY, FAILED) accept no transitions
        terminal_states = {LoopState.READY, LoopState.FAILED}
        for src in terminal_states:
            for dst in LoopState:
                if dst == src:
                    continue
                sm = StateMachine(initial=src)
                ok = sm.transition(dst, "test")
                if ok:
                    self.findings.append(Finding(
                        kind=FindingKind.STATE_LEAK,
                        severity=Severity.LOW,
                        file="app/supervisor/state_machine.py", line=0,
                        title=f"Terminal state {src} allows transition to {dst}",
                        detail=f"READY and FAILED should not transition anywhere — transition succeeded",
                        operator="dynamic"))

    def _test_runtime_creation(self):
        from app.supervisor.runtime import SupervisedRuntime
        from app.supervisor.state_machine import StateMachine
        sm = StateMachine()
        # Test runtime with minimal args
        try:
            r = SupervisedRuntime(provider=None, sm=sm)
            assert r.sm is sm, "Runtime should use provided SM"
            r.record_artifact("test.txt", "content", "text", "test")
            assert len(r.artifacts) == 1
        except Exception as e:
            self.findings.append(Finding(
                kind=FindingKind.MISSING_ERROR_HANDLING,
                severity=Severity.HIGH,
                file="app/supervisor/runtime.py", line=0,
                title="Runtime creation failed",
                detail=str(e),
                operator="dynamic"))

    def _test_session_load_failures(self):
        import tempfile, json
        from pathlib import Path
        from app.session.manager import SessionManager
        from app.session.schema import SessionState

        td = tempfile.mkdtemp()
        # Test loading non-existent file
        s = SessionManager(td).load()
        assert isinstance(s, SessionState), "Should return empty SessionState"

        # Test loading corrupt JSON
        bad = Path(td) / ".loop-session.json"
        bad.write_text("{{{corrupt")  # ponytail: temp test file, safe
        s2 = SessionManager(td).load()
        assert isinstance(s2, SessionState), "Should handle corrupt JSON gracefully"

        # Test session roundtrip
        mgr = SessionManager(td)
        state = SessionState(project_dir=td, current_state="TEST", loops_completed=5)
        mgr.save(state)
        loaded = mgr.load()
        assert loaded.loops_completed == 5, "Session roundtrip should preserve data"

        self.findings.append(Finding(
            kind=FindingKind.CODE_SMELL,
            severity=Severity.INFO,
            file="app/session/manager.py", line=0,
            title="Session manager handles corruption gracefully",
            detail="Confirmed: corrupt JSON returns empty SessionState, not crash",
            fix="None needed",
            operator="dynamic"))
