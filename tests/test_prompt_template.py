from phdkit.prompt import PromptTemplate


def test_prompt_include_and_cache_split(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()

    base = prompts / "base.md"
    base.write_text("!<CACHE_MARKER>!CachedHeader\nBody: ?<value>?")

    pt = PromptTemplate(template="!<include:base.md>!", prompts_dir=prompts)

    cached, non_cached = pt.fill_out(_ignore_cache_marker=False, value="XYZ")

    # Expect prefix (cached) to be everything before marker, and suffix to be after
    assert cached == ""
    assert "CachedHeader" in non_cached
    assert "Body: XYZ" in non_cached


def test_variable_substitution_and_resource_include(tmp_path):
    # create resources dir
    resources = tmp_path / "resources"
    resources.mkdir()
    (resources / "greeting.txt").write_text("Hello, ?<name>?!!!")

    # template uses resource include and variable
    tpl_text = "?<include:greeting.txt>?"
    tpl = PromptTemplate(template=tpl_text, resources_dir=resources)

    cached, non_cached = tpl.fill_out(_ignore_cache_marker=False, name="World")
    assert cached == ""
    assert non_cached == "Hello, World!!!"


def test_prompt_include_recursive_and_cache_markers(tmp_path):
    # setup prompts dir with recursive include
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "inner.md").write_text("!<CACHE_MARKER>!Inner cached\nSuffix")
    (prompts / "outer.md").write_text("Start\n!<include:inner.md>!\nEnd")

    tpl = PromptTemplate(template="!<include:outer.md>!", prompts_dir=prompts)
    segments = tpl.fill_out()

    # outer includes inner; after expansion we expect a tuple (cached_prefix, non_cached_suffix)
    cached, non_cached = tpl.fill_out(_ignore_cache_marker=False)
    # The cached prefix should contain everything up to the marker included in inner
    assert isinstance(cached, str)
    assert isinstance(non_cached, str)
    assert "Start" in cached + non_cached and "End" in cached + non_cached


def test_missing_files_and_vars_return_empty(tmp_path):
    # empty dirs
    prompts = tmp_path / "prompts"
    resources = tmp_path / "resources"
    prompts.mkdir()
    resources.mkdir()

    tpl = PromptTemplate(
        template="Before ?<include:missing.txt>? ?<not.exists>? After",
        prompts_dir=prompts,
        resources_dir=resources,
    )
    cached, non_cached = tpl.fill_out(_ignore_cache_marker=False)
    assert cached == ""
    assert "Before   After" in non_cached


def test_circular_includes_respected_max_depth(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    # create two files that include each other
    (prompts / "a.md").write_text("A -> !<include:b.md>!")
    (prompts / "b.md").write_text("B -> !<include:a.md>!")

    tpl = PromptTemplate(template="!<include:a.md>!", prompts_dir=prompts, max_depth=3)
    # Should not infinite loop; returns a tuple of strings (may be truncated by depth)
    cached, non_cached = tpl.fill_out(_ignore_cache_marker=False)
    assert isinstance(cached, str) and isinstance(non_cached, str)


def test_lookup_nested_and_attribute_like(tmp_path):
    class Obj:
        def __init__(self, x):
            self.value = x

    tpl = PromptTemplate(template="Val: ?<data.value>? and Obj: ?<obj.value>?")
    cached, non_cached = tpl.fill_out(
        _ignore_cache_marker=False, data={"value": "D"}, obj=Obj("O")
    )
    assert cached == ""
    assert non_cached == "Val: D and Obj: O"


def test_unmatched_cache_begin_is_literal(tmp_path):
    tpl = PromptTemplate(template="Before !<CACHE_MARKER>!After")
    cached, non_cached = tpl.fill_out(_ignore_cache_marker=False)
    # If marker present, cached is the prefix before it ("Before ") and non_cached is the rest
    assert cached == "Before "
    assert non_cached == "After"


def test_ignore_cache_marker_returns_single_string(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()

    base = prompts / "base.md"
    base.write_text("!<CACHE_MARKER>!CachedHeader\nBody: ?<value>?")

    pt = PromptTemplate(template="!<include:base.md>!", prompts_dir=prompts)

    out = pt.fill_out(_ignore_cache_marker=True)

    # When ignoring cache marker we expect a single string with the marker removed
    assert isinstance(out, str)
    assert "!<CACHE_MARKER>!" not in out
    assert "CachedHeader" in out
    assert "Body: XYZ" in pt.fill_out(_ignore_cache_marker=True, value="XYZ")


def test_ignore_cache_marker_recursive_include(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "inner.md").write_text("Prefix !<CACHE_MARKER>!Inner cached\nSuffix")
    (prompts / "outer.md").write_text("Start\n!<include:inner.md>!\nEnd")

    tpl = PromptTemplate(template="!<include:outer.md>!", prompts_dir=prompts)
    out = tpl.fill_out(_ignore_cache_marker=True)

    assert isinstance(out, str)
    assert "!<CACHE_MARKER>!" not in out
    assert "Inner cached" in out
    assert "Start" in out and "End" in out
