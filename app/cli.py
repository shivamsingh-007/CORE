import argparse
import sys


def _get_provider():
    from app.providers import provider_from_config
    p = provider_from_config()
    if not p.check_health():
        print(f"Provider {p.base_url} not reachable.")
        print("Set LLM_BASE_URL or start Ollama, or set OPENROUTER_API_KEY.")
        sys.exit(1)
    return p


def cmd_init(args):
    p = _get_provider()
    from app.supervisor import StateMachine, SupervisedRuntime
    from app.schemas.state import LoopState
    sm = StateMachine(initial=LoopState.INITIALIZING)
    r = SupervisedRuntime(provider=p, sm=sm)
    from app.agents.initializer import InitializerAgent
    agent = InitializerAgent(provider=p, runtime=r)
    agent.run(args.project_dir)
    print(f"\nState: {r.sm.current.value}")
    print(f"Artifacts: {len(r.artifacts)}")


def cmd_harness(args):
    p = _get_provider()
    from app.supervisor import SupervisedRuntime
    r = SupervisedRuntime(provider=p)
    from app.agents.harness import HarnessAgent
    agent = HarnessAgent(provider=p, runtime=r)
    agent.run(args.project_dir, args.harness_command, args.goal or "")


def cmd_coding(args):
    p = _get_provider()
    from app.supervisor import SupervisedRuntime
    r = SupervisedRuntime(provider=p)
    from app.agents.coding import CodingAgent
    agent = CodingAgent(provider=p, runtime=r)
    agent.run(args.project_dir, args.task_id or "")


def cmd_hunt(args):
    from app.agents.t3mp3st import T3MP3STAgent
    try:
        p = _get_provider()
    except SystemExit:
        p = None
        print("[hunt] No LLM provider — static + dynamic analysis only")
    agent = T3MP3STAgent(provider=p, runtime=None)
    agent.run(args.project_dir)


def cmd_loop(args):
    p = _get_provider()
    from app.agents.loop.orchestrator import Orchestrator
    o = Orchestrator(provider=p)
    s = o.run(args.project_dir, args.goal or "Full loop execution", args.max_loops)
    _print_loop_result(s)


def cmd_go(args):
    """Single entry point: init + loop with auto-sync."""
    from app.core_sync import scaffold_loop_files

    scaffold_loop_files(args.project_dir)

    p = _get_provider()
    from app.agents.loop.orchestrator import Orchestrator
    o = Orchestrator(provider=p)
    s = o.run(args.project_dir, args.goal or args.command_args or "", args.max_loops)
    _print_loop_result(s)


def _print_loop_result(s):
    print(f"\n=== Loop complete ===")
    print(f"State: {s.current_state}")
    print(f"Loops: {s.loops_completed}")
    for run in s.runs[-3:]:
        print(f"  {run.state}: {run.result} — {run.detail[:80]}")
    if s.last_error:
        print(f"Error: {s.last_error}")


def main():
    parser = argparse.ArgumentParser(prog="loop-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initializer Agent: interview + harness setup")
    init.add_argument("--project-dir", default=".")

    harness = sub.add_parser("harness", help="Harness Agent: plan | review | release")
    harness.add_argument("harness_command", choices=["plan", "review", "release"])
    harness.add_argument("--project-dir", default=".")
    harness.add_argument("--goal", default="", help="Goal for plan mode")

    coding = sub.add_parser("coding", help="Coding Agent: implement one feature per session")
    coding.add_argument("--project-dir", default=".")
    coding.add_argument("--task-id", default="", help="Feature ID to implement")

    loop = sub.add_parser("loop", help="Autonomous loop: runs DISCOVERY through READY")
    loop.add_argument("--project-dir", default=".")
    loop.add_argument("--goal", default="", help="Project goal")
    loop.add_argument("--max-loops", type=int, default=10, help="Max iterations")

    t3 = sub.add_parser("hunt", help="T3MP3ST bug hunter: scan + test + review")
    t3.add_argument("--project-dir", default=".")

    go = sub.add_parser("go", help="Single entry: init + autonomous loop with auto-sync")
    go.add_argument("--project-dir", default=".")
    go.add_argument("--goal", default="", help="Project goal")
    go.add_argument("command_args", nargs="*", help="Goal as positional args (fallback)")
    go.add_argument("--max-loops", type=int, default=0, help="Max iterations (0 = unlimited)")

    args = parser.parse_args()
    if args.command == "init":
        cmd_init(args)
    elif args.command == "harness":
        cmd_harness(args)
    elif args.command == "coding":
        cmd_coding(args)
    elif args.command == "loop":
        cmd_loop(args)
    elif args.command == "hunt":
        cmd_hunt(args)
    elif args.command == "go":
        cmd_go(args)


if __name__ == "__main__":
    main()
