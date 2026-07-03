import json
import os
import re
import subprocess
from datetime import datetime
from typing import Optional

from app.providers import BaseLLMProvider, LLMMessage
from app.supervisor.runtime import SupervisedRuntime
from app.workspace.artifact_store import ArtifactStore
from app.core_sync import scaffold_loop_files

TOOL_PATTERN = re.compile(r"\[TOOL:\s*(\w+)\](.*?)\[/TOOL\]", re.DOTALL)


class InitializerAgent:
    def __init__(self, provider: BaseLLMProvider, runtime: "SupervisedRuntime"):
        self.provider = provider
        self.runtime = runtime
        self.store = ArtifactStore(".")
        self.messages: list[LLMMessage] = []
        self.knowledge: dict = {}

    def run(self, project_dir: str) -> bool:
        self.store = ArtifactStore(project_dir)
        self.messages = [
            LLMMessage(role="system", content=self._system_prompt())
        ]

        print("\n=== Initializer Agent (Harness Setup) ===")
        print("I'll interview you to understand your project, then set up")
        print("the harness environment per Anthropic's long-running agent patterns.\n")

        self._send(f"Project directory: {project_dir}\n\nStart the interview.")
        self._loop()
        return True

    def _system_prompt(self) -> str:
        return """You are the INITIALIZER AGENT — the very first session in a long-running agent harness.

Your job is to interview the user and then set up the environment so that
future coding agents can work incrementally across many context windows
without losing state or declaring victory too early.

Per Anthropic's effective harnesses research, you must create:

1. FEATURE_LIST.json — A comprehensive JSON file listing every feature the
   project needs. Each feature has: category, description, steps (array of
   strings), and "passes": false. The coding agent will work on ONE feature
   at a time and flip passes to true only after end-to-end testing.

2. INIT.SH — A shell script that installs deps and starts the dev server.
   The coding agent runs this every session to verify the app still works
   before starting new work.

3. CLAUDE-PROGRESS.txt — A running log of what each agent session does.
   The coding agent reads this + git log at the start of every session.

4. GIT REPO — Initialize git and make the first commit so the coding agent
   can use git log for context and git revert for recovery.

5. PROJECT_BRIEF.md + GOAL_CONTRACT.json — The project description
   captured from the interview.

6. LOOP FILES — Call create_loop_files to scaffold AGENTS.md, loop-rules.md,
   LOOP.md, context.md, state.md, and tasks/ files. These files track loop
   state and are synced after every change in the autonomous loop.

INTERVIEW RULES:
- Ask ONE question at a time.
- Track what you know. Don't repeat questions.
- When you understand the project well enough (name, stack, goal, features,
  target users, how to run the app), generate all harness files.

TOOLS:
[TOOL: ask_user] your question [/TOOL]
[TOOL: create_artifact] path | content [/TOOL]
[TOOL: create_feature_list] path | JSON array of features [/TOOL]
[TOOL: create_init_script] path | content [/TOOL]
[TOOL: init_git] commit message [/TOOL]
[TOOL: create_loop_files] — scaffold AGENTS.md, loop-rules.md, LOOP.md, context.md, state.md, tasks/ [/TOOL]
[TOOL: finish] project summary [/TOOL]"""

    def _send(self, text: str):
        self.messages.append(LLMMessage(role="user", content=text))

    def _loop(self):
        for _ in range(100):
            response = self.provider.chat(self.messages)
            content = response.content.strip()
            if not content:
                continue
            tools = TOOL_PATTERN.findall(content)
            clean = TOOL_PATTERN.sub("", content).strip()
            if clean:
                safe = clean.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
                safe = safe.encode("ascii", errors="replace").decode("ascii", errors="replace")
                print(f"\n{safe}")
            for name, args in tools:
                result = self._tool(name.strip(), args.strip())
                if result == "__FINISH__":
                    return
                self._send(result)

            if not tools:
                self.messages.append(LLMMessage(role="assistant", content=content))

        print("\nMax turns reached. Running finish with what we have.")
        self._finish("Interview timed out after 100 turns.")

    def _tool(self, name: str, args: str) -> str:
        if name == "ask_user":
            safe = args.encode("ascii", errors="replace").decode("ascii", errors="replace")
            print(f"\n{safe}")
            answer = input("> ").strip()
            if answer.lower() in ("exit", "quit"):
                return "__FINISH__"
            self._capture_knowledge(args, answer)
            return f"User answered: {answer}"

        if name == "create_artifact":
            if "|" not in args:
                return "Error: need 'path | content'"
            path, content = args.split("|", 1)
            full = self.store.write(path.strip(), content.strip())
            self.runtime.record_artifact(
                path.strip(), content.strip(), self._ext(path), "initializer"
            )
            return f"Created {full}"

        if name == "create_feature_list":
            if "|" not in args:
                return "Error: need 'path | JSON array'"
            path, features_raw = args.split("|", 1)
            path = path.strip()
            try:
                features = json.loads(features_raw.strip())
                content = json.dumps(features, indent=2)
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON — {e}"
            full = self.store.write(path, content)
            self.runtime.record_artifact(path, content, "json", "initializer")
            return f"Created {full} with {len(features)} features"

        if name == "create_init_script":
            if "|" not in args:
                return "Error: need 'path | content'"
            path, content = args.split("|", 1)
            path = path.strip()
            full = self.store.write(path, content.strip())
            os.chmod(full, 0o755)
            self.runtime.record_artifact(path, content.strip(), "shell", "initializer")
            return f"Created {full}"

        if name == "init_git":
            return self._init_git(args)

        if name == "create_loop_files":
            created = scaffold_loop_files(str(self.store.root))
            if created:
                return f"Created loop files: {', '.join(created)}"
            return "Loop files already exist (no new files created)"

        if name == "finish":
            self._finish(args)
            return "__FINISH__"

        return f"Unknown tool: {name}"

    def _init_git(self, commit_msg: str) -> str:
        try:
            result = subprocess.run(
                ["git", "init"], capture_output=True, text=True, timeout=10
            )
            out = result.stdout + result.stderr
            subprocess.run(
                ["git", "add", "-A"], capture_output=True, text=True, timeout=10
            )
            result2 = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True, text=True, timeout=10,
            )
            out += result2.stdout + result2.stderr
            return f"Git repo initialized.\n{out.strip()}"
        except Exception as e:
            return f"Git init failed (non-fatal): {e}"

    def _finish(self, summary: str):
        """Write all bootstrap artifacts, then print summary."""
        name = self.knowledge.get("project_name", "my-project")
        desc = self.knowledge.get("description", "")
        goal = self.knowledge.get("goal", "")

        files = {
            "docs/PROJECT_BRIEF.md": (
                f"# {name}\n\n"
                f"## Description\n{desc}\n\n"
                f"## Goal\n{goal}\n\n"
                f"## Interview Summary\n{summary}\n"
            ),
            "docs/GOAL_CONTRACT.json": json.dumps({
                "project": name,
                "goal": goal,
                "stack": self.knowledge.get("stack", ""),
                "knowledge": self.knowledge,
                "summary": summary,
            }, indent=2, default=str),
        }

        print("\n--- Harness Artifacts ---")
        for path, content in files.items():
            self.store.write(path, content)
            self.runtime.record_artifact(path, content, "markdown" if path.endswith(".md") else "json", "initializer")
            safe_path = path.encode("ascii", errors="replace").decode("ascii")
            print(f"  {safe_path}")

        print("\nHarness setup complete.")
        safe_knowledge = json.dumps(self.knowledge, indent=2, default=str)
        safe_knowledge = safe_knowledge.encode("ascii", errors="replace").decode("ascii")
        print(f"Knowledge captured: {safe_knowledge}")

    def _capture_knowledge(self, question: str, answer: str):
        topics = {
            "name": "project_name", "project": "project_name", "called": "project_name",
            "do": "description",
            "stack": "stack", "tech": "stack", "language": "stack", "framework": "stack",
            "goal": "goal", "problem": "goal", "objective": "goal",
            "user": "target_user", "audience": "target_user", "who": "target_user",
            "constraint": "constraints", "limit": "constraints", "deadline": "constraints",
            "feature": "features", "functionality": "features",
            "run": "run_command", "start": "run_command", "dev": "run_command",
            "test": "test_command", "deploy": "deploy_target",
        }
        q = question.lower()
        for word, key in topics.items():
            if word in q:
                self.knowledge[key] = answer
                return

    def _ext(self, path: str) -> str:
        return {"md": "markdown", "json": "json", "yaml": "yaml", "sh": "shell", "py": "python", "txt": "text"}.get(
            path.rsplit(".", 1)[-1].lower(), "text"
        )
