import tomllib
import os
import smtplib
from email.mime.text import MIMEText
from ..configlib import configurable, setting


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


@configurable(
    read_config=__read_email_config,
    read_env=__read_email_env_config,
    config_key="mailog",
)
class __EmailNotifier:
    """The actual email notifier.

    As the `configurable` decorator discards type information, we forward this class to `EmailNotifier`.
    """

    def __init__(self):
        self.__receiver = None
        self.__smtp = None
        self.__sender = None
        self.__password = None

    def send(self, header: str, body: str):
        """Send an email with the given header and body."""

        if (
            self.__receiver is None
            or self.__smtp is None
            or self.__sender is None
            or self.__password is None
        ):
            raise ValueError("Email configuration is not set.")

        msg = MIMEText(body)
        msg["Subject"] = header
        msg["From"] = self.__sender
        msg["To"] = self.__receiver

        with smtplib.SMTP(self.__smtp) as server:
            server.starttls()
            server.login(self.__sender, self.__password)
            server.sendmail(self.__sender, [self.__receiver], msg.as_string())

    @property
    def receiver(self) -> str | None:
        return self.__receiver

    @receiver.setter
    @setting("receiver")
    def receiver(self, value: str | None):
        if value is not None:
            assert isinstance(value, str)
        self.__receiver = value

    @property
    def smtp(self) -> str | None:
        return self.__smtp

    @smtp.setter
    @setting("smtp")
    def smtp(self, value: str | None):
        if value is not None:
            assert isinstance(value, str)
        self.__smtp = value

    @property
    def sender(self) -> str | None:
        return self.__sender

    @sender.setter
    @setting("sender")
    def sender(self, value: str | None):
        if value is not None:
            assert isinstance(value, str)
        self.__sender = value

    @property
    def password(self) -> str | None:
        return self.__password

    @password.setter
    @setting("password")
    def password(self, value: str | None):
        if value is not None:
            assert isinstance(value, str)
        self.__password = value


class EmailNotifier(__EmailNotifier):
    def __init__(self):
        super().__init__()

    def send(self, header: str, body: str):
        super().send(header, body)

    @property
    def receiver(self) -> str | None:
        return super().receiver

    @receiver.setter
    def receiver(self, value: str | None):
        super().receiver = value

    @property
    def smtp(self) -> str | None:
        return super().smtp

    @smtp.setter
    def smtp(self, value: str | None):
        super().smtp = value

    @property
    def sender(self) -> str | None:
        return super().sender

    @sender.setter
    def sender(self, value: str | None):
        super().sender = value

    @property
    def password(self) -> str | None:
        return super().password

    @password.setter
    def password(self, value: str | None):
        super().password = value
