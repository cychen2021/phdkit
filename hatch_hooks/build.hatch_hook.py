from hatchling.builders.hooks.plugin.interface import BuildHookInterface # type: ignore
from pydust.build import build_uv # type: ignore

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        build_uv()