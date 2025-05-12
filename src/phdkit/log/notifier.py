import tomllib
import os
import smtplib
from email.mime.text import MIMEText
from ..configlib import Configurable, setting, Setting


def __read_email_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {}
        if "MAILOG_RECEIVER" in os.environ:
            config["mailog_receiver"] = os.environ["MAILOG_RECEIVER"]
        else:
            config["mailog_receiver"] = None

        if "MAILOG_SMTP" in os.environ:
            config["mailog_smtp"] = os.environ["MAILOG_SMTP"]
        else:
            config["mailog_smtp"] = None

        if "MAILOG_SENDER" in os.environ:
            config["mailog_sender"] = os.environ["MAILOG_SENDER"]
        else:
            config["mailog_sender"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        assert set(config.keys()).issubset(
            {"mailog_receiver", "mailog_smtp", "mailog_sender"}
        )
        if "mailog_receiver" not in config:
            config["mailog_receiver"] = None
        if "mailog_smtp" not in config:
            config["mailog_smtp"] = None
        if "mailog_sender" not in config:
            config["mailog_sender"] = None
    return config


def __read_email_env_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {}
        if "MAILOG_PASSWORD" in os.environ:
            config["mailog_password"] = os.environ["MAILOG_PASSWORD"]
        else:
            config["mailog_password"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        assert set(config.keys()).issubset({"mailog_password"})
        if "mailog_password" not in config:
            config["mailog_password"] = None
    return config


class EmailNotifier(Configurable):
    """The actual email notifier.

    As the `configurable` decorator discards type information, we forward this class to `EmailNotifier`.
    """

    reciever: Setting[None | str] = setting("mailog_receiver")
    smtp: Setting[None | str] = setting("mailog_smtp")
    sender: Setting[None | str] = setting("mailog_sender")
    password: Setting[None | str] = setting("mailog_password")

    def __init__(self):
        super().__init__(
            read_config=__read_email_config,
            read_env=__read_email_env_config,
            config_key="email_notifier",
        )

    def send(self, header: str, body: str):
        """Send an email with the given header and body."""

        if (
            self.reciever is None
            or self.smtp is None
            or self.sender is None
            or self.password is None
        ):
            raise ValueError("Email configuration is not set.")

        msg = MIMEText(body)
        msg["Subject"] = header
        msg["From"] = self.sender
        msg["To"] = self.reciever

        with smtplib.SMTP(self.smtp) as server:
            server.starttls()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, [self.reciever], msg.as_string())