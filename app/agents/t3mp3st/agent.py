import json
from pathlib import Path
from datetime import datetime
from app.providers import BaseLLMProvider, LLMMessage
from app.supervisor.runtime import SupervisedRuntime
from app.workspace.artifact_store import ArtifactStore
from app.agents.t3mp3st.findings import Finding, Severity, FindingKind
from app.agents.t3mp3st.scan_engine import ScanEngine
from app.agents.t3mp3st.dynamic_engine import DynamicEngine
from app.agents.t3mp3st.review_engine import ReviewEngine


class T3MP3STAgent:
    """Multi-engine bug-hunting agent. Mirrors T3MP3ST kill chain:

        RECON -> SCAN (static AST analysis)
              -> EXPLOIT (dynamic runtime testing)
              -> REVIEW (LLM code review)
              -> REPORT (structured findings with evidence)

    Provider is optional — works with static + dynamic alone.
    """

    def __init__(self, provider, runtime):
        self.provider = provider
        self.runtime = runtime
        self.store = ArtifactStore(".")
        self.findings: list[Finding] = []

    def run(self, project_dir: str):
        self.store = ArtifactStore(project_dir)
        print("\n=== T3MP3ST Bug Hunter ===")
        print("Multi-engine kill chain: RECON -> SCAN -> EXPLOIT -> REVIEW -> REPORT\n")

        scan = ScanEngine(project_dir)
        findings = []

        # Phase 1: RECON + SCAN (AST static analysis)
        print("[SCAN] Static AST analysis...")
        sf = scan.run()
        findings.extend(sf)
        print(f"  {len(sf)} static findings")

        # Phase 2: DYNAMIC (runtime testing)
        print("[EXPLOIT] Dynamic runtime testing...")
        de = DynamicEngine(project_dir)
        df = de.run()
        findings.extend(df)
        print(f"  {len(df)} dynamic findings")

        # Phase 3: REVIEW (LLM code review)
        if self.provider and self.provider.check_health():
            print("[REVIEW] LLM code review...")
            re = ReviewEngine(self.provider, project_dir)
            rf = re.run(findings)
            findings.extend(rf)
            print(f"  {len(rf)} review findings")
        else:
            print("[REVIEW] Skipped — provider not available")

        # Deduplicate
        self.findings = self._dedup(findings)

        # Phase 4: REPORT
        report = self._report(project_dir)
        print(f"\n=== Bug Hunt Complete ===")
        print(f"Total findings: {len(self.findings)}")
        sev_counts = {}
        for f in self.findings:
            sev_counts[f.severity.value] = sev_counts.get(f.severity.value, 0) + 1
        for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            if sev_counts.get(s):
                print(f"  {s}: {sev_counts[s]}")
        print(f"\nReport: {report}")

        if self.runtime:
            self.runtime.record_artifact(
                "t3mp3st-report.json",
                json.dumps({"findings": [f.to_dict() for f in self.findings]}, indent=2),
                "json",
                "t3mp3st",
            )
        return self.findings

    def _dedup(self, findings: list[Finding]) -> list[Finding]:
        seen = set()
        deduped = []
        for f in findings:
            key = (f.file, f.line, f.kind.value)
            if key not in seen:
                seen.add(key)
                deduped.append(f)
        return deduped

    def _report(self, project_dir: str) -> str:
        by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": [], "INFO": []}
        for f in self.findings:
            by_severity[f.severity.value].append(f)

        parts = [f"# T3MP3ST Bug Report", f"Generated: {datetime.now().isoformat()}", f"Project: {project_dir}", ""]
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            items = by_severity[sev]
            if not items:
                continue
            parts.append(f"## {sev} ({len(items)})")
            for f in items:
                parts.append(f"- [{f.operator}] `{f.file}:{f.line}` **{f.title}**")
                parts.append(f"  {f.detail}")
                if f.fix:
                    parts.append(f"  Fix: {f.fix}")
                parts.append("")
        content = "\n".join(parts)
        self.store.write("docs/T3MP3ST_REPORT.md", content)
        return f"docs/T3MP3ST_REPORT.md ({len(self.findings)} findings)"
