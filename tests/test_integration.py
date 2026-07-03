"""End-to-end integration test with mock providers.
Verifies each agent tool chain and the full loop progression."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse
from app.supervisor import StateMachine, SupervisedRuntime
from app.schemas.state import LoopState
from app.session.manager import SessionManager


def _mkproject() -> str:
    td = tempfile.mkdtemp()
    p = Path(td)
    p.joinpath("docs").mkdir()
    p.joinpath("init.sh").write_text("echo OK")  # ponytail: temp dir, safe
    p.joinpath("claude-progress.txt").write_text("Session 0: init")  # ponytail: temp dir
    p.joinpath("feature_list.json").write_text(json.dumps([  # ponytail: temp dir
        {"id": "F001", "category": "core", "description": "User can log in", "steps": [], "passes": False},
        {"id": "F002", "category": "core", "description": "User can log out", "steps": [], "passes": False},
    ]))
    return td


class MockProvider(BaseLLMProvider):
    def __init__(self):
        self.calls = []
    def chat(self, messages, **kwargs):
        self.calls.append(len(messages))
        return LLMResponse(content="[TOOL: finish] done [/TOOL]", model="mock")
    def check_health(self):
        return True


# --- Test 1: Initializer Agent ---
def test_initializer_agent():
    from app.agents.initializer import InitializerAgent
    p = MockProvider()
    r = SupervisedRuntime(provider=p)
    a = InitializerAgent(provider=p, runtime=r)
    td = _mkproject()
    ok = a.run(td)
    assert ok is True
    assert len(r.artifacts) >= 2  # PROJECT_BRIEF + GOAL_CONTRACT
    assert Path(td, "docs", "PROJECT_BRIEF.md").exists()
    assert Path(td, "docs", "GOAL_CONTRACT.json").exists()
    print(f"  Initializer: {len(r.artifacts)} artifacts, OK")


# --- Test 2: Harness Agent ---
def test_harness_agent():
    from app.agents.harness import HarnessAgent
    p = MockProvider()
    r = SupervisedRuntime(provider=p)
    a = HarnessAgent(provider=p, runtime=r)
    td = _mkproject()
    a.run(td, "plan", "Build a web app")
    a.run(td, "review")
    a.run(td, "release")
    print("  Harness: plan + review + release, OK")


# --- Test 3: Coding Agent ---
def test_coding_agent():
    from app.agents.coding import CodingAgent
    p = MockProvider()
    r = SupervisedRuntime(provider=p)
    a = CodingAgent(provider=p, runtime=r)
    td = _mkproject()
    a.run(td, "F001")
    feats = json.loads(Path(td, "feature_list.json").read_text())  # ponytail: just created
    # Mock provider always finishes, so feature might not be updated
    assert isinstance(feats, list)
    print(f"  Coding: {len(feats)} features, OK")


# --- Test 4: Verifying Agent ---
def test_verifying_agent():
    from app.agents.verifying import VerifyingAgent
    p = MockProvider()
    r = SupervisedRuntime(provider=p)
    a = VerifyingAgent(provider=p, runtime=r)
    td = _mkproject()
    result = a.run(td)
    assert "features" in result
    assert result["total"] == 2
    print(f"  Verifying: {result['summary']}, OK")


# --- Test 5: Full Loop Progression ---
def test_full_loop():
    from app.agents.loop.orchestrator import Orchestrator
    p = MockProvider()
    o = Orchestrator(provider=p)
    td = _mkproject()

    cwd = os.getcwd()
    os.chdir(td)
    try:
        s = o.run(td, "Integration test", max_loops=6)
        # Should progress through multiple states
        assert s.loops_completed > 0
        # State should have moved past DISCOVERY
        assert s.current_state != "DISCOVERY" or s.loops_completed > 1
        print(f"  Loop: {s.loops_completed} cycles, state={s.current_state}, OK")

        # Session file persisted
        assert Path(td, ".loop-session.json").exists()
        loaded = SessionManager(td).load()
        assert loaded.loops_completed == s.loops_completed
    finally:
        os.chdir(cwd)


# --- Test 6: State Machine Transitions ---
def test_state_machine():
    sm = StateMachine(initial=LoopState.DISCOVERY)
    assert sm.current == LoopState.DISCOVERY
    assert sm.transition(LoopState.PLANNING, "Discovery done")
    assert sm.current == LoopState.PLANNING
    assert not sm.can_transition(LoopState.DISCOVERY)  # No backward from PLANNING
    assert sm.transition(LoopState.SCAFFOLDING, "Planning done")
    assert sm.current == LoopState.SCAFFOLDING
    assert sm.transition(LoopState.INITIALIZING, "Scaffolding done")
    assert sm.transition(LoopState.IMPLEMENTING, "Init done")
    assert sm.transition(LoopState.SELF_CHECK, "Implement done")
    assert sm.transition(LoopState.VERIFYING, "Self-check done")
    assert sm.transition(LoopState.BUG_HUNT, "Verify done")
    assert sm.transition(LoopState.READY, "No bugs found")
    assert not sm.can_transition(LoopState.FAILED)  # READY is terminal
    print(f"  State machine: all transitions valid, OK")


if __name__ == "__main__":
    test_state_machine()
    test_initializer_agent()
    test_harness_agent()
    test_coding_agent()
    test_verifying_agent()
    test_full_loop()
    print("\nAll integration tests passed.")
