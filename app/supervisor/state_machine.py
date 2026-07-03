from app.schemas.state import LoopState

TRANSITIONS = {
    LoopState.DISCOVERY: [LoopState.PLANNING, LoopState.FAILED],
    LoopState.PLANNING: [LoopState.SCAFFOLDING, LoopState.INITIALIZING, LoopState.REWORK],
    LoopState.SCAFFOLDING: [LoopState.INITIALIZING, LoopState.REWORK],
    LoopState.INITIALIZING: [LoopState.IMPLEMENTING, LoopState.REWORK],
    LoopState.IMPLEMENTING: [LoopState.SELF_CHECK, LoopState.REWORK, LoopState.FAILED],
    LoopState.SELF_CHECK: [LoopState.VERIFYING, LoopState.REWORK],
    LoopState.VERIFYING: [LoopState.BUG_HUNT, LoopState.REWORK, LoopState.FAILED],
    LoopState.BUG_HUNT: [LoopState.READY, LoopState.REWORK],
    LoopState.REWORK: [LoopState.IMPLEMENTING, LoopState.PLANNING, LoopState.FAILED],
    LoopState.READY: [],
    LoopState.FAILED: [],
}


class StateMachine:
    def __init__(self, initial: LoopState = LoopState.DISCOVERY):
        self.current = initial
        self.history: list[tuple[LoopState, LoopState, str]] = []

    def can_transition(self, target: LoopState) -> bool:
        return target in TRANSITIONS[self.current]

    def transition(self, target: LoopState, reason: str) -> bool:
        if not self.can_transition(target):
            return False
        self.history.append((self.current, target, reason))
        self.current = target
        return True
