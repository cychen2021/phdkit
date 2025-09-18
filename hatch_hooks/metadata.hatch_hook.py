from hatchling.metadata.plugin.interface import MetadataHookInterface  # type: ignore
from pathlib import Path

PROJECT_SOURCE = Path(__file__).parent.parent.resolve()


class RedactReadmeHook(MetadataHookInterface):
    def update(self, metadata):
        with open(PROJECT_SOURCE / "README.md", "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        content_without_badges = "\n".join(lines[:1] + lines[3:])

        metadata["readme"] = {
            "content-type": "text/markdown",
            "text": content_without_badges.strip(),
        }
