from app.providers import BaseLLMProvider
from app.supervisor.state_machine import StateMachine
from app.supervisor.runtime import SupervisedRuntime
from app.schemas.state import LoopState
from app.session.schema import SessionState, LoopRun
from app.session.manager import SessionManager
from app.core_sync import sync_core_files, scaffold_loop_files


class Orchestrator:
    """Procedural loop orchestrator. Routes to agents based on state machine.
    Syncs core files after every phase. Supports goal tracking and resume."""

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self.sm = StateMachine()
        self.runtime = SupervisedRuntime(provider=provider, sm=self.sm)
        self._session_dir = "."
        self.session = SessionManager(self._session_dir)

    def _set_project(self, project_dir: str):
        self._session_dir = project_dir
        self.session = SessionManager(project_dir)

    def run(self, project_dir: str, goal: str = "", max_loops: int = 0):
        """Run the loop. max_loops=0 means run until READY or FAILED."""
        self._set_project(project_dir)
        s = self.session.load()
        s.project_dir = project_dir
        s.max_loops = max_loops or s.max_loops
        if goal:
            s.goal = goal

        if not s.runs:
            print(f"=== Loop: {s.goal} ===")
        else:
            print(f"=== Resume: {s.current_state} (loop {s.loops_completed}) ===")

        self.sm.current = LoopState(s.current_state)
        loops_run = 0
        limit = s.max_loops or 9999

        while loops_run < limit:
            state = self.sm.current
            print(f"\n[{state.value}]")

            if state == LoopState.READY:
                self._release(project_dir)
                self._sync(s)
                break

            if state == LoopState.FAILED:
                print("Failed — manual intervention required")
                self._sync(s)
                break

            handler = self._handler(state)
            try:
                result = handler(project_dir)
                self._transition(result)
                self._record(s, state, "success", str(result)[:200])
            except Exception as e:
                self.sm.transition(LoopState.FAILED, f"{state.value} failed: {e}")
                self._record(s, state, "failed", str(e))
                s.last_error = str(e)
                self._sync(s)
                raise

            self._sync(s)
            loops_run += 1

        self.session.save(s)
        self._sync(s)
        return s

    def _sync(self, s: SessionState):
        """Sync session state to core loop files after every change."""
        sync_core_files(s)
        self.session.save(s)

    def _handler(self, state: LoopState):
        handlers = {
            LoopState.DISCOVERY: self._discovery,
            LoopState.PLANNING: self._planning,
            LoopState.SCAFFOLDING: self._scaffolding,
            LoopState.INITIALIZING: self._init,
            LoopState.IMPLEMENTING: self._implement,
            LoopState.SELF_CHECK: self._self_check,
            LoopState.VERIFYING: self._verify,
            LoopState.BUG_HUNT: self._bug_hunt,
            LoopState.REWORK: self._rework,
        }
        return handlers[state]

    def _record(self, s: SessionState, state: LoopState, result: str, detail: str = ""):
        s.loops_completed += 1
        s.current_state = self.sm.current.value
        s.runs.append(LoopRun(state=state.value, agent=state.value.lower(), result=result, detail=detail))

    def _transition(self, hint: dict):
        target = LoopState(hint.get("next", self.sm.current.value))
        reason = hint.get("reason", "Handler completed")
        if self.sm.can_transition(target):
            self.sm.transition(target, reason)

    def _discovery(self, project_dir: str) -> dict:
        from app.agents.initializer.agent import InitializerAgent
        a = InitializerAgent(provider=self.provider, runtime=self.runtime)
        ok = a.run(project_dir)
        scaffold_loop_files(project_dir)
        return {"next": "PLANNING" if ok else "FAILED", "reason": "Discovery complete"}

    def _planning(self, project_dir: str) -> dict:
        from app.agents.harness.agent import HarnessAgent
        a = HarnessAgent(provider=self.provider, runtime=self.runtime)
        a.run(project_dir, "plan", "Scope the project and create spec + plans")
        return {"next": "SCAFFOLDING", "reason": "Planning complete"}

    def _scaffolding(self, project_dir: str) -> dict:
        from app.agents.harness.agent import HarnessAgent
        a = HarnessAgent(provider=self.provider, runtime=self.runtime)
        a.run(project_dir, "plan", "Write initial project files and configs")
        return {"next": "INITIALIZING", "reason": "Scaffolding complete"}

    def _init(self, project_dir: str) -> dict:
        from app.agents.initializer.agent import InitializerAgent
        a = InitializerAgent(provider=self.provider, runtime=self.runtime)
        ok = a.run(project_dir)
        scaffold_loop_files(project_dir)
        return {"next": "IMPLEMENTING" if ok else "REWORK", "reason": "Initialization complete"}

    def _implement(self, project_dir: str) -> dict:
        from app.agents.coding.agent import CodingAgent
        a = CodingAgent(provider=self.provider, runtime=self.runtime)
        a.run(project_dir, "")
        return {"next": "SELF_CHECK", "reason": "Implementation complete"}

    def _self_check(self, project_dir: str) -> dict:
        import json
        from app.workspace.artifact_store import ArtifactStore

        store = ArtifactStore(project_dir)
        data = store.read("feature_list.json")
        if not data:
            return {"next": "VERIFYING", "reason": "No feature list to check"}

        try:
            features = json.loads(data)
        except json.JSONDecodeError:
            return {"next": "REWORK", "reason": "Corrupt feature_list.json"}

        all_done = all(f.get("passes") for f in features)
        next_state = "VERIFYING" if all_done else "IMPLEMENTING"
        return {"next": next_state, "reason": f"{sum(1 for f in features if f.get('passes'))}/{len(features)} features done"}

    def _verify(self, project_dir: str) -> dict:
        from app.agents.verifying.agent import VerifyingAgent
        a = VerifyingAgent(provider=self.provider, runtime=self.runtime)
        result = a.run(project_dir)
        if result.get("passed_all"):
            return {"next": "BUG_HUNT", "reason": "All tests passed — hunting for bugs"}
        if result.get("failed", 0) > 0 and result.get("passed", 0) > 0:
            return {"next": "REWORK", "reason": f"{result.get('failed')} tests failed, {result.get('passed')} passed"}
        return {"next": "FAILED", "reason": "No tests passed"}

    def _bug_hunt(self, project_dir: str) -> dict:
        from app.agents.t3mp3st import T3MP3STAgent
        p = self.provider
        agent = T3MP3STAgent(provider=p, runtime=self.runtime)
        agent.run(project_dir)
        findings = getattr(agent, "findings", [])
        if findings:
            return {"next": "REWORK", "reason": f"Found {len(findings)} bugs — reworking"}
        return {"next": "READY", "reason": "No bugs found — ready for release"}

    def _rework(self, project_dir: str) -> dict:
        import json
        from app.workspace.artifact_store import ArtifactStore

        store = ArtifactStore(project_dir)
        data = store.read("feature_list.json")
        if not data:
            return {"next": "PLANNING", "reason": "No plan — go back to planning"}

        try:
            features = json.loads(data)
        except json.JSONDecodeError:
            return {"next": "FAILED", "reason": "Corrupt feature_list.json"}

        undone = [f for f in features if not f.get("passes")]
        if undone:
            return {"next": "IMPLEMENTING", "reason": f"{len(undone)} features remain"}
        return {"next": "PLANNING", "reason": "All features done — re-plan"}

    def _release(self, project_dir: str):
        from app.agents.harness.agent import HarnessAgent
        a = HarnessAgent(provider=self.provider, runtime=self.runtime)
        a.run(project_dir, "release")
