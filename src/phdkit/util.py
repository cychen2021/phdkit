__all__ = ["UnimplementedError", "unimplemented", "strip_indent", "protect_indent"]


class UnimplementedError(Exception):
    def __init__(self, message: str = "This feature is not implemented yet."):
        self.message = message

    def __str__(self):
        return f"Unimplemented Error: {self.message}"


def unimplemented(message: str | None = None) -> None:
    if message is None:
        raise UnimplementedError()
    else:
        raise UnimplementedError(message)


def strip_indent(text: str, *, keep_trailing_ws: bool = False) -> str:
    '''Strip leading whitespace from each line in the text.

    Example usage:

    ```python
    # Hereafter, the leading whitespaces and trailing whitespaces are represented by underscores.
    text = """
    ____|This is a line with leading whitespace.
    ____|This is another line with leading whitespace.
    ____|This line has a pipe at the start.
    ____||This line has two pipes at the start.
    """
    stripped_text = strip_indent(text, keep_trailing_ws=True)
    print(stripped_text)
    ```
    The output will be:
    ```text
    This is a line with leading whitespace.
    This is another line with leading whitespace.
    This line has a pipe at the start.
    ____|This line has two pipes at the start.
    ____
    ```

    Args:
        text (str): The input text to process.
        keep_trailing_ws (bool): If True, keep the trailing whitespace of the original text.
            Defaults to False.
    Returns:
        str: The processed text with leading whitespace stripped from each line.
    '''

    lines = text.strip().splitlines()
    if not lines:
        return ""

    new_lines = []
    for line in lines:
        stripped_line = line.lstrip()
        if stripped_line[0:1] == "||":
            new_line = line[: len(line) - len(stripped_line)] + "|" + stripped_line[2:]
        elif stripped_line[0] == "|":
            new_line = stripped_line[1:]
        else:
            new_line = line
        new_lines.append(new_line)
    if keep_trailing_ws:
        content = "\n".join(new_lines).lstrip()
        content += text[: len(content) - len(text.lstrip())]
    else:
        content = "\n".join(new_lines).strip()
    return content


def protect_indent(text: str) -> str:
    """Protect the indentation of lines starting with a pipe character by adding an additional pipe.

    See :func:`strip_indent`/
    """

    lines = text.splitlines()

    new_lines = []
    for line in lines:
        stripped_line = line.lstrip()
        if stripped_line.startswith("|"):
            new_line = line[: len(line) - len(stripped_line)] + "||" + stripped_line[1:]
        else:
            new_line = line
        new_lines.append(new_line)
    return "\n".join(new_lines)
