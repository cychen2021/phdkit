from ..configlib import configurable, setting

def __read_email_config(config_file: str | None) -> dict:...
def __read_email_env_config(config_file: str | None) -> dict:...

@configurable(
    read_config=__read_email_config,
    read_env=__read_email_env_config,
)
class EmailNotifier: ...