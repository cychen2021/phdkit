from rich.text import Text
from rich.panel import Panel
from rich.live import Live
import subprocess
import time


class ScrollPanel:
    def __init__(self, title: str, line_num: int):
        self.title = title
        self.line_num = line_num
        self.__lines = []

    def __call__(self):
        return Panel(
            Text("\n".join(self.__lines)),
            height=self.line_num + 2,
            title=f"[bold]{self.title}[/bold]",
            border_style="dim",
        )

    def push(self, line: str):
        self.__lines.append(line)
        if len(self.__lines) > self.line_num:
            self.__lines.pop(0)


def subshell(title: str, line_num: int):
    panel = ScrollPanel(title, line_num)

    def __run(config_cmd, *, check: bool = False, **kwargs) -> int:
        with (
            Live(
                vertical_overflow="visible", get_renderable=panel, auto_refresh=False
            ) as live,
            subprocess.Popen(
                config_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                **kwargs,
            ) as p,
        ):
            time.sleep(0.5)
            assert p.stdout is not None
            for line in p.stdout:
                panel.push(line.strip())
                live.refresh()
            return_code = p.wait()
            if return_code != 0 and check:
                raise subprocess.CalledProcessError(
                    return_code,
                    config_cmd,
                    output=p.stdout.read(),
                )
            return return_code

    return __run
