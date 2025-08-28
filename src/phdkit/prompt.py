import re
from pathlib import Path
from typing import Any, Literal


class PromptTemplate:
    """A lightweight prompt template processor.

    Notes on behavior (implemented to match repository conventions):
    - ?<include:NAME>?  => substitute contents of `resources/NAME` (if present)
    - !<include:NAME>!  => substitute contents of `prompts/NAME` and recursively
                           expand it (prompts may contain further includes/vars)
    - ?<VAR.FIELD>?     => lookup `VAR.FIELD` in the kwargs (dot-separated)
    - After full expansion, the returned value is a list of (segment, is_cached)
      where segments originally enclosed by !<CACHE_BEGIN>! / !<CACHE_END>!
      are returned with is_cached=True and the markers removed.
    """

    def __init__(
        self,
        template: str = "",
        *,
        prompts_dir: Path | None = None,
        resources_dir: Path | None = None,
        max_depth: int = 20,
    ) -> None:
        """Initialize a PromptTemplate.

        Args:
            template: The template string to expand.
            prompts_dir: Optional prompts directory override.
            prompts_dir: Optional prompts directory override.
            resources_dir: Optional resources directory override.
            max_depth: Max recursion depth for includes.
        """

        self.template = template
        self._prompts_dir = prompts_dir
        self._resources_dir = resources_dir
        self._max_depth = max_depth

    def fill_out(self, **kwargs) -> str:
        """Fill out the prompt template with placeholders substituted.

        The `!<CACHE_MARKER>!` marker will be ignored and eliminated.

        Return:
            A filled prompt snippet with placeholders substituted.
        """

        return self._fill_out(_cache_marker_action="ignore", **kwargs)  # type: ignore

    def fill_out_cached(self, **kwargs) -> tuple[str, str]:
        """Fill out the prompt template with placeholders substituted.

        The prompt will be splitted at the `!<CACHE_MARKER>!` marker to
        a prefix to use cache and the rest not to.

        Return:
            A tuple containing the prefix and the non-cached part of the prompt.
        """

        return self._fill_out(_cache_marker_action="split", **kwargs)  # type: ignore

    def fill_out_cache_stripped(self, **kwargs) -> str:
        """Fill out the prompt template with placeholders substituted.

        The prefix before the `!<CACHE_MARKER>!` marker will be discarded.

        Return:
            The filled prompt with the cache marker stripped.
        """
        return self._fill_out(_cache_marker_action="strip", **kwargs)  # type: ignore

    def _fill_out(
        self,
        *,
        _cache_marker_action: Literal["ignore", "split", "strip"],
        **kwargs,
    ) -> tuple[str, str] | str:
        CACHE_MARKER = "!<CACHE_MARKER>!"
        # locate repository root (assumes this file lives at <repo>/src/mc/...)
        prompts_dir = self._prompts_dir
        resources_dir = self._resources_dir

        # regexes for the supported patterns
        re_prompt_include = re.compile(r"!<include:([^>]+)>!")
        re_resource_include = re.compile(r"\?<include:([^>]+)>\?")
        re_var = re.compile(r"\?<([^>]+)>\?")

        def lookup_var(expr: str) -> str:
            """Lookup a dotted variable from kwargs; return empty string if not found."""
            parts = expr.split(".")
            val: Any = kwargs
            for p in parts:
                if isinstance(val, dict):
                    if p in val:
                        val = val[p]
                    else:
                        return ""
                else:
                    # try attribute access for objects
                    try:
                        val = getattr(val, p)
                    except Exception:
                        return ""
            return "" if val is None else str(val)

        # recursion guard
        MAX_DEPTH = self._max_depth

        def expand(text: str, depth: int = 0) -> str:
            if depth > MAX_DEPTH:
                return text

            # resource includes first
            def _res_inc(m: re.Match) -> str:
                name = m.group(1).strip()
                path = resources_dir / name
                if not path.exists():
                    return ""
                try:
                    content = path.read_text(encoding="utf-8")
                except Exception:
                    return ""
                return expand(content, depth + 1)

            text = re_resource_include.sub(_res_inc, text)

            # prompt includes (recursively expand)
            def _prompt_inc(m: re.Match) -> str:
                name = m.group(1).strip()
                path = prompts_dir / name
                if not path.exists():
                    return ""
                try:
                    content = path.read_text(encoding="utf-8")
                except Exception:
                    return ""
                return expand(content, depth + 1)

            text = re_prompt_include.sub(_prompt_inc, text)

            # variables (including any leftover include:... forms handled defensively)
            def _var(m: re.Match) -> str:
                expr = m.group(1).strip()
                # defensive: treat include:... here too (resources)
                if expr.startswith("include:"):
                    name = expr.split(":", 1)[1].strip()
                    path = resources_dir / name
                    if not path.exists():
                        return ""
                    try:
                        return expand(path.read_text(encoding="utf-8"), depth + 1)
                    except Exception:
                        return ""
                return lookup_var(expr)

            text = re_var.sub(_var, text)
            return text

        template = getattr(self, "template", "") or ""
        expanded = expand(template)

        match _cache_marker_action:
            case "ignore":
                return expanded.replace(CACHE_MARKER, "")
            case "strip":
                marker_loc = expanded.find(CACHE_MARKER)
                expanded = (
                    expanded[marker_loc + len(CACHE_MARKER) :]
                    if marker_loc != -1
                    else expanded
                )
                return expanded


        pos = expanded.find(CACHE_MARKER)
        if pos == -1:
            # No marker: everything is non-cached (empty cached prefix)
            return ("", expanded)

        prefix = expanded[:pos]
        suffix = expanded[pos + len(CACHE_MARKER) :]
        return (prefix, suffix)
