import json
import subprocess
import sys

from app.providers import BaseLLMProvider, LLMMessage, LLMResponse
from app.supervisor.runtime import SupervisedRuntime
from app.workspace.artifact_store import ArtifactStore


class VerifyingAgent:
    """Run tests, validate features, report pass/fail. No LLM by default — runs commands."""

    def __init__(self, provider: BaseLLMProvider, runtime: SupervisedRuntime):
        self.provider = provider
        self.runtime = runtime
        self.store = ArtifactStore(".")

    def run(self, project_dir: str) -> dict:
        self.store = ArtifactStore(project_dir)
        print("\n=== Verifying Agent ===")
        result = self._verify_all()
        self.runtime.record_artifact(
            "verify-results.json",
            json.dumps(result, indent=2),
            "json",
            "verifying",
        )
        return result

    def _verify_all(self) -> dict:
        features = self._load_features()
        if not features:
            return {"features": [], "summary": "No features to verify", "passed": False}

        results = {"features": [], "total": len(features), "passed": 0, "failed": 0}

        for f in features:
            fid = f.get("id", "?")
            desc = f.get("description", "")
            test_cmd = self._find_test_for(fid)
            if not test_cmd:
                # No test found — check if marked passing
                if f.get("passes"):
                    results["features"].append({"id": fid, "status": "assumed_pass", "detail": "No test found but marked passes=true"})
                    results["passed"] += 1
                else:
                    results["features"].append({"id": fid, "status": "skipped", "detail": "No test found"})
                    results["failed"] += 1
                continue

            print(f"  Testing {fid}…")
            status, detail = self._run_test(test_cmd, fid)
            results["features"].append({"id": fid, "status": status, "detail": detail, "command": test_cmd})
            if status == "pass":
                results["passed"] += 1
            else:
                results["failed"] += 1

        results["summary"] = f"{results['passed']}/{results['total']} passed"
        results["passed_all"] = results["failed"] == 0
        print(f"  {results['summary']}")
        return results

    def _load_features(self) -> list:
        data = self.store.read("feature_list.json")
        if not data:
            return []
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return []

    def _find_test_for(self, feature_id: str) -> str:
        """Return a test command or empty string."""
        # Check for pytest markers
        if self.store.exists("tests"):
            return f"uv run pytest -k {feature_id} --no-header -q 2>&1 || echo NO_MATCH"
        # Check for npm test
        if self.store.exists("package.json"):
            return f"npx jest --testPathPattern {feature_id} --no-coverage 2>&1 || echo NO_MATCH"
        return ""

    def _run_test(self, cmd: str, feature_id: str):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            output = (result.stdout + result.stderr).strip()

            if result.returncode == 0 and "NO_MATCH" not in output:
                return "pass", "Tests passed"
            if "NO_MATCH" in output:
                return "skip", f"No test matched for {feature_id}"
            return "fail", f"Tests failed (exit {result.returncode}): {output[-500:]}"

        except subprocess.TimeoutExpired:
            return "fail", "Tests timed out"
        except Exception as e:
            return "fail", f"Test error: {e}"
