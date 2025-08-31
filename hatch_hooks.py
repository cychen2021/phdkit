from hatchling.metadata.plugin.interface import MetadataHookInterface # type: ignore

class CustomHook(MetadataHookInterface):
    def update(self, metadata):
        """
        在构建时被调用，用于更新元数据。
        """
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        content_without_badges = "\n".join(lines[:2] + lines[3:])

        metadata["readme"] = {
            "content-type": "text/markdown",
            "text": content_without_badges.strip(),
        }