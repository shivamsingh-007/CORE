import json
import re
import subprocess

from app.providers import BaseLLMProvider, LLMMessage
from app.supervisor.runtime import SupervisedRuntime
from app.workspace.artifact_store import ArtifactStore
from app.agents.coding.prompts import CODING_SYSTEM

TOOL_PATTERN = re.compile(r"\[TOOL:\s*(\w+)\](.*?)\[/TOOL\]", re.DOTALL)


def _safe(text: str) -> str:
    return text.encode("ascii", errors="replace").decode("ascii")


class CodingAgent:
    def __init__(self, provider: BaseLLMProvider, runtime: SupervisedRuntime):
        self.provider = provider
        self.runtime = runtime
        self.store = ArtifactStore(".")
        self.messages: list[LLMMessage] = []

    def run(self, project_dir: str, task_id: str = ""):
        self.store = ArtifactStore(project_dir)
        self.messages = [LLMMessage(role="system", content=CODING_SYSTEM)]

        goal = f"Implement feature: {task_id}" if task_id else "Read the feature list and pick the next undone feature."
        self._send(f"Project: {project_dir}\nTask: {goal}")
        self._loop()

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
                print(f"\n{_safe(clean)}")
            for name, args_text in tools:
                result = self._tool(name.strip(), args_text.strip())
                if result == "__FINISH__":
                    return
                self._send(result)
            if not tools:
                self.messages.append(LLMMessage(role="assistant", content=content))
        print("\nCoding session: max turns reached.")

    def _tool(self, name: str, args_text: str) -> str:
        if name == "read_file":
            data = self.store.read(args_text.strip())
            if data is None:
                return f"File not found: {args_text}"
            return f"Content of {args_text}:\n---\n{data}\n---"

        if name == "write_file":
            if "|" not in args_text:
                return "Error: need 'path | content'"
            path, content = args_text.split("|", 1)
            full = self.store.write(path.strip(), content.strip())
            self.runtime.record_artifact(path.strip(), content.strip(), "text", "coding")
            return f"Written: {full}"

        if name == "run":
            cmd = args_text.strip()
            # Allow longer timeout for dev server, tests
            timeout = 120 if any(x in cmd for x in ["run", "test", "pytest", "npm"]) else 30
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=timeout
                )
                out = (result.stdout + result.stderr)[-3000:]
                return f"Exit: {result.returncode}\n{out.strip()}"
            except subprocess.TimeoutExpired:
                return f"Command timed out ({timeout}s): {cmd}"
            except Exception as e:
                return f"Command error: {e}"

        if name == "update_feature":
            if "|" not in args_text:
                return "Error: need 'task_id | passes:true/false'"
            fid, status = args_text.split("|", 1)
            fid = fid.strip()
            status = status.strip()
            return self._update_feature_list(fid, "true" in status.lower())

        if name == "finish_work":
            print(f"\n--- Coding session complete ---")
            print(f"{_safe(args_text)}")
            return "__FINISH__"

        return f"Unknown tool: {name}"

    def _update_feature_list(self, task_id: str, passing: bool) -> str:
        data = self.store.read("feature_list.json")
        if not data:
            return "feature_list.json not found"
        try:
            features = json.loads(data)
        except json.JSONDecodeError:
            return "Error parsing feature_list.json"

        updated = 0
        for f in features:
            if f.get("id") == task_id or f.get("description", "").startswith(task_id):
                f["passes"] = passing
                updated += 1

        if updated == 0:
            return f"No feature found for: {task_id}"
        self.store.write("feature_list.json", json.dumps(features, indent=2))
        return f"Updated {updated} feature(s) — {task_id} passes={passing}"
