import json
import os
from pathlib import Path
from app.agents.t3mp3st.findings import Finding, Severity, FindingKind
from app.providers import BaseLLMProvider, LLMMessage


REVIEW_PROMPT = """You are the Analyst operator (T3MP3ST). Review the following Python code for bugs.

Focus on:
1. **Logic bugs** — incorrect control flow, wrong comparisons, off-by-one
2. **State leaks** — shared mutable state between operations
3. **Race conditions** — unsynchronized access in concurrent contexts
4. **Security** — command injection, path traversal, unsafe deserialization
5. **Edge cases** — empty inputs, None values, boundary conditions
6. **Encoding issues** — cp1252 / Unicode handling on Windows

File: {filepath}
```python
{code}
```

Respond in this JSON format:
```json
[
  {{
    "kind": "logic_bug|state_leak|security|code_smell",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
    "line": <int>,
    "title": "short description",
    "detail": "detailed explanation",
    "fix": "suggested fix"
  }}
]
```

If no bugs, respond with empty array: []"""


class ReviewEngine:
    """LLM-based code review. T3MP3ST Analyst operator."""

    def __init__(self, provider: BaseLLMProvider, project_dir: str):
        self.provider = provider
        self.root = Path(project_dir).resolve()
        self.findings: list[Finding] = []

    def run(self, existing_findings: list[Finding]) -> list[Finding]:
        self.findings = []
        # Pick high-value files to review (most complex)
        files = self._pick_files()
        for rel, full in files:
            try:
                code = full.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            result = self._review_file(str(rel), code)
            if result:
                self.findings.extend(result)
        return self.findings

    def _pick_files(self) -> list[tuple[Path, Path]]:
        all_py = sorted(f for f in self.root.rglob("*.py") if ".venv" not in f.parts and "__pycache__" not in f.parts)
        scored = []
        for f in all_py:
            rel = f.relative_to(self.root)
            try:
                lines = len(f.read_text().splitlines())
            except OSError:
                continue
            # Score by complexity: more lines = more likely to have bugs
            scored.append((lines, rel, f))
        scored.sort(reverse=True)
        # Review top 5 most complex files
        return [(rel, full) for _, rel, full in scored[:5]]

    def _review_file(self, filepath: str, code: str) -> list[Finding]:
        if not code.strip():
            return []
        prompt = REVIEW_PROMPT.format(filepath=filepath, code=code)
        msgs = [LLMMessage(role="user", content=prompt)]
        try:
            resp = self.provider.chat(msgs, temperature=0.1)
            return self._parse(filepath, resp.content)
        except Exception as e:
            return [Finding(
                kind=FindingKind.CODE_SMELL,
                severity=Severity.INFO,
                file=filepath, line=0,
                title=f"LLM review failed: {e}",
                detail=str(e),
                operator="analyst")]

    def _parse(self, filepath: str, content: str) -> list[Finding]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            data = json.loads(content.strip())
            if not isinstance(data, list):
                return []
            results = []
            for item in data:
                try:
                    results.append(Finding(
                        kind=FindingKind(item["kind"]),
                        severity=Severity(item["severity"]),
                        file=filepath,
                        line=item.get("line", 0),
                        title=item.get("title", "Unknown"),
                        detail=item.get("detail", ""),
                        fix=item.get("fix", ""),
                        operator="analyst"))
                except (ValueError, KeyError):
                    continue
            return results
        except json.JSONDecodeError:
            return []
