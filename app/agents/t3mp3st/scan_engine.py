import ast
import os
from pathlib import Path
from typing import Optional
from app.agents.t3mp3st.findings import Finding, Severity, FindingKind


class ScanEngine:
    """AST-based static analysis. T3MP3ST Recon + Scanner operators."""

    def __init__(self, project_dir: str):
        self.root = Path(project_dir).resolve()
        self.findings: list[Finding] = []

    def run(self) -> list[Finding]:
        py_files = [f for f in self.root.rglob("*.py") if ".venv" not in f.parts]
        self.findings = []
        for f in py_files:
            rel = f.relative_to(self.root)
            try:
                raw = f.read_bytes()
                tree = ast.parse(raw)
                self._scan_file(rel, tree, f)
            except SyntaxError as e:
                self.findings.append(Finding(
                    kind=FindingKind.CODE_SMELL,
                    severity=Severity.HIGH,
                    file=str(rel), line=e.lineno or 0,
                    title="Syntax error in Python file",
                    detail=str(e),
                    operator="scanner"))
            except OSError as e:
                self.findings.append(Finding(
                    kind=FindingKind.MISSING_ERROR_HANDLING,
                    severity=Severity.LOW,
                    file=str(rel), line=0,
                    title=f"Cannot read file: {e}",
                    detail=str(e),
                    operator="scanner"))
        return self.findings

    def _scan_file(self, rel: Path, tree: ast.AST, full: Path):
        v = BugVisitor(str(rel))
        v.visit(tree)
        for f in v.findings:
            self.findings.append(f)
        self._check_encoding(rel, full)

    def _check_encoding(self, rel: Path, full: Path):
        try:
            raw = full.read_bytes()
        except OSError:
            return
        if any(b > 127 for b in raw):
            text = raw.decode("utf-8", errors="replace")
            if "\u2018" in text or "\u2019" in text or "\u201c" in text or "\u201d" in text:
                self.findings.append(Finding(
                    kind=FindingKind.ENCODING,
                    severity=Severity.LOW,
                    file=str(rel), line=0,
                    title="Non-ASCII curly quotes found",
                    detail="Smart/curly quotes may cause SyntaxError on non-UTF-8 systems. Use straight quotes.",
                    operator="scanner",
                    fix="Replace \u2018/\u2019 with ' and \u201c/\u201d with \""))


class BugVisitor(ast.NodeVisitor):
    def __init__(self, rel: str):
        self.rel = rel
        self.findings: list[Finding] = []
        self._imports: dict[str, int] = {}
        self._functions: dict[str, int] = {}

    def visit_Import(self, node):
        for alias in node.names:
            self._imports[alias.asname or alias.name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self._imports[alias.asname or f"{module}.{alias.name}"] = node.lineno
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self._functions[node.name] = node.lineno
        self._check_missing_error_handling(node)
        self._check_bare_except(node)
        self._check_optional_unwrap(node)
        self._check_type_annotations(node)
        self.generic_visit(node)

    def _check_missing_error_handling(self, node: ast.FunctionDef):
        """Functions that call I/O methods but lack try/except around them."""
        calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
        io_funcs = {"read_text", "write_text", "open", "read_bytes", "json.loads", "json.dumps",
                    "subprocess.run", "subprocess.Popen", "httpx.get", "httpx.post",
                    "raise_for_status", "request"}
        for call in calls:
            if isinstance(call.func, ast.Attribute) and call.func.attr in io_funcs:
                if not self._in_try(call, node):
                    self.findings.append(Finding(
                        kind=FindingKind.MISSING_ERROR_HANDLING,
                        severity=Severity.MEDIUM,
                        file=self.rel, line=call.lineno,
                        title=f"Unhandled exception from {call.func.attr}()",
                        detail=f"`{call.func.attr}()` can raise — wrap in try/except",
                        operator="scanner"))

    def _in_try(self, target: ast.AST, scope: ast.AST) -> bool:
        for n in ast.walk(scope):
            if isinstance(n, ast.Try):
                for body_node in ast.walk(n):
                    if body_node is target:
                        return True
        return False

    def _check_bare_except(self, node: ast.FunctionDef):
        for n in ast.walk(node):
            if isinstance(n, ast.ExceptHandler) and n.type is None:
                self.findings.append(Finding(
                    kind=FindingKind.CODE_SMELL,
                    severity=Severity.LOW,
                    file=self.rel, line=n.lineno,
                    title="Bare except clause",
                    detail="Captures BaseException (KeyboardInterrupt, SystemExit). Use `except Exception:`.",
                    operator="scanner"))

    def _check_optional_unwrap(self, node: ast.FunctionDef):
        for n in ast.walk(node):
            if isinstance(n, ast.Attribute) and n.attr in ("get",):
                if isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and n.value.func.attr in ("get", "load"):
                    self.findings.append(Finding(
                        kind=FindingKind.TYPE_SAFETY,
                        severity=Severity.INFO,
                        file=self.rel, line=n.lineno,
                        title="Optional.get() without None check",
                        detail="Chained Optional access may raise if intermediate is None",
                        operator="scanner"))

    def _check_type_annotations(self, node: ast.FunctionDef):
        # Check for Optional typing without None default
        for arg in node.args.args:
            if arg.annotation and "Optional" in ast.dump(arg.annotation):
                has_default = any(
                    a.arg == arg.arg
                    for a in node.args.kwonlyargs + node.args.args[len(node.args.args) - len(node.args.defaults):]
                )
                if not has_default:
                    self.findings.append(Finding(
                        kind=FindingKind.TYPE_SAFETY,
                        severity=Severity.INFO,
                        file=self.rel, line=arg.lineno or node.lineno,
                        title=f"Optional parameter '{arg.arg}' without None default",
                        detail="Optional[X] without =None default is misleading — caller cannot pass None",
                        operator="scanner"))
