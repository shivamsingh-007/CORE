import json
import os
import re
import subprocess

from app.providers import BaseLLMProvider, LLMMessage
from app.supervisor.runtime import SupervisedRuntime
from app.workspace.artifact_store import ArtifactStore
from app.agents.harness.prompts import HARNESS_PLAN, HARNESS_REVIEW, HARNESS_RELEASE

TOOL_PATTERN = re.compile(r"\[TOOL:\s*(\w+)\](.*?)\[/TOOL\]", re.DOTALL)


def _safe(text: str) -> str:
    return text.encode("ascii", errors="replace").decode("ascii")


class HarnessAgent:
    def __init__(self, provider: BaseLLMProvider, runtime: SupervisedRuntime):
        self.provider = provider
        self.runtime = runtime
        self.store = ArtifactStore(".")
        self.messages: list[LLMMessage] = []

    def run(self, project_dir: str, command: str, args: str = ""):
        self.store = ArtifactStore(project_dir)
        prompts = {"plan": HARNESS_PLAN, "review": HARNESS_REVIEW, "release": HARNESS_RELEASE}
        if command not in prompts:
            print(f"Unknown harness command: {command}. Use: plan, review, release")
            return

        if command == "plan":
            return self._plan_loop(args)
        if command == "review":
            return self._review_loop()
        if command == "release":
            return self._release_loop()

    def _plan_loop(self, initial_goal: str):
        self.messages = [LLMMessage(role="system", content=HARNESS_PLAN)]
        if initial_goal:
            self._send(f"I need to plan this: {initial_goal}")
        else:
            self._send("Start the planning session. Ask what needs to be built.")
        self._loop("plan")

    def _review_loop(self):
        self.messages = [LLMMessage(role="system", content=HARNESS_REVIEW)]
        self._send("Review the current project state. Check spec alignment, Plans.md, features, tests.")
        self._loop("review")

    def _release_loop(self):
        self.messages = [LLMMessage(role="system", content=HARNESS_RELEASE)]
        self._send("Check release readiness for this project.")
        self._loop("release")

    def _send(self, text: str):
        self.messages.append(LLMMessage(role="user", content=text))

    def _loop(self, mode: str):
        for _ in range(50):
            response = self.provider.chat(self.messages)
            content = response.content.strip()
            if not content:
                continue
            tools = TOOL_PATTERN.findall(content)
            clean = TOOL_PATTERN.sub("", content).strip()
            if clean:
                print(f"\n{_safe(clean)}")
            for name, args_text in tools:
                result = self._tool(name.strip(), args_text.strip())
                if result == "__FINISH__":
                    return
                self._send(result)
            if not tools:
                self.messages.append(LLMMessage(role="assistant", content=content))
        print(f"\nHarness {mode}: max turns reached.")

    def _tool(self, name: str, args_text: str) -> str:
        if name == "ask_user":
            print(f"\n{_safe(args_text)}")
            answer = input("> ").strip()
            if answer.lower() in ("exit", "quit"):
                return "__FINISH__"
            return f"User answered: {answer}"

        if name == "read_file":
            path = args_text.strip()
            data = self.store.read(path)
            if data is None:
                return f"File not found: {path}"
            return f"Content of {path}:\n---\n{data}\n---"

        if name == "run":
            cmd = args_text.strip()
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30
                )
                out = result.stdout + result.stderr
                return f"Command: {cmd}\nExit: {result.returncode}\n{out.strip()[-2000:]}"
            except subprocess.TimeoutExpired:
                return f"Command timed out: {cmd}"
            except Exception as e:
                return f"Command error: {e}"

        if name == "write_spec":
            if "|" not in args_text:
                return "Error: need 'path | content'"
            path, content = args_text.split("|", 1)
            full = self.store.write(path.strip(), content.strip())
            return f"Created {full}"

        if name == "write_plans":
            if "|" not in args_text:
                return "Error: need 'path | content'"
            path, content = args_text.split("|", 1)
            full = self.store.write(path.strip(), content.strip())
            return f"Created {full}"

        if name in ("finish_plan", "finish_review", "finish_release"):
            print(f"\n--- Harness {name.replace('finish_', '')} complete ---")
            return "__FINISH__"

        return f"Unknown tool: {name}"
