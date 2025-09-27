from datetime import datetime
import tomllib
import os
import smtplib
from email.mime.text import MIMEText
from ..configlib import setting, configurable


def __read_email_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {"email": {}}
        if "EMAIL_RECEIVER" in os.environ:
            config["email"]["email_receiver"] = os.environ["EMAIL_RECEIVER"]
        else:
            config["email"]["email_receiver"] = None

        if "EMAIL_SMTP" in os.environ:
            config["email"]["email_smtp"] = os.environ["EMAIL_SMTP"]
        else:
            config["email"]["email_smtp"] = None

        if "EMAIL_SENDER" in os.environ:
            config["email"]["email_sender"] = os.environ["EMAIL_SENDER"]
        else:
            config["email"]["email_sender"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        # assert set(config.keys()).issubset(
        #     {"email_receiver", "email_smtp", "email_sender"}
        # ), f"Unexpected keys found: {set(config.keys()) - {'email_receiver', 'email_smtp', 'email_sender'}}"
        if "email" not in config:
            config["email"] = {}
        if "email_receiver" not in config["email"]:
            config["email"]["email_receiver"] = None
        if "email_smtp" not in config["email"]:
            config["email"]["email_smtp"] = None
        if "email_sender" not in config["email"]:
            config["email"]["email_sender"] = None
    return config


def __read_email_env_config(config_file: str | None) -> dict:
    if config_file is None:
        config = {"email": {}}
        if "EMAIL_PASSWORD" in os.environ:
            config["email"]["email_password"] = os.environ["EMAIL_PASSWORD"]
        else:
            config["email"]["email_password"] = None
    else:
        with open(config_file, "rb") as f:
            config = tomllib.load(f)
        # assert set(config.keys()).issubset({"email_password"}), f"Unexpected keys found: {set(config.keys()) - {'email_password'}}"
        if "email" not in config:
            config["email"] = {}
        if "email_password" not in config["email"]:
            config["email"]["email_password"] = None
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

    @setting("email_receiver")
    def receiver(self) -> str | None: ...

    @setting("email_smtp")
    def smtp(self) -> str | None: ...

    @setting("email_sender")
    def sender(self) -> str | None: ...

    @setting("email_password")
    def password(self) -> str | None: ...

    def send(self, header: str, body: str):
        """Send an email with the given header and body."""

        if (
            self.receiver is None
            or self.smtp is None
            or self.sender is None
            or self.password is None
        ):
            raise ValueError("Email configuration is not set.")

        msg = MIMEText(body)
        msg["Subject"] = header
        msg["From"] = self.sender
        msg["To"] = self.receiver

        with smtplib.SMTP(self.smtp) as server:
            server.starttls()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, [self.receiver], msg.as_string())
            if os.environ.get("PHDKIT_EMAIL_DEBUG", "0").lower() in [
                "1",
                "true",
                "yes",
                "on",
            ]:
                print(
                    f"Email sent: from {self.sender} to {self.receiver} through {self.smtp} at {datetime.now()}"
                )
