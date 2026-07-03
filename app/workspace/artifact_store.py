from pathlib import Path
from typing import Optional


class ArtifactStore:
    def __init__(self, project_dir: str):
        self.root = Path(project_dir).resolve()

    def write(self, path: str, content: str) -> Optional[str]:
        try:
            full = self.root / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)
            return str(full)
        except OSError as e:
            return None

    def read(self, path: str) -> Optional[str]:
        try:
            full = self.root / path
            return full.read_text() if full.exists() else None
        except OSError:
            return None

    def exists(self, path: str) -> bool:
        return (self.root / path).exists()
