import tomllib
import os
import smtplib
from email.mime.text import MIMEText
from ..configlib import setting, configurable


def __read_email_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {}
        if "email_RECEIVER" in os.environ:
            config["email_receiver"] = os.environ["email_RECEIVER"]
        else:
            config["email_receiver"] = None

        if "email_SMTP" in os.environ:
            config["email_smtp"] = os.environ["email_SMTP"]
        else:
            config["email_smtp"] = None

        if "email_SENDER" in os.environ:
            config["email_sender"] = os.environ["email_SENDER"]
        else:
            config["email_sender"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        assert set(config.keys()).issubset(
            {"email_receiver", "email_smtp", "email_sender"}
        )
        if "email_receiver" not in config:
            config["email_receiver"] = None
        if "email_smtp" not in config:
            config["email_smtp"] = None
        if "email_sender" not in config:
            config["email_sender"] = None
    return config


def __read_email_env_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {}
        if "email_PASSWORD" in os.environ:
            config["email_password"] = os.environ["email_PASSWORD"]
        else:
            config["email_password"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        assert set(config.keys()).issubset({"email_password"})
        if "email_password" not in config:
            config["email_password"] = None
    return config


@configurable(
    config_key="email",
    load_config=__read_email_config,
    load_env=__read_email_env_config,
)
class EmailNotifier:
    """An email notifier.

    Settings:
        reciever (str | None): The email address to send notifications to.
        smtp (str | None): The SMTP server to use for sending emails.
        sender (str | None): The email address to send notifications from.
        password (str | None): The password for the sender's email account.
    Methods:
        send(header: str, body: str): Sends an email with the given header and body.
    """

    @setting("email_reciever")
    def reciever(self) -> str | None: ...

    @setting("email_smtp")
    def smtp(self) -> str | None: ...

    @setting("email_sender")
    def sender(self) -> str | None: ...

    @setting("email_password")
    def password(self) -> str | None: ...

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
