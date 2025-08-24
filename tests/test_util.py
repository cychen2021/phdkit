import pytest

from phdkit import util


def test_unimplemented_raises_default():
    with pytest.raises(util.UnimplementedError) as exc:
        util.unimplemented()
    assert "not implemented" in str(exc.value).lower()


def test_unimplemented_with_message():
    msg = "please implement"
    with pytest.raises(util.UnimplementedError) as exc:
        util.unimplemented(msg)
    assert msg in str(exc.value)


def test_strip_indent_basic():
    text = """
    |Hello
      |World
    """
    out = util.strip_indent(text)
    assert out == "Hello\nWorld"


def test_strip_indent_keep_trailing_ws():
    text = """
    |Line1  
    |Line2\n
    """
    out = util.strip_indent(text, keep_trailing_ws=True)
    assert "Line1" in out


def test_protect_indent():
    text = "  |Keep\nNoPipe"
    out = util.protect_indent(text)
    assert "||Keep" in out
