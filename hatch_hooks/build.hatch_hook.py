from hatchling.builders.hooks.plugin.interface import BuildHookInterface # type: ignore
from pydust.build import build_uv # type: ignore
import re

PATTERN = r"""const ldlibrary = try getPythonOutput(\s*allocator,\s*python_exe,\s*"import sysconfig; print(sysconfig.get_config_var('LDLIBRARY'), end='')",);"""

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        build_uv()